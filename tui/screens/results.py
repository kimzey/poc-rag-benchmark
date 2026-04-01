"""Result viewer screen — reads existing benchmark JSON files and shows tables."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.widget import Widget
from textual.widgets import Label, Select, Static, TabbedContent, TabPane

from tui.widgets.result_table import ResultTable

_ROOT = Path(__file__).parents[2]
_VDB_RESULTS = _ROOT / "benchmarks" / "vector-db" / "results"
_RAG_RESULTS = _ROOT / "benchmarks" / "rag-framework" / "results"
_EMB_RESULTS = _ROOT / "benchmarks" / "embedding-model" / "results"
_LLM_RESULTS = _ROOT / "benchmarks" / "llm-provider" / "results"


def _list_jsons(directory: Path) -> list[tuple[str, Path]]:
    """Return (label, path) list sorted newest first."""
    files = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        (f"{f.name}  [{datetime.fromtimestamp(f.stat().st_mtime).strftime('%m-%d %H:%M')}]", f)
        for f in files
    ]


def _load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text())
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
        self._refresh_selector()

    def _refresh_selector(self) -> None:
        options = _list_jsons(_VDB_RESULTS)
        row = self.query_one("#vdb-sel-row")
        msg = self.query_one("#vdb-msg", Static)
        if not options:
            row.display = False
            msg.update("[red]No result files found in benchmarks/vector-db/results/[/red]")
            return
        row.display = True
        sel = self.query_one("#vdb-file-sel", Select)
        sel.set_options(options)
        sel.value = options[0][1]

    def _load(self, path: Path) -> None:
        data = _load_json(path)
        msg = self.query_one("#vdb-msg", Static)
        if not data:
            msg.update(f"[red]Failed to load {path.name}[/red]")
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
        if not rows:
            msg.update(f"[dim]{path.name}[/dim]  [yellow]No data rows in file[/yellow]")
        else:
            msg.update(f"[dim]{path.name}[/dim]  [green]{len(rows)} records[/green]")
        self.query_one(ResultTable).load(cols, rows)

    @on(Select.Changed, "#vdb-file-sel")
    def on_file_changed(self, event: Select.Changed) -> None:
        if event.value is not Select.BLANK:
            self._load(event.value)

    def compose(self) -> ComposeResult:
        with Horizontal(id="vdb-sel-row", classes="file-sel-row"):
            yield Label("File: ", classes="file-sel-label")
            yield Select([], id="vdb-file-sel", prompt="Select result file...")
        yield Static("", id="vdb-msg")
        yield ResultTable(title="Vector DB Search Latency & Throughput")


# ── RAG Framework tab ─────────────────────────────────────────────────────────

class _RAGFrameworkResult(ScrollableContainer):
    def on_show(self) -> None:
        self._refresh_selector()

    def _refresh_selector(self) -> None:
        options = _list_jsons(_RAG_RESULTS)
        row = self.query_one("#rag-sel-row")
        msg = self.query_one("#rag-msg", Static)
        if not options:
            row.display = False
            msg.update("[red]No result files found in benchmarks/rag-framework/results/[/red]")
            return
        row.display = True
        sel = self.query_one("#rag-file-sel", Select)
        sel.set_options(options)
        sel.value = options[0][1]

    def _load(self, path: Path) -> None:
        data = _load_json(path)
        msg = self.query_one("#rag-msg", Static)
        if not data:
            msg.update(f"[red]Failed to load {path.name}[/red]")
            return
        results = data.get("results", []) if isinstance(data, dict) else data

        idx_cols = ["Framework", "Chunks", "Idx(ms)", "LOC"]
        idx_rows = []
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
                    _fmt(sorted_lat[min(p95_idx, len(sorted_lat) - 1)], 1),
                ])

        if not idx_rows:
            msg.update(f"[dim]{path.name}[/dim]  [yellow]No data rows in file (run: make rag-eval)[/yellow]")
        else:
            msg.update(f"[dim]{path.name}[/dim]  [green]{len(idx_rows)} frameworks[/green]")
        tables = self.query(ResultTable)
        tables[0].load(idx_cols, idx_rows)
        tables[1].load(lat_cols, lat_rows)

    @on(Select.Changed, "#rag-file-sel")
    def on_file_changed(self, event: Select.Changed) -> None:
        if event.value is not Select.BLANK:
            self._load(event.value)

    def compose(self) -> ComposeResult:
        with Horizontal(id="rag-sel-row", classes="file-sel-row"):
            yield Label("File: ", classes="file-sel-label")
            yield Select([], id="rag-file-sel", prompt="Select result file...")
        yield Static("", id="rag-msg")
        yield ResultTable(title="Indexing")
        yield ResultTable(title="Query Latency")


# ── Embedding Model tab ───────────────────────────────────────────────────────

class _EmbeddingModelResult(ScrollableContainer):
    def on_show(self) -> None:
        self._refresh_selector()

    def _refresh_selector(self) -> None:
        options = _list_jsons(_EMB_RESULTS)
        row = self.query_one("#emb-sel-row")
        msg = self.query_one("#emb-msg", Static)
        if not options:
            row.display = False
            msg.update("[red]No result files found in benchmarks/embedding-model/results/[/red]")
            return
        row.display = True
        sel = self.query_one("#emb-file-sel", Select)
        sel.set_options(options)
        sel.value = options[0][1]

    def _load(self, path: Path) -> None:
        data = _load_json(path)
        msg = self.query_one("#emb-msg", Static)
        if not data:
            msg.update(f"[red]Failed to load {path.name}[/red]")
            return
        results = data.get("results", []) if isinstance(data, dict) else data

        quality_cols = ["Model", "Thai Recall", "Eng Recall", "Overall", "MRR"]
        quality_rows = []
        latency_cols = ["Model", "Idx(ms)", "Avg Query(ms)", "Cost/1M", "Self-host"]
        latency_rows = []
        score_cols = ["Rank", "Model", "Weighted Score", "Dims", "Max Tokens", "Lock-in"]
        score_rows = []

        for rank, r in enumerate(results, start=1):
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
            score_rows.append([
                str(rank),
                meta.get("name", model),
                _fmt(r.get("weighted_score"), 4),
                str(meta.get("dimensions", "?")),
                str(meta.get("max_tokens", "?")),
                str(meta.get("vendor_lock_in", "?")),
            ])

        if not quality_rows:
            msg.update(f"[dim]{path.name}[/dim]  [yellow]No data rows in file (run: make embed-eval)[/yellow]")
        else:
            msg.update(f"[dim]{path.name}[/dim]  [green]{len(quality_rows)} models[/green]")
        tables = self.query(ResultTable)
        tables[0].load(quality_cols, quality_rows)
        tables[1].load(latency_cols, latency_rows)
        tables[2].load(score_cols, score_rows)

    @on(Select.Changed, "#emb-file-sel")
    def on_file_changed(self, event: Select.Changed) -> None:
        if event.value is not Select.BLANK:
            self._load(event.value)

    def compose(self) -> ComposeResult:
        with Horizontal(id="emb-sel-row", classes="file-sel-row"):
            yield Label("File: ", classes="file-sel-label")
            yield Select([], id="emb-file-sel", prompt="Select result file...")
        yield Static("", id="emb-msg")
        yield ResultTable(title="Retrieval Quality")
        yield ResultTable(title="Latency & Cost")
        yield ResultTable(title="Weighted Scorecard (Thai 25%·Eng 15%·Latency 15%·Cost 15%·Self-host 10%·Dims 5%·MaxTok 5%·Lock-in 10%)")


# ── LLM Provider tab ──────────────────────────────────────────────────────────

class _LLMProviderResult(ScrollableContainer):
    def on_show(self) -> None:
        self._refresh_selector()

    def _refresh_selector(self) -> None:
        options = _list_jsons(_LLM_RESULTS)
        row = self.query_one("#llm-sel-row")
        msg = self.query_one("#llm-msg", Static)
        if not options:
            row.display = False
            msg.update("[red]No result files found in benchmarks/llm-provider/results/[/red]")
            return
        row.display = True
        sel = self.query_one("#llm-file-sel", Select)
        sel.set_options(options)
        sel.value = options[0][1]

    def _load(self, path: Path) -> None:
        data = _load_json(path)
        msg = self.query_one("#llm-msg", Static)
        if not data:
            msg.update(f"[red]Failed to load {path.name}[/red]")
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

        if not quality_rows:
            msg.update(f"[dim]{path.name}[/dim]  [yellow]No data rows in file (run: make llm-eval)[/yellow]")
        else:
            msg.update(f"[dim]{path.name}[/dim]  [green]{len(quality_rows)} providers[/green]")
        tables = self.query(ResultTable)
        tables[0].load(quality_cols, quality_rows)
        tables[1].load(cost_cols, cost_rows)

    @on(Select.Changed, "#llm-file-sel")
    def on_file_changed(self, event: Select.Changed) -> None:
        if event.value is not Select.BLANK:
            self._load(event.value)

    def compose(self) -> ComposeResult:
        with Horizontal(id="llm-sel-row", classes="file-sel-row"):
            yield Label("File: ", classes="file-sel-label")
            yield Select([], id="llm-file-sel", prompt="Select result file...")
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
