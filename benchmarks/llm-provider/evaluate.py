#!/usr/bin/env python3
"""
Phase 3.5: LLM Provider Comparison — Evaluation Runner

Measures RAG answer quality, latency, cost, and produces a weighted
scorecard for each LLM provider / model combination.

Retrieval uses a simple TF-IDF cosine similarity (no embedding model
dependency) so the benchmark can run without GPU or heavy dependencies.
For a fair production comparison, pass --use-bge to use BGE-M3 (Phase 3 winner).

Usage:
    python evaluate.py                              # OpenRouter only (gpt-4o-mini)
    python evaluate.py --providers all              # All configured providers
    python evaluate.py --providers openrouter ollama
    python evaluate.py --provider openrouter --models openai/gpt-4o-mini openai/gpt-4o
    python evaluate.py --top-k 5
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import re
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.WARNING)

BENCH_DIR = Path(__file__).parent
sys.path.insert(0, str(BENCH_DIR))

import config

DATASETS_DIR = config.DATASETS_DIR
RESULTS_DIR  = config.RESULTS_DIR
RESULTS_DIR.mkdir(exist_ok=True)

ALL_DOC_FILES = [
    str(DATASETS_DIR / "hr_policy_th.md"),
    str(DATASETS_DIR / "tech_docs_en.md"),
    str(DATASETS_DIR / "faq_mixed.md"),
]

# ── Scoring weights (from plan.md Phase 3.5) ──────────────────────────────────
# Response Quality 20%, Anti-Lock-in 20%, Cost 15%, Latency 15%,
# Thai Quality 10%, Fallback/Reliability 10%, Privacy 5%, Ease-of-switching 5%
WEIGHTS = {
    "overall_quality": 0.20,
    "lock_in":         0.20,
    "cost":            0.15,
    "latency":         0.15,
    "thai_quality":    0.10,
    "reliability":     0.10,  # static: openrouter=high, ollama=high, direct=medium
    "privacy":         0.05,  # static: ollama=best, direct=worst
    "ease_switching":  0.05,  # static: openrouter=best, direct=worst
}

# ── Provider registry ──────────────────────────────────────────────────────────
# Each entry: (class dotted path, model_id or None for default)
PROVIDER_REGISTRY: dict[str, tuple[str, str | None]] = {
    "openrouter_gpt4o_mini":   ("providers.openrouter.OpenRouterProvider",    "openai/gpt-4o-mini"),
    "openrouter_gpt4o":        ("providers.openrouter.OpenRouterProvider",    "openai/gpt-4o"),
    "openrouter_claude_sonnet":("providers.openrouter.OpenRouterProvider",    "anthropic/claude-3.5-sonnet-20241022"),
    "openrouter_llama3":       ("providers.openrouter.OpenRouterProvider",    "meta-llama/llama-3.1-70b-instruct"),
    "openrouter_gemini_flash": ("providers.openrouter.OpenRouterProvider",    "google/gemini-2.0-flash-001"),
    "openrouter_deepseek":     ("providers.openrouter.OpenRouterProvider",    "deepseek/deepseek-chat"),
    "openai_gpt4o_mini":       ("providers.openai_direct.OpenAIDirectProvider", "gpt-4o-mini"),
    "openai_gpt4o":            ("providers.openai_direct.OpenAIDirectProvider", "gpt-4o"),
    "anthropic_sonnet":        ("providers.anthropic_direct.AnthropicDirectProvider", "claude-3-5-sonnet-20241022"),
    "anthropic_haiku":         ("providers.anthropic_direct.AnthropicDirectProvider", "claude-3-haiku-20240307"),
    "ollama":                  ("providers.ollama.OllamaProvider",            None),
}

# Default set when no --providers flag is given
DEFAULT_PROVIDERS = {"openrouter_gpt4o_mini"}

# Static reliability score (0–1) per provider type — qualitative assessment
_RELIABILITY: dict[str, float] = {
    "openrouter": 0.85,  # multi-provider fallback, but adds one hop
    "openai":     0.90,  # direct, very reliable SLA
    "anthropic":  0.90,
    "ollama":     0.70,  # depends on local hardware
}

# Static privacy score (0–1) per provider type
_PRIVACY: dict[str, float] = {
    "ollama":     1.0,   # fully local
    "openrouter": 0.5,   # data transits a third-party gateway
    "openai":     0.4,
    "anthropic":  0.4,
}

# Ease of model switching (0–1)
_EASE_SWITCHING: dict[str, float] = {
    "openrouter": 1.0,   # one model string change
    "ollama":     0.8,   # pull model + restart
    "openai":     0.4,
    "anthropic":  0.3,
}


# ── Document chunking (identical to Phase 3) ──────────────────────────────────

def _chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    step = config.CHUNK_SIZE - config.CHUNK_OVERLAP
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i: i + config.CHUNK_SIZE]))
        i += step
    return chunks


def _load_corpus() -> list[str]:
    chunks: list[str] = []
    for doc_path in ALL_DOC_FILES:
        text = Path(doc_path).read_text(encoding="utf-8")
        chunks.extend(_chunk_text(text))
    return chunks


def _load_questions() -> list[dict]:
    return json.loads((DATASETS_DIR / "questions.json").read_text(encoding="utf-8"))


# ── TF-IDF retrieval (no external dependency) ─────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w\u0E00-\u0E7F]+", text.lower())


def _build_tfidf(chunks: list[str]) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Returns (tf_per_chunk, idf_dict)."""
    N = len(chunks)
    df: dict[str, int] = {}
    tfs: list[dict[str, float]] = []

    for chunk in chunks:
        tokens = _tokenize(chunk)
        freq: dict[str, int] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        total = len(tokens) or 1
        tf = {t: c / total for t, c in freq.items()}
        tfs.append(tf)
        for t in tf:
            df[t] = df.get(t, 0) + 1

    idf = {t: math.log((N + 1) / (c + 1)) + 1 for t, c in df.items()}
    return tfs, idf


