"""Latency and recall metric helpers."""
import time
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class LatencyStats:
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    qps: float


@dataclass
class BenchmarkResult:
    db_name: str
    n_vectors: int
    dim: int
    index_time_s: float
    index_throughput: float        # vectors/sec
    search_latency: LatencyStats
    filtered_latency: LatencyStats | None
    recall_at_10: float | None     # None if ground truth not available
    notes: str = ""


def measure_latencies(times_ms: list[float]) -> LatencyStats:
    arr = np.array(times_ms)
    total_s = arr.sum() / 1000
    return LatencyStats(
        p50_ms=float(np.percentile(arr, 50)),
        p95_ms=float(np.percentile(arr, 95)),
        p99_ms=float(np.percentile(arr, 99)),
        mean_ms=float(np.mean(arr)),
        qps=float(len(arr) / total_s) if total_s > 0 else 0.0,
    )


def compute_recall(
    results: list[list[str]],
    ground_truth: list[set[str]],
) -> float:
    hits = sum(
        len(set(r) & gt) for r, gt in zip(results, ground_truth)
    )
    total = sum(len(gt) for gt in ground_truth)
    return hits / total if total > 0 else 0.0


def save_results(results: list[BenchmarkResult], output_dir: str) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    file = path / f"results_{ts}.json"
    file.write_text(json.dumps([asdict(r) for r in results], indent=2))
    return file
