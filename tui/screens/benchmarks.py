"""Benchmark runner screen — 4 tabs, one per benchmark phase."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Input, Label, Rule, TabbedContent, TabPane

from tui.widgets.benchmark_progress import BenchmarkProgress

# Project root
_ROOT = Path(__file__).parents[2]
_UV = "uv"


def _uv_run(*args: str) -> list[str]:
    return [_UV, "run", *args]


class _VectorDBTab(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Vector DB Benchmark", classes="section-header")
        yield Label("Select databases to benchmark:", classes="dim-label")
        with Horizontal(id="vdb-checks"):
            yield Checkbox("Qdrant",     id="vdb-qdrant",     value=True)
            yield Checkbox("pgvector",   id="vdb-pgvector",   value=True)
            yield Checkbox("Milvus",     id="vdb-milvus",     value=True)
            yield Checkbox("OpenSearch", id="vdb-opensearch",  value=True)
        with Horizontal(id="vdb-options"):
            yield Label("N vectors:")
            yield Input("10000", id="vdb-n", restrict="0-9", max_length=7, classes="short-input")
        yield Label(
            "[dim]Requires Docker: [bold]make up-db[/bold][/dim]",
            id="vdb-prereq",
        )
        yield Rule()
        yield Button("Run Vector DB Benchmark", id="btn-run-vdb", variant="primary")
        yield BenchmarkProgress(id="vdb-progress")

    @on(Button.Pressed, "#btn-run-vdb")
    def run_vdb(self) -> None:
        n = self.query_one("#vdb-n", Input).value.strip() or "10000"
        script = str(_ROOT / "benchmarks" / "vector-db" / "run_benchmark.py")
        cmd = _uv_run("python", script, "--n", n, "--quiet")
        self.query_one("#vdb-progress", BenchmarkProgress).run_command(
            cmd, cwd=str(_ROOT)
        )


class _RAGFrameworkTab(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("RAG Framework Benchmark", classes="section-header")
        yield Label("Select frameworks:", classes="dim-label")
        with Horizontal(id="rag-checks"):
            yield Checkbox("bare_metal",  id="rag-bare",   value=True)
            yield Checkbox("LlamaIndex",  id="rag-llama",  value=True)
            yield Checkbox("LangChain",   id="rag-lang",   value=True)
            yield Checkbox("Haystack",    id="rag-hay",    value=True)
        with Horizontal(id="rag-options"):
            yield Checkbox("--no-llm (retrieval only)", id="rag-nollm", value=False)
        yield Label("[dim]OPENROUTER_API_KEY required for LLM mode[/dim]", id="rag-key-hint")
        yield Rule()
        yield Button("Run RAG Framework Benchmark", id="btn-run-rag", variant="primary")
        yield BenchmarkProgress(id="rag-progress")

    @on(Button.Pressed, "#btn-run-rag")
    def run_rag(self) -> None:
        script = str(_ROOT / "benchmarks" / "rag-framework" / "evaluate.py")
        fw_map = {
            "rag-bare":  "bare_metal",
            "rag-llama": "llamaindex",
            "rag-lang":  "langchain",
            "rag-hay":   "haystack",
        }
        selected = [
            fw_map[cb.id]
            for cb in self.query(Checkbox)
            if cb.id in fw_map and cb.value
        ]
        cmd = _uv_run("python", script, "--frameworks", *(selected or ["all"]))
        if self.query_one("#rag-nollm", Checkbox).value:
            cmd.append("--no-llm")
        self.query_one("#rag-progress", BenchmarkProgress).run_command(
            cmd, cwd=str(_ROOT)
        )


class _EmbeddingModelTab(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Embedding Model Benchmark", classes="section-header")
        yield Label("Select models:", classes="dim-label")
        with Horizontal(id="emb-checks"):
            yield Checkbox("multilingual_e5", id="emb-e5",      value=True)
            yield Checkbox("bge_m3",          id="emb-bge",     value=True)
            yield Checkbox("mxbai",           id="emb-mxbai",   value=True)
            yield Checkbox("openai_large",    id="emb-oai-lg",  value=False)
            yield Checkbox("openai_small",    id="emb-oai-sm",  value=False)
        with Horizontal(id="emb-options"):
            yield Label("top_k:")
            yield Input("3", id="emb-topk", restrict="0-9", max_length=2, classes="short-input")
        yield Label("[dim]OPENAI_API_KEY required for openai_* models[/dim]", id="emb-key-hint")
        yield Rule()
        yield Button("Run Embedding Benchmark", id="btn-run-emb", variant="primary")
        yield BenchmarkProgress(id="emb-progress")

    @on(Button.Pressed, "#btn-run-emb")
    def run_emb(self) -> None:
        script = str(_ROOT / "benchmarks" / "embedding-model" / "evaluate.py")
        model_map = {
            "emb-e5":     "multilingual_e5",
            "emb-bge":    "bge_m3",
            "emb-mxbai":  "mxbai",
            "emb-oai-lg": "openai_large",
            "emb-oai-sm": "openai_small",
        }
        selected = [
            model_map[cb.id]
            for cb in self.query(Checkbox)
            if cb.id in model_map and cb.value
        ]
        top_k = self.query_one("#emb-topk", Input).value.strip() or "3"
        cmd = _uv_run("python", script, "--models", *(selected or ["all"]), "--top-k", top_k)
        self.query_one("#emb-progress", BenchmarkProgress).run_command(
            cmd, cwd=str(_ROOT)
        )


class _LLMProviderTab(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("LLM Provider Benchmark", classes="section-header")
        yield Label("API key status:", classes="dim-label")
        yield Label("", id="llm-key-status")
        yield Rule()
        with Horizontal(id="llm-options"):
            yield Label("top_k:")
            yield Input("3", id="llm-topk", restrict="0-9", max_length=2, classes="short-input")
        yield Button("Run LLM Provider Benchmark", id="btn-run-llm", variant="primary")
        yield BenchmarkProgress(id="llm-progress")

    def on_show(self) -> None:
        keys = [
            ("OPENROUTER", "OPENROUTER_API_KEY"),
            ("OPENAI",     "OPENAI_API_KEY"),
            ("ANTHROPIC",  "ANTHROPIC_API_KEY"),
            ("COHERE",     "COHERE_API_KEY"),
        ]
        lines = [
            f"{'[green]✓[/green]' if os.getenv(k) else '[red]✗[/red]'} {name}"
            for name, k in keys
        ]
        try:
            self.query_one("#llm-key-status", Label).update("\n".join(lines))
        except Exception:
            pass

    @on(Button.Pressed, "#btn-run-llm")
    def run_llm(self) -> None:
        script = str(_ROOT / "benchmarks" / "llm-provider" / "evaluate.py")
        top_k = self.query_one("#llm-topk", Input).value.strip() or "3"
        cmd = _uv_run("python", script, "--top-k", top_k)
        self.query_one("#llm-progress", BenchmarkProgress).run_command(
            cmd, cwd=str(_ROOT)
        )


class BenchmarksPanel(Widget):
    """Benchmark runner panel with TabbedContent (4 phases)."""

    def compose(self) -> ComposeResult:
        yield Label("Benchmark Runner", id="bench-title")
        with TabbedContent(id="bench-tabs"):
            with TabPane("Vector DB", id="tab-vdb"):
                yield _VectorDBTab()
            with TabPane("RAG Framework", id="tab-rag"):
                yield _RAGFrameworkTab()
            with TabPane("Embedding Model", id="tab-emb"):
                yield _EmbeddingModelTab()
            with TabPane("LLM Provider", id="tab-llm"):
                yield _LLMProviderTab()