def _tfidf_score(query_tokens: list[str], tf: dict[str, float], idf: dict[str, float]) -> float:
    score = 0.0
    for t in query_tokens:
        if t in tf:
            score += tf[t] * idf.get(t, 1.0)
    return score


def _retrieve(query: str, tfs: list[dict], idf: dict, top_k: int) -> list[int]:
    q_tokens = _tokenize(query)
    scores = [_tfidf_score(q_tokens, tf, idf) for tf in tfs]
    return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]


# ── Answer quality: token-overlap F1 (language-agnostic) ─────────────────────

def _f1_score(prediction: str, reference: str) -> float:
    pred_tokens = set(_tokenize(prediction))
    ref_tokens  = set(_tokenize(reference))
    if not pred_tokens or not ref_tokens:
        return 0.0
    common = pred_tokens & ref_tokens
    precision = len(common) / len(pred_tokens)
    recall    = len(common) / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ── Load provider class ───────────────────────────────────────────────────────

def _load_provider(dotted: str, model_id: str | None):
    module_path, cls_name = dotted.rsplit(".", 1)
    import importlib
    cls = getattr(importlib.import_module(module_path), cls_name)
    return cls(model_id) if model_id is not None else cls()


# ── Per-provider evaluation ───────────────────────────────────────────────────

def _evaluate_provider(
    name: str,
    chunks: list[str],
    tfs: list[dict],
    idf: dict,
    questions: list[dict],
    top_k: int,
) -> dict[str, Any] | None:
    from rich.console import Console
    console = Console()

    dotted, model_id = PROVIDER_REGISTRY[name]
    console.rule(f"[bold cyan]{name}[/bold cyan]")

    try:
        provider = _load_provider(dotted, model_id)
    except EnvironmentError as e:
        console.print(f"  [yellow]SKIP: {e}[/yellow]")
        return None
    except Exception as e:
        console.print(f"  [red]LOAD ERROR: {e}[/red]")
        return None

    meta = provider.meta
    console.print(
        f"  Provider: {meta.name}  "
        f"lock_in={meta.vendor_lock_in}  "
        f"self_host={meta.self_hostable}"
    )

    query_results: list[dict] = []
    total_cost_usd = 0.0
    latencies: list[float] = []

    for q in questions:
        question_text = q["question"]
        expected      = q["expected_answer"]
        category      = q.get("category", "")

        # Retrieve context
        top_idx = _retrieve(question_text, tfs, idf, top_k)
        context = "\n\n---\n\n".join(chunks[i] for i in top_idx)

        # Generate answer
        try:
            result = provider.generate(question_text, context)
        except Exception as e:
            console.print(f"  [red]Generate error for Q{q['id']}: {e}[/red]")
            continue

        f1 = _f1_score(result.text, expected)
        latencies.append(result.latency_ms)
        total_cost_usd += result.cost_usd

        query_results.append({
            "id":           q["id"],
            "question":     question_text,
            "category":     category,
            "expected":     expected,
            "generated":    result.text,
            "f1_score":     round(f1, 4),
            "latency_ms":   round(result.latency_ms, 1),
            "input_tokens": result.input_tokens,
            "output_tokens":result.output_tokens,
            "cost_usd":     round(result.cost_usd, 6),
        })

    if not query_results:
        return None

    thai_qs = [r for r in query_results if "thai" in r["category"]]
    eng_qs  = [r for r in query_results if "english" in r["category"] or "eng" in r["category"]]

    def _avg_f1(qs: list[dict]) -> float:
        return sum(r["f1_score"] for r in qs) / len(qs) if qs else 0.0

    overall_f1   = _avg_f1(query_results)
    thai_f1      = _avg_f1(thai_qs)
    avg_latency  = sum(latencies) / len(latencies)

    console.print(
        f"  Overall F1: {overall_f1:.3f}  "
        f"Thai F1: {thai_f1:.3f}  "
        f"Avg Latency: {avg_latency:.0f} ms  "
        f"Total Cost: ${total_cost_usd:.4f}"
    )

    return {
        "provider": name,
        "meta": {
            "name":                meta.name,
            "model_id":            meta.model_id,
            "provider":            meta.provider,
            "cost_per_1m_input":   meta.cost_per_1m_input,
            "cost_per_1m_output":  meta.cost_per_1m_output,
            "vendor_lock_in":      meta.vendor_lock_in,
            "self_hostable":       meta.self_hostable,
            "openai_compatible":   meta.openai_compatible,
        },
        "overall_f1":       round(overall_f1, 4),
        "thai_f1":          round(thai_f1, 4),
        "avg_latency_ms":   round(avg_latency, 1),
        "total_cost_usd":   round(total_cost_usd, 6),
        "num_questions":    len(query_results),
        "queries":          query_results,
    }


