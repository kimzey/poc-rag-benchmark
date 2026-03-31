#!/usr/bin/env python3
"""
Phase 1 — Vector DB Benchmark Runner

Usage:
  # Benchmark all DBs, 10K vectors, 100 queries
  python run_benchmark.py

  # Specific DB, larger dataset
  python run_benchmark.py --db qdrant --n 100000

  # Skip a DB (e.g. Milvus not running)
  python run_benchmark.py --skip milvus

  # List available DBs
  python run_benchmark.py --list
"""
import argparse
import sys
import time
from pathlib import Path

# Allow running as: python run_benchmark.py  (from this directory)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from clients.qdrant import QdrantAdapter
from clients.pgvector import PgvectorAdapter
from clients.milvus import MilvusAdapter
from clients.opensearch import OpenSearchAdapter
from clients.base import VectorDBClient
from utils.dataset import generate_dataset, generate_queries, compute_ground_truth
from utils.metrics import measure_latencies, compute_recall, save_results, BenchmarkResult

console = Console()

CLIENTS_MAP = {
    "qdrant": QdrantAdapter,
    "pgvector": PgvectorAdapter,
    "milvus": MilvusAdapter,
    "opensearch": OpenSearchAdapter,
}

N_QUERY_RUNS = 100          # queries to run for latency measurement
FILTER_RUNS = 50            # queries for filtered-search latency
TOP_K = 10


def run_single(
    client: VectorDBClient,
    dataset,
    queries,
    filtered_queries,
    ground_truth,
    n_vectors: int,
) -> BenchmarkResult | None:
    db = client.name

    # ── Connect ──────────────────────────────────────────────────────
    console.print(f"\n[bold cyan]▶ {db}[/bold cyan]")
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            t = progress.add_task("Connecting …", total=None)
            client.connect()
            progress.update(t, description="Connected")

            # ── Create collection ────────────────────────────────────
            progress.update(t, description="Creating collection …")
            client.create_collection("spike_benchmark")

            # ── Insert ───────────────────────────────────────────────
            progress.update(t, description=f"Inserting {n_vectors:,} vectors …")
            t0 = time.perf_counter()
            client.insert(dataset)
            index_time = time.perf_counter() - t0
            index_throughput = n_vectors / index_time
            progress.update(t, description=f"Indexed {n_vectors:,} → {index_throughput:,.0f} vec/s")

            # Verify
            count = client.count()
            if count != n_vectors:
                console.print(f"  [yellow]Warning: expected {n_vectors} but count={count}[/yellow]")

            # ── ANN search latency ────────────────────────────────────
            progress.update(t, description="Measuring ANN latency …")
            search_times = []
            result_ids: list[list[str]] = []
            for q in queries[:N_QUERY_RUNS]:
                t0 = time.perf_counter()
                hits = client.search(q, top_k=TOP_K)
                elapsed = (time.perf_counter() - t0) * 1000
                search_times.append(elapsed)
                result_ids.append([h.id for h in hits])
            search_stats = measure_latencies(search_times)

            # ── Filtered search latency ───────────────────────────────
            progress.update(t, description="Measuring filtered search latency …")
            filter_times = []
            for q in filtered_queries[:FILTER_RUNS]:
                t0 = time.perf_counter()
                client.search(q, top_k=TOP_K, filter={"access_level": "internal"})
                elapsed = (time.perf_counter() - t0) * 1000
                filter_times.append(elapsed)
            filtered_stats = measure_latencies(filter_times)

            # ── Recall@10 ────────────────────────────────────────────
            recall = None
            if ground_truth:
                progress.update(t, description="Computing recall@10 …")
                recall = compute_recall(result_ids, ground_truth[:N_QUERY_RUNS])

            # ── Cleanup ───────────────────────────────────────────────
            progress.update(t, description="Cleaning up …")
            client.drop_collection()
            progress.update(t, description="[green]Done[/green]")

    except Exception as exc:
        console.print(f"  [red]ERROR: {exc}[/red]")
        return None

    return BenchmarkResult(
        db_name=db,
        n_vectors=n_vectors,
        dim=VectorDBClient.DIM,
        index_time_s=round(index_time, 2),
        index_throughput=round(index_throughput, 1),
        search_latency=search_stats,
        filtered_latency=filtered_stats,
        recall_at_10=round(recall, 4) if recall else None,
    )


