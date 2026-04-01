"""Result viewer screen — reads existing benchmark JSON files and shows tables."""
from __future__ import annotations

import json
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widget import Widget
from textual.widgets import Label, Static, TabbedContent, TabPane

from tui.widgets.result_table import ResultTable

_ROOT = Path(__file__).parents[2]
_VDB_RESULTS   = _ROOT / "benchmarks" / "vector-db"   / "results"
_RAG_RESULTS   = _ROOT / "benchmarks" / "rag-framework"/ "results"
_EMB_RESULTS   = _ROOT / "benchmarks" / "embedding-model" / "results"
_LLM_RESULTS   = _ROOT / "benchmarks" / "llm-provider" / "results"


def _latest_json(directory: Path) -> dict | list | None:
    files = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text())
    except Exception:
        return None


def _fmt(val: object, decimals: int = 1) -> str:
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"{val:.{decimals}f}"
    return str(val)


# ── Vector DB tab ─────────────────────────────────────────────────────────────

class _VectorDBResult(ScrollableContainer):
    def on_show(self) -> None:
        self._load()

    def _load(self) -> None:
        data = _latest_json(_VDB_RESULTS)
        if not data:
            self.query_one("#vdb-msg", Static).update("[red]No result files found in benchmarks/vector-db/results/[/red]")
            return
        if not isinstance(data, list):
            data = [data]

        cols = ["DB", "Vectors", "Idx(s)", "Throughput", "p50(ms)", "p95(ms)", "p99(ms)", "QPS", "Filter p95", "Recall@10"]
        rows = []
        for r in data:
            sl = r.get("search_latency", {})
            fl = r.get("filtered_latency", {})
            rows.append([
                r.get("db_name", "?"),
                _fmt(r.get("n_vectors"), 0),
                _fmt(r.get("index_time_s"), 1),
                _fmt(r.get("index_throughput"), 1),
                _fmt(sl.get("p50_ms"), 1),
                _fmt(sl.get("p95_ms"), 1),
                _fmt(sl.get("p99_ms"), 1),
                _fmt(sl.get("qps"), 1),
                _fmt(fl.get("p95_ms"), 1),
                _fmt(r.get("recall_at_10")),
            ])
        self.query_one("#vdb-msg", Static).update("")
        self.query_one(ResultTable).load(cols, rows)

    def compose(self) -> ComposeResult:
        yield Static("", id="vdb-msg")
        yield ResultTable(title="Vector DB Search Latency & Throughput")


# ── RAG Framework tab ─────────────────────────────────────────────────────────

class _RAGFrameworkResult(ScrollableContainer):
    def on_show(self) -> None:
        self._load()

    def _load(self) -> None:
        data = _latest_json(_RAG_RESULTS)
        if not data:
            self.query_one("#rag-msg", Static).update(
                "[red]No result files found in benchmarks/rag-framework/results/[/red]"
            )
            return
        results = data.get("results", []) if isinstance(data, dict) else data

        # Indexing table
        idx_cols = ["Framework", "Chunks", "Idx(ms)", "LOC"]
        idx_rows = []
        # Query latency table
        lat_cols = ["Framework", "Min(ms)", "Avg(ms)", "Max(ms)", "p95(ms)"]
        lat_rows = []

        for r in results:
            fw = r.get("framework", "?")
            idx_rows.append([
                fw,
                _fmt(r.get("num_chunks"), 0),
                _fmt(r.get("indexing_time_ms"), 1),
                _fmt(r.get("loc"), 0),
            ])
            queries = r.get("queries", [])
            if queries:
                latencies = [q.get("latency_ms", 0) for q in queries]
                sorted_lat = sorted(latencies)
                p95_idx = int(len(sorted_lat) * 0.95)
                lat_rows.append([
                    fw,
                    _fmt(min(latencies), 1),
                    _fmt(sum(latencies) / len(latencies), 1),
                    _fmt(max(latencies), 1),
                    _fmt(sorted_lat[min(p95_idx, len(sorted_lat)-1)], 1),
                ])

        self.query_one("#rag-msg", Static).update("")
        tables = self.query(ResultTable)
        tables[0].load(idx_cols, idx_rows)
        tables[1].load(lat_cols, lat_rows)

    def compose(self) -> ComposeResult:
        yield Static("", id="rag-msg")
        yield ResultTable(title="Indexing")
        yield ResultTable(title="Query Latency")