# ── Weighted scorecard ────────────────────────────────────────────────────────

def _compute_scores(results: list[dict]) -> list[dict]:
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

    quality_scores   = _norm_higher(_col("overall_f1"))
    thai_scores      = _norm_higher(_col("thai_f1"))
    latency_scores   = _norm_lower(_col("avg_latency_ms"))
    # Cost: blend input+output pricing (estimate 3:1 input:output ratio)
    blended_costs = [
        r["meta"]["cost_per_1m_input"] * 0.75 + r["meta"]["cost_per_1m_output"] * 0.25
        for r in results
    ]
    cost_scores      = _norm_lower(blended_costs)
    lock_scores      = _norm_lower([float(r["meta"]["vendor_lock_in"]) for r in results])
    reliability_vals = [_RELIABILITY.get(r["meta"]["provider"], 0.7) for r in results]
    privacy_vals     = [_PRIVACY.get(r["meta"]["provider"], 0.5) for r in results]
    switching_vals   = [_EASE_SWITCHING.get(r["meta"]["provider"], 0.5) for r in results]

    scored = []
    for i, r in enumerate(results):
        weighted = (
            WEIGHTS["overall_quality"] * quality_scores[i]
            + WEIGHTS["lock_in"]       * lock_scores[i]
            + WEIGHTS["cost"]          * cost_scores[i]
            + WEIGHTS["latency"]       * latency_scores[i]
            + WEIGHTS["thai_quality"]  * thai_scores[i]
            + WEIGHTS["reliability"]   * reliability_vals[i]
            + WEIGHTS["privacy"]       * privacy_vals[i]
            + WEIGHTS["ease_switching"]* switching_vals[i]
        )
        scored.append({**r, "weighted_score": round(weighted, 4)})

    return sorted(scored, key=lambda x: x["weighted_score"], reverse=True)


# ── Rich output ───────────────────────────────────────────────────────────────

