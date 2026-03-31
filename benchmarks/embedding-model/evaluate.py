#!/usr/bin/env python3
"""
Phase 3: Embedding Model Comparison — Evaluation Runner

Measures retrieval quality (Recall@k, MRR), latency, and produces a
weighted scorecard for each embedding model.

Usage:
    python evaluate.py                          # open-source models only (no API key)
    python evaluate.py --models all             # include OpenAI if OPENAI_API_KEY set
    python evaluate.py --models bge_m3 mxbai   # specific models
    python evaluate.py --top-k 5               # override retrieval top-k
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.WARNING)

BENCH_DIR = Path(__file__).parent
sys.path.insert(0, str(BENCH_DIR))

import config

DATASETS_DIR = config.DATASETS_DIR
RESULTS_DIR = config.RESULTS_DIR
RESULTS_DIR.mkdir(exist_ok=True)

ALL_DOC_FILES = [
    str(DATASETS_DIR / "hr_policy_th.md"),
    str(DATASETS_DIR / "tech_docs_en.md"),
    str(DATASETS_DIR / "faq_mixed.md"),
]

# ── Scoring weights (from plan.md Phase 3) ────────────────────────────────────
# Thai Retrieval Quality 25%, English Quality 15%, Latency 15%, Cost 15%,
# Self-hosting 10%, Dim/Storage 5%, Max Tokens 5%, Vendor Lock-in 10%
WEIGHTS = {
    "thai_recall":    0.25,
    "eng_recall":     0.15,
    "latency":        0.15,
    "cost":           0.15,
    "self_host":      0.10,
    "dimension":      0.05,
    "max_tokens":     0.05,
    "lock_in":        0.10,
}

# ── Model registry ────────────────────────────────────────────────────────────
MODEL_REGISTRY: dict[str, str] = {
    "bge_m3":           "models.bge_m3.BGEM3Model",
    "multilingual_e5":  "models.multilingual_e5.MultilingualE5LargeModel",
    "mxbai":            "models.mxbai.MxbaiEmbedLargeModel",
    "openai_large":     "models.openai_large.OpenAILargeModel",
    "openai_small":     "models.openai_small.OpenAISmallModel",
}

OPEN_SOURCE_MODELS = {"bge_m3", "multilingual_e5", "mxbai"}


# ── Document chunking ─────────────────────────────────────────────────────────

def _chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    step = config.CHUNK_SIZE - config.CHUNK_OVERLAP
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + config.CHUNK_SIZE]))
        i += step
    return chunks


def _load_corpus() -> tuple[list[str], list[str]]:
    """Returns (chunks, source_labels)."""
    chunks: list[str] = []
    sources: list[str] = []
    for doc_path in ALL_DOC_FILES:
        text = Path(doc_path).read_text(encoding="utf-8")
        doc_chunks = _chunk_text(text)
        chunks.extend(doc_chunks)
        sources.extend([Path(doc_path).name] * len(doc_chunks))
    return chunks, sources


def _load_questions() -> list[dict]:
    return json.loads((DATASETS_DIR / "questions.json").read_text(encoding="utf-8"))


# ── Ground truth: find relevant chunk per question ────────────────────────────

def _token_overlap(a: str, b: str) -> float:
    """Jaccard token overlap between two strings (model-agnostic proxy for relevance)."""
    a_tokens = set(a.lower().split())
    b_tokens = set(b.lower().split())
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def _find_ground_truth_chunk(expected_answer: str, chunks: list[str]) -> int:
    """Return index of chunk most likely to contain the answer (by token overlap)."""
    scores = [_token_overlap(expected_answer, chunk) for chunk in chunks]
    return int(max(range(len(scores)), key=lambda i: scores[i]))


# ── Cosine retrieval ──────────────────────────────────────────────────────────

import numpy as np


def _cosine_retrieve(
    query_emb: np.ndarray,        # shape (dims,)
    corpus_embs: np.ndarray,      # shape (n, dims), normalized
    top_k: int,
) -> list[int]:
    scores = corpus_embs @ query_emb
    return list(np.argsort(scores)[::-1][:top_k])


# ── Per-model evaluation ──────────────────────────────────────────────────────

def _load_model_class(dotted: str):
    module_path, cls_name = dotted.rsplit(".", 1)
    import importlib
    return getattr(importlib.import_module(module_path), cls_name)


def _evaluate_model(
    name: str,
    chunks: list[str],
    questions: list[dict],
    top_k: int,
) -> dict[str, Any] | None:
    from rich.console import Console
    console = Console()
    console.rule(f"[bold cyan]{name}[/bold cyan]")

    try:
        cls = _load_model_class(MODEL_REGISTRY[name])
        model = cls()
    except EnvironmentError as e:
        console.print(f"  [yellow]SKIP: {e}[/yellow]")
        return None
    except Exception as e:
        console.print(f"  [red]LOAD ERROR: {e}[/red]")
        return None

    meta = model.meta
    console.print(f"  Model: {meta.name}  dims={meta.dimensions}  max_tokens={meta.max_tokens}")

    # ── Index corpus ──────────────────────────────────────────────────────────
    console.print(f"  [dim]Indexing {len(chunks)} chunks...[/dim]")

    # E5 uses query/passage prefixes via special method
    is_e5 = hasattr(model, "encode_passages")
    if is_e5:
        idx_result = model.encode_passages(chunks)
    else:
        idx_result = model.encode(chunks)

    corpus_embs = idx_result.embeddings
    index_time_ms = idx_result.latency_ms
    console.print(f"  ✓ Indexed in {index_time_ms:.0f} ms")

    # ── Find ground truth chunks ──────────────────────────────────────────────
    gt_indices = {
        q["id"]: _find_ground_truth_chunk(q["expected_answer"], chunks)
        for q in questions
    }

    # ── Query evaluation ──────────────────────────────────────────────────────
    query_results: list[dict] = []
    query_latencies: list[float] = []

    for q in questions:
        query_text = q["question"]

        if is_e5:
            q_result = model.encode_queries([query_text])
        else:
            q_result = model.encode([query_text])

        q_emb = q_result.embeddings[0]
        query_latencies.append(q_result.latency_ms)

        retrieved_idx = _cosine_retrieve(q_emb, corpus_embs, top_k)
        gt_idx = gt_indices[q["id"]]
        hit = gt_idx in retrieved_idx

        # MRR: reciprocal rank of the ground truth chunk
        rr = 0.0
        if gt_idx in retrieved_idx:
            rank = retrieved_idx.index(gt_idx) + 1  # 1-indexed
            rr = 1.0 / rank

        query_results.append(
            {
                "id": q["id"],
                "question": q["question"],
                "category": q.get("category", ""),
                "gt_chunk_idx": gt_idx,
                "hit_at_k": hit,
                "reciprocal_rank": rr,
                "retrieved_top1_chunk": chunks[retrieved_idx[0]][:120] if retrieved_idx else "",
                "query_latency_ms": q_result.latency_ms,
            }
        )

    # ── Aggregate metrics ─────────────────────────────────────────────────────
    thai_qs = [r for r in query_results if "thai" in r["category"]]
    eng_qs  = [r for r in query_results if "english" in r["category"] or "eng" in r["category"]]

    def _recall(qs: list[dict]) -> float:
        if not qs:
            return 0.0
        return sum(r["hit_at_k"] for r in qs) / len(qs)

    def _mrr(qs: list[dict]) -> float:
        if not qs:
            return 0.0
        return sum(r["reciprocal_rank"] for r in qs) / len(qs)

    thai_recall = _recall(thai_qs)
    eng_recall  = _recall(eng_qs)
    overall_recall = _recall(query_results)
    mrr = _mrr(query_results)
    avg_query_latency_ms = sum(query_latencies) / len(query_latencies) if query_latencies else 0.0

    console.print(
        f"  Thai Recall@{top_k}: {thai_recall:.0%}  "
        f"Eng Recall@{top_k}: {eng_recall:.0%}  "
        f"Overall Recall@{top_k}: {overall_recall:.0%}  "
        f"MRR: {mrr:.3f}"
    )
    console.print(
        f"  Index: {index_time_ms:.0f} ms  Avg Query: {avg_query_latency_ms:.0f} ms"
    )

    return {
        "model": name,
        "meta": {
            "name": meta.name,
            "dimensions": meta.dimensions,
            "max_tokens": meta.max_tokens,
            "cost_per_1m_tokens": meta.cost_per_1m_tokens,
            "vendor_lock_in": meta.vendor_lock_in,
            "self_hostable": meta.self_hostable,
        },
        "index_time_ms": index_time_ms,
        "avg_query_latency_ms": avg_query_latency_ms,
        "thai_recall": thai_recall,
        "eng_recall": eng_recall,
        "overall_recall": overall_recall,
        "mrr": mrr,
        "queries": query_results,
    }


# ── Weighted scorecard ────────────────────────────────────────────────────────

def _compute_scores(results: list[dict]) -> list[dict]:
    """
    Normalise each dimension (higher = better) then apply weights.

    Latency & cost & dimension & lock-in are inverted (lower = better).
    """
    if not results:
        return []

    def _col(key: str) -> list[float]:
        return [r[key] for r in results]

    def _norm_higher(vals: list[float]) -> list[float]:
        mn, mx = min(vals), max(vals)
        if mx == mn:
            return [1.0] * len(vals)
        return [(v - mn) / (mx - mn) for v in vals]

    def _norm_lower(vals: list[float]) -> list[float]:
        mn, mx = min(vals), max(vals)
        if mx == mn:
            return [1.0] * len(vals)
        return [(mx - v) / (mx - mn) for v in vals]

    thai_scores   = _norm_higher(_col("thai_recall"))
    eng_scores    = _norm_higher(_col("eng_recall"))
    latency_scores = _norm_lower(_col("avg_query_latency_ms"))
    cost_scores   = _norm_lower([r["meta"]["cost_per_1m_tokens"] for r in results])
    self_host_scores = [1.0 if r["meta"]["self_hostable"] else 0.0 for r in results]
    dim_scores    = _norm_lower([float(r["meta"]["dimensions"]) for r in results])
    token_scores  = _norm_higher([float(r["meta"]["max_tokens"]) for r in results])
    lock_scores   = _norm_lower([float(r["meta"]["vendor_lock_in"]) for r in results])

    scored = []
    for i, r in enumerate(results):
        weighted = (
            WEIGHTS["thai_recall"]  * thai_scores[i]
            + WEIGHTS["eng_recall"] * eng_scores[i]
            + WEIGHTS["latency"]    * latency_scores[i]
            + WEIGHTS["cost"]       * cost_scores[i]
            + WEIGHTS["self_host"]  * self_host_scores[i]
            + WEIGHTS["dimension"]  * dim_scores[i]
            + WEIGHTS["max_tokens"] * token_scores[i]
            + WEIGHTS["lock_in"]    * lock_scores[i]
        )
        scored.append({**r, "weighted_score": round(weighted, 4)})

    return sorted(scored, key=lambda x: x["weighted_score"], reverse=True)


# ── Rich output ───────────────────────────────────────────────────────────────

def _rich_tables(scored: list[dict], top_k: int) -> None:
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # ── Retrieval quality table ───────────────────────────────────────────────
    q_table = Table(
        title=f"[bold]Phase 3 — Retrieval Quality (Recall@{top_k} / MRR)[/bold]",
        show_lines=True,
    )
    q_table.add_column("Model", style="cyan", no_wrap=True)
    q_table.add_column(f"Thai\nRecall@{top_k}", justify="right")
    q_table.add_column(f"Eng\nRecall@{top_k}", justify="right")
    q_table.add_column(f"Overall\nRecall@{top_k}", justify="right")
    q_table.add_column("MRR", justify="right")

    for r in scored:
        q_table.add_row(
            r["meta"]["name"],
            f"{r['thai_recall']:.0%}",
            f"{r['eng_recall']:.0%}",
            f"{r['overall_recall']:.0%}",
            f"{r['mrr']:.3f}",
        )
    console.print(q_table)

    # ── Latency & cost table ─────────────────────────────────────────────────
    lc_table = Table(
        title="[bold]Phase 3 — Latency & Cost[/bold]",
        show_lines=True,
    )
    lc_table.add_column("Model", style="cyan", no_wrap=True)
    lc_table.add_column("Index Time (ms)", justify="right")
    lc_table.add_column("Avg Query (ms)", justify="right")
    lc_table.add_column("Cost/1M tokens", justify="right")
    lc_table.add_column("Self-hosted", justify="center")

    for r in scored:
        meta = r["meta"]
        cost_str = f"${meta['cost_per_1m_tokens']:.2f}" if meta["cost_per_1m_tokens"] > 0 else "FREE"
        lc_table.add_row(
            meta["name"],
            f"{r['index_time_ms']:.0f}",
            f"{r['avg_query_latency_ms']:.0f}",
            cost_str,
            "✅" if meta["self_hostable"] else "❌",
        )
    console.print(lc_table)

    # ── Model metadata table ─────────────────────────────────────────────────
    meta_table = Table(
        title="[bold]Phase 3 — Model Metadata[/bold]",
        show_lines=True,
    )
    meta_table.add_column("Model", style="cyan", no_wrap=True)
    meta_table.add_column("Dims", justify="right")
    meta_table.add_column("Max Tokens", justify="right")
    meta_table.add_column("Lock-in\n(0=open,10=locked)", justify="right")

    for r in scored:
        meta = r["meta"]
        meta_table.add_row(
            meta["name"],
            str(meta["dimensions"]),
            str(meta["max_tokens"]),
            str(meta["vendor_lock_in"]),
        )
    console.print(meta_table)

    # ── Weighted scorecard ────────────────────────────────────────────────────
    score_table = Table(
        title="[bold]Phase 3 — Weighted Scorecard[/bold]  "
              "(Thai 25% · Eng 15% · Latency 15% · Cost 15% · Self-host 10% · "
              "Dims 5% · MaxTok 5% · Lock-in 10%)",
        show_lines=True,
    )
    score_table.add_column("Rank", justify="right")
    score_table.add_column("Model", style="cyan", no_wrap=True)
    score_table.add_column("Weighted Score", justify="right")
    score_table.add_column("Verdict")

    for rank, r in enumerate(scored, start=1):
        verdict = "⭐ RECOMMENDED" if rank == 1 else ("✅ Runner-up" if rank == 2 else "")
        score_table.add_row(
            str(rank),
            r["meta"]["name"],
            f"{r['weighted_score']:.4f}",
            verdict,
        )
    console.print(score_table)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3: Embedding Model Benchmark")
    parser.add_argument(
        "--models",
        nargs="+",
        default=list(OPEN_SOURCE_MODELS),
        choices=list(MODEL_REGISTRY.keys()) + ["all"],
        help=(
            "Which models to evaluate (default: open-source only). "
            "Use 'all' to include OpenAI models if OPENAI_API_KEY is set."
        ),
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=config.TOP_K,
        help=f"Top-k for retrieval (default: {config.TOP_K})",
    )
    parser.add_argument(
        "--output",
        default=str(RESULTS_DIR / "embedding_model_results.json"),
        help="Output JSON path",
    )
    args = parser.parse_args()

    models = (
        list(MODEL_REGISTRY.keys())
        if "all" in args.models
        else args.models
    )

    # ── Verify datasets exist ─────────────────────────────────────────────────
    missing = [f for f in ALL_DOC_FILES if not Path(f).exists()]
    if missing:
        print(f"⚠️  Missing dataset files: {missing}")
        sys.exit(1)

    chunks, sources = _load_corpus()
    questions = _load_questions()

    print(f"\nCorpus: {len(chunks)} chunks from {len(ALL_DOC_FILES)} documents")
    print(f"Questions: {len(questions)}")
    print(f"Models: {models}")
    print(f"Top-k: {args.top_k}\n")

    all_results: list[dict] = []
    for name in models:
        res = _evaluate_model(name, chunks, questions, args.top_k)
        if res is not None:
            all_results.append(res)

    if not all_results:
        print("No models evaluated successfully.")
        sys.exit(1)

    scored = _compute_scores(all_results)
    _rich_tables(scored, args.top_k)

    out = {
        "phase": 3,
        "top_k": args.top_k,
        "chunk_size": config.CHUNK_SIZE,
        "chunk_overlap": config.CHUNK_OVERLAP,
        "num_chunks": len(chunks),
        "num_questions": len(questions),
        "weights": WEIGHTS,
        "results": scored,
    }
    out_path = Path(args.output)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Results saved → {out_path}")


if __name__ == "__main__":
    main()