def print_summary(results: list[BenchmarkResult]) -> None:
    table = Table(title="Phase 1 — Vector DB Benchmark Summary", show_lines=True)
    table.add_column("DB", style="bold cyan", min_width=12)
    table.add_column("Vectors", justify="right")
    table.add_column("Index time (s)", justify="right")
    table.add_column("Throughput (v/s)", justify="right")
    table.add_column("Search p50 (ms)", justify="right")
    table.add_column("Search p95 (ms)", justify="right")
    table.add_column("Search p99 (ms)", justify="right")
    table.add_column("Search QPS", justify="right")
    table.add_column("Filter p95 (ms)", justify="right")
    table.add_column("Recall@10", justify="right")

    for r in results:
        recall_str = f"{r.recall_at_10:.1%}" if r.recall_at_10 is not None else "N/A"
        filter_p95 = f"{r.filtered_latency.p95_ms:.1f}" if r.filtered_latency else "N/A"
        table.add_row(
            r.db_name,
            f"{r.n_vectors:,}",
            str(r.index_time_s),
            f"{r.index_throughput:,.0f}",
            f"{r.search_latency.p50_ms:.1f}",
            f"{r.search_latency.p95_ms:.1f}",
            f"{r.search_latency.p99_ms:.1f}",
            f"{r.search_latency.qps:.0f}",
            filter_p95,
            recall_str,
        )

    console.print()
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Vector DB Phase 1 Benchmark")
    parser.add_argument("--db", help="Run only this DB (e.g. qdrant)")
    parser.add_argument("--skip", nargs="*", default=[], help="Skip these DBs")
    parser.add_argument("--n", type=int, default=10_000, help="Number of vectors (default 10000)")
    parser.add_argument("--list", action="store_true", help="List available DB adapters")
    args = parser.parse_args()

    if args.list:
        console.print("[bold]Available DBs:[/bold]", ", ".join(CLIENTS_MAP.keys()))
        return

    n_vectors = args.n
    skip = {s.lower() for s in args.skip}

    console.rule(f"[bold]Phase 1 — Vector DB Benchmark  (n={n_vectors:,})[/bold]")

    # ── Prepare data ─────────────────────────────────────────────────
    console.print(f"\n[dim]Generating {n_vectors:,} vectors (dim={VectorDBClient.DIM}) …[/dim]")
    dataset = generate_dataset(n_vectors)
    queries = generate_queries(N_QUERY_RUNS + FILTER_RUNS)
    search_queries = queries[:N_QUERY_RUNS]
    filter_queries = queries[N_QUERY_RUNS:]

    # Compute ground truth only for small datasets (brute-force is O(N*Q))
    ground_truth = None
    if n_vectors <= 50_000:
        console.print("[dim]Computing brute-force ground truth for recall@10 …[/dim]")
        ground_truth = compute_ground_truth(dataset, search_queries, top_k=TOP_K)

    # ── Select clients ────────────────────────────────────────────────
    target = {args.db.lower()} if args.db else set(CLIENTS_MAP.keys())
    selected = {k: v for k, v in CLIENTS_MAP.items() if k in target and k not in skip}

    if not selected:
        console.print("[red]No DBs selected. Use --list to see options.[/red]")
        return

    # ── Run benchmarks ────────────────────────────────────────────────
    results = []
    for key, cls in selected.items():
        result = run_single(cls(), dataset, search_queries, filter_queries, ground_truth, n_vectors)
        if result:
            results.append(result)

    if not results:
        console.print("[red]No results collected.[/red]")
        return

    # ── Summary table ─────────────────────────────────────────────────
    print_summary(results)

    # ── Save JSON ─────────────────────────────────────────────────────
    output_dir = Path(__file__).parent / "results"
    saved = save_results(results, str(output_dir))
    console.print(f"\n[green]Results saved to:[/green] {saved}\n")


if __name__ == "__main__":
    main()