def _rich_tables(scored: list[dict]) -> None:
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # Quality table
    q_table = Table(
        title="[bold]Phase 3.5 — RAG Answer Quality (Token-overlap F1)[/bold]",
        show_lines=True,
    )
    q_table.add_column("Provider / Model", style="cyan", no_wrap=True)
    q_table.add_column("Overall F1", justify="right")
    q_table.add_column("Thai F1",    justify="right")
    q_table.add_column("Questions",  justify="right")

    for r in scored:
        q_table.add_row(
            r["meta"]["name"],
            f"{r['overall_f1']:.3f}",
            f"{r['thai_f1']:.3f}",
            str(r["num_questions"]),
        )
    console.print(q_table)

    # Cost & latency table
    lc_table = Table(
        title="[bold]Phase 3.5 — Cost & Latency[/bold]",
        show_lines=True,
    )
    lc_table.add_column("Provider / Model", style="cyan", no_wrap=True)
    lc_table.add_column("Avg Latency (ms)", justify="right")
    lc_table.add_column("Total Cost (USD)",  justify="right")
    lc_table.add_column("$/1M in",           justify="right")
    lc_table.add_column("$/1M out",          justify="right")
    lc_table.add_column("Self-hosted",        justify="center")

    for r in scored:
        m = r["meta"]
        in_str  = f"${m['cost_per_1m_input']:.3f}"  if m["cost_per_1m_input"]  > 0 else "FREE"
        out_str = f"${m['cost_per_1m_output']:.3f}" if m["cost_per_1m_output"] > 0 else "FREE"
        lc_table.add_row(
            m["name"],
            f"{r['avg_latency_ms']:.0f}",
            f"${r['total_cost_usd']:.4f}",
            in_str,
            out_str,
            "✅" if m["self_hostable"] else "❌",
        )
    console.print(lc_table)

    # Vendor attributes table
    attr_table = Table(
        title="[bold]Phase 3.5 — Vendor Attributes[/bold]",
        show_lines=True,
    )
    attr_table.add_column("Provider / Model", style="cyan", no_wrap=True)
    attr_table.add_column("Lock-in\n(0=open)", justify="right")
    attr_table.add_column("OpenAI-compat", justify="center")
    attr_table.add_column("Reliability", justify="right")
    attr_table.add_column("Privacy", justify="right")
    attr_table.add_column("Switch-ease", justify="right")

    for r in scored:
        m = r["meta"]
        p = m["provider"]
        attr_table.add_row(
            m["name"],
            str(m["vendor_lock_in"]),
            "✅" if m["openai_compatible"] else "❌",
            f"{_RELIABILITY.get(p, 0.7):.0%}",
            f"{_PRIVACY.get(p, 0.5):.0%}",
            f"{_EASE_SWITCHING.get(p, 0.5):.0%}",
        )
    console.print(attr_table)

    # Weighted scorecard
    score_table = Table(
        title=(
            "[bold]Phase 3.5 — Weighted Scorecard[/bold]  "
            "(Quality 20% · Lock-in 20% · Cost 15% · Latency 15% · "
            "Thai 10% · Reliability 10% · Privacy 5% · Switch 5%)"
        ),
        show_lines=True,
    )
    score_table.add_column("Rank",           justify="right")
    score_table.add_column("Provider / Model", style="cyan", no_wrap=True)
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
    parser = argparse.ArgumentParser(description="Phase 3.5: LLM Provider Benchmark")
    parser.add_argument(
        "--providers",
        nargs="+",
        default=list(DEFAULT_PROVIDERS),
        choices=list(PROVIDER_REGISTRY.keys()) + ["all"],
        help=(
            "Which providers to evaluate. "
            "Default: openrouter_gpt4o_mini. "
            "Use 'all' to run every registered provider."
        ),
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=config.TOP_K,
        help=f"Chunks retrieved per question (default: {config.TOP_K})",
    )
    parser.add_argument(
        "--output",
        default=str(RESULTS_DIR / "llm_provider_results.json"),
        help="Output JSON path",
    )
    args = parser.parse_args()

    providers = (
        list(PROVIDER_REGISTRY.keys())
        if "all" in args.providers
        else args.providers
    )

    # Verify datasets
    missing = [f for f in ALL_DOC_FILES if not Path(f).exists()]
    if missing:
        print(f"⚠️  Missing dataset files: {missing}")
        sys.exit(1)

    chunks    = _load_corpus()
    questions = _load_questions()
    tfs, idf  = _build_tfidf(chunks)

    print(f"\nCorpus:    {len(chunks)} chunks from {len(ALL_DOC_FILES)} documents")
    print(f"Questions: {len(questions)}")
    print(f"Providers: {providers}")
    print(f"Top-k:     {args.top_k}\n")

    all_results: list[dict] = []
    for name in providers:
        res = _evaluate_provider(name, chunks, tfs, idf, questions, args.top_k)
        if res is not None:
            all_results.append(res)

    if not all_results:
        print("No providers evaluated successfully.")
        sys.exit(1)

    scored = _compute_scores(all_results)
    _rich_tables(scored)

    out = {
        "phase":          "3.5",
        "top_k":          args.top_k,
        "chunk_size":     config.CHUNK_SIZE,
        "chunk_overlap":  config.CHUNK_OVERLAP,
        "num_chunks":     len(chunks),
        "num_questions":  len(questions),
        "weights":        WEIGHTS,
        "results":        scored,
    }
    out_path = Path(args.output)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Results saved → {out_path}")


if __name__ == "__main__":
    main()