# ── Embedding Model tab ───────────────────────────────────────────────────────

class _EmbeddingModelResult(ScrollableContainer):
    def on_show(self) -> None:
        self._load()

    def _load(self) -> None:
        data = _latest_json(_EMB_RESULTS)
        if not data:
            self.query_one("#emb-msg", Static).update(
                "[red]No result files found in benchmarks/embedding-model/results/[/red]"
            )
            return
        results = data.get("results", []) if isinstance(data, dict) else data

        quality_cols = ["Model", "Thai Recall", "Eng Recall", "Overall", "MRR"]
        quality_rows = []
        latency_cols = ["Model", "Idx(ms)", "Avg Query(ms)", "Cost/1M", "Self-host"]
        latency_rows = []

        for r in results:
            model = r.get("model", "?")
            meta = r.get("meta", {})
            quality_rows.append([
                model,
                _fmt(r.get("thai_recall"), 3),
                _fmt(r.get("eng_recall"), 3),
                _fmt(r.get("overall_recall"), 3),
                _fmt(r.get("mrr"), 3),
            ])
            latency_rows.append([
                model,
                _fmt(r.get("index_time_ms"), 1),
                _fmt(r.get("avg_query_latency_ms"), 1),
                _fmt(meta.get("cost_per_1m_tokens"), 4),
                "Yes" if meta.get("self_hostable") else "No",
            ])

        self.query_one("#emb-msg", Static).update("")
        tables = self.query(ResultTable)
        tables[0].load(quality_cols, quality_rows)
        tables[1].load(latency_cols, latency_rows)

    def compose(self) -> ComposeResult:
        yield Static("", id="emb-msg")
        yield ResultTable(title="Retrieval Quality")
        yield ResultTable(title="Latency & Cost")


# ── LLM Provider tab ──────────────────────────────────────────────────────────

class _LLMProviderResult(ScrollableContainer):
    def on_show(self) -> None:
        self._load()

    def _load(self) -> None:
        data = _latest_json(_LLM_RESULTS)
        if not data:
            self.query_one("#llm-msg", Static).update(
                "[red]No result files found in benchmarks/llm-provider/results/[/red]"
            )
            return
        results = data.get("results", []) if isinstance(data, dict) else data

        quality_cols = ["Provider", "Overall F1", "Thai F1", "Questions"]
        quality_rows = []
        cost_cols = ["Provider", "Avg Lat(ms)", "Total Cost($)", "$/1M in", "$/1M out"]
        cost_rows = []

        for r in results:
            provider = r.get("provider", "?")
            meta = r.get("meta", {})
            quality_rows.append([
                meta.get("name", provider),
                _fmt(r.get("overall_f1"), 4),
                _fmt(r.get("thai_f1"), 4),
                _fmt(r.get("num_questions"), 0),
            ])
            cost_rows.append([
                meta.get("name", provider),
                _fmt(r.get("avg_latency_ms"), 1),
                _fmt(r.get("total_cost_usd"), 6),
                _fmt(meta.get("cost_per_1m_input"), 3),
                _fmt(meta.get("cost_per_1m_output"), 3),
            ])

        self.query_one("#llm-msg", Static).update("")
        tables = self.query(ResultTable)
        tables[0].load(quality_cols, quality_rows)
        tables[1].load(cost_cols, cost_rows)

    def compose(self) -> ComposeResult:
        yield Static("", id="llm-msg")
        yield ResultTable(title="Answer Quality")
        yield ResultTable(title="Cost & Latency")


# ── Main panel ────────────────────────────────────────────────────────────────

class ResultsPanel(Widget):
    """Result viewer panel with TabbedContent (4 benchmark phases)."""

    def compose(self) -> ComposeResult:
        yield Label("Benchmark Results", id="results-title")
        with TabbedContent(id="results-tabs"):
            with TabPane("Vector DB", id="rtab-vdb"):
                yield _VectorDBResult()
            with TabPane("RAG Framework", id="rtab-rag"):
                yield _RAGFrameworkResult()
            with TabPane("Embedding Model", id="rtab-emb"):
                yield _EmbeddingModelResult()
            with TabPane("LLM Provider", id="rtab-llm"):
                yield _LLMProviderResult()
