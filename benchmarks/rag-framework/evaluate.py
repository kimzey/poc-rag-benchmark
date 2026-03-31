#!/usr/bin/env python3
"""
Phase 2: RAG Framework Comparison — Evaluation Runner

Usage:
    python evaluate.py                                  # run all frameworks
    python evaluate.py --frameworks bare_metal langchain
    python evaluate.py --frameworks all --no-llm        # retrieval only (no API key needed)
    python evaluate.py --questions 1 2 3               # specific question IDs
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.WARNING)

# ── Paths ─────────────────────────────────────────────────────────────────────
BENCH_DIR = Path(__file__).parent
sys.path.insert(0, str(BENCH_DIR))

import config
from base import BaseRAGPipeline, IndexStats, RAGResult

DATASETS_DIR = config.DATASETS_DIR
RESULTS_DIR = config.RESULTS_DIR
RESULTS_DIR.mkdir(exist_ok=True)

ALL_DOC_FILES = [
    str(DATASETS_DIR / "hr_policy_th.md"),
    str(DATASETS_DIR / "tech_docs_en.md"),
    str(DATASETS_DIR / "faq_mixed.md"),
]

FRAMEWORK_REGISTRY: dict[str, str] = {
    "bare_metal":    "frameworks.bare_metal.pipeline.BareMetalRAGPipeline",
    "llamaindex":    "frameworks.llamaindex_poc.pipeline.LlamaIndexRAGPipeline",
    "langchain":     "frameworks.langchain_poc.pipeline.LangChainRAGPipeline",
    "haystack":      "frameworks.haystack_poc.pipeline.HaystackRAGPipeline",
}


# ── Rich helpers ─────────────────────────────────────────────────────────────
def _rich_table(results: list[dict]) -> None:
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # ── Indexing table ──────────────────────────────────────────────────────
    idx_table = Table(title="[bold]Phase 2 — Indexing Stats[/bold]", show_lines=True)
    idx_table.add_column("Framework", style="cyan", no_wrap=True)
    idx_table.add_column("Chunks", justify="right")
    idx_table.add_column("Index Time (ms)", justify="right")
    idx_table.add_column("Non-blank LOC", justify="right")

    for r in results:
        idx_table.add_row(
            r["framework"],
            str(r["num_chunks"]),
            f"{r['indexing_time_ms']:.0f}",
            str(r["loc"]),
        )
    console.print(idx_table)

    # ── Query latency table ─────────────────────────────────────────────────
    q_table = Table(title="[bold]Phase 2 — Query Latency (ms)[/bold]", show_lines=True)
    q_table.add_column("Framework", style="cyan", no_wrap=True)
    q_table.add_column("Min", justify="right")
    q_table.add_column("Avg", justify="right")
    q_table.add_column("Max", justify="right")
    q_table.add_column("p95", justify="right")

    for r in results:
        latencies = [q["latency_ms"] for q in r["queries"]]
        if not latencies:
            continue
        latencies_sorted = sorted(latencies)
        p95_idx = int(len(latencies_sorted) * 0.95)
        q_table.add_row(
            r["framework"],
            f"{min(latencies):.0f}",
            f"{sum(latencies)/len(latencies):.0f}",
            f"{max(latencies):.0f}",
            f"{latencies_sorted[p95_idx]:.0f}",
        )
    console.print(q_table)

    # ── Swap-ability summary ────────────────────────────────────────────────
    swap_table = Table(
        title="[bold]Phase 2 — Component Swap-ability (manual assessment)[/bold]",
        show_lines=True,
    )
    swap_table.add_column("Framework", style="cyan")
    swap_table.add_column("Swap LLM", justify="center")
    swap_table.add_column("Swap VectorDB", justify="center")
    swap_table.add_column("Swap Embedder", justify="center")
    swap_table.add_column("Notes")

    swap_notes = {
        "bare_metal":  ("✅ 1 line", "✅ 1 class",  "✅ 1 line",  "Full control, all changes explicit"),
        "llamaindex":  ("✅ Settings", "⚠️  Plugin",   "✅ Settings", "Global Settings is footgun; plugin ecosystem varies"),
        "langchain":   ("✅ ChatModel", "⚠️  Plugin",  "✅ Embeddings", "LCEL composable; legacy chain API still prevalent"),
        "haystack":    ("✅ Component", "✅ Component", "✅ Component", "Explicit DAG makes swaps obvious but verbose"),
    }
    for r in results:
        notes = swap_notes.get(r["framework"], ("?", "?", "?", ""))
        swap_table.add_row(r["framework"], *notes)
    console.print(swap_table)


def _load_class(dotted_path: str) -> type:
    module_path, cls_name = dotted_path.rsplit(".", 1)
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, cls_name)


def _load_questions(question_ids: list[int] | None) -> list[dict]:
    q_path = DATASETS_DIR / "questions.json"
    questions: list[dict] = json.loads(q_path.read_text(encoding="utf-8"))
    if question_ids:
        questions = [q for q in questions if q["id"] in question_ids]
    return questions


def _run_framework(
    name: str,
    doc_files: list[str],
    questions: list[dict],
    no_llm: bool = False,
) -> dict:
    from rich.console import Console

    console = Console()
    console.rule(f"[bold cyan]{name}[/bold cyan]")

    cls = _load_class(FRAMEWORK_REGISTRY[name])
    pipeline: BaseRAGPipeline = cls()

    # Index
    console.print(f"  [dim]Indexing {len(doc_files)} documents...[/dim]")
    idx_stats = pipeline.build_index(doc_files)
    console.print(
        f"  ✓ {idx_stats.num_chunks} chunks indexed in {idx_stats.indexing_time_ms:.0f} ms"
    )

    loc = pipeline.loc
    console.print(f"  ✓ {loc} non-blank lines of code (pipeline.py)")

    query_results: list[dict] = []

    if no_llm:
        console.print("  [yellow]--no-llm: skipping generation (retrieval only)[/yellow]")
    else:
        for q in questions:
            console.print(f"  [dim]Q{q['id']}: {q['question'][:60]}...[/dim]")
            result = pipeline.query(q["question"])
            console.print(f"  → {result.answer[:120]}...")
            console.print(f"  → latency: {result.latency_ms:.0f} ms\n")
            query_results.append(
                {
                    "id": q["id"],
                    "question": q["question"],
                    "answer": result.answer,
                    "sources": result.sources,
                    "latency_ms": result.latency_ms,
                    "category": q.get("category", ""),
                }
            )

    return {
        "framework": name,
        "num_chunks": idx_stats.num_chunks,
        "indexing_time_ms": idx_stats.indexing_time_ms,
        "loc": loc,
        "queries": query_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2: RAG Framework Benchmark")
    parser.add_argument(
        "--frameworks",
        nargs="+",
        default=["all"],
        choices=list(FRAMEWORK_REGISTRY.keys()) + ["all"],
        help="Which frameworks to evaluate (default: all)",
    )
    parser.add_argument(
        "--questions",
        nargs="*",
        type=int,
        default=None,
        help="Question IDs to run (default: all)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM generation — only measure indexing (no API key needed)",
    )
    parser.add_argument(
        "--output",
        default=str(RESULTS_DIR / "rag_framework_results.json"),
        help="Output JSON path",
    )
    args = parser.parse_args()

    frameworks = (
        list(FRAMEWORK_REGISTRY.keys())
        if "all" in args.frameworks
        else args.frameworks
    )

    if not args.no_llm and not config.OPENROUTER_API_KEY:
        print(
            "⚠️  OPENROUTER_API_KEY not set. Use --no-llm to run retrieval-only, "
            "or set the key in .env"
        )
        sys.exit(1)

    questions = _load_questions(args.questions)

    # ── Check docs exist ──────────────────────────────────────────────────────
    missing = [f for f in ALL_DOC_FILES if not Path(f).exists()]
    if missing:
        print(f"⚠️  Missing dataset files: {missing}")
        print(f"   Expected in: {DATASETS_DIR}")
        sys.exit(1)

    all_results: list[dict] = []
    for name in frameworks:
        try:
            res = _run_framework(name, ALL_DOC_FILES, questions, no_llm=args.no_llm)
            all_results.append(res)
        except Exception as exc:
            print(f"  [ERROR] {name} failed: {exc}")
            import traceback; traceback.print_exc()

    # ── Print comparison tables ───────────────────────────────────────────────
    if all_results:
        _rich_table(all_results)

    # ── Save JSON results ─────────────────────────────────────────────────────
    out_path = Path(args.output)
    out_path.write_text(
        json.dumps(
            {
                "phase": 2,
                "embedding_model": config.EMBEDDING_MODEL,
                "llm_model": config.LLM_MODEL if not args.no_llm else "N/A (--no-llm)",
                "chunk_size": config.CHUNK_SIZE,
                "chunk_overlap": config.CHUNK_OVERLAP,
                "top_k": config.TOP_K,
                "results": all_results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\n✓ Results saved → {out_path}")


if __name__ == "__main__":
    main()
