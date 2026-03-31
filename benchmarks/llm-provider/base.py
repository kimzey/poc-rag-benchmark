"""Abstract base class for Phase 3.5 LLM Provider benchmark."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GenerateResult:
    text: str               # Generated answer text
    latency_ms: float       # Wall time for the full response
    input_tokens: int       # Prompt tokens consumed
    output_tokens: int      # Completion tokens generated
    cost_usd: float         # Estimated cost in USD for this call


@dataclass
class ProviderMeta:
    """Static facts about an LLM provider / model (no API call needed)."""
    name: str               # Human-readable name (e.g. "OpenRouter / claude-3.5-sonnet")
    model_id: str           # API model string
    provider: str           # "openrouter" | "openai" | "anthropic" | "ollama"
    cost_per_1m_input: float    # USD; 0.0 for self-hosted
    cost_per_1m_output: float   # USD; 0.0 for self-hosted
    vendor_lock_in: int     # 0 = fully open, 10 = hard lock-in
    self_hostable: bool
    openai_compatible: bool # True if endpoint uses OpenAI-compatible API


class BaseLLMProvider(ABC):
    """Common interface every LLM provider adapter must implement."""

    @property
    @abstractmethod
    def meta(self) -> ProviderMeta: ...

    @abstractmethod
    def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
        """Send prompt+context to the provider.

        Returns (answer_text, input_tokens, output_tokens).
        Raises EnvironmentError if required API key / service is missing.
        """
        ...

    def generate(self, prompt: str, context: str) -> GenerateResult:
        """Generate an answer and record timing + cost."""
        t0 = time.perf_counter()
        text, in_tok, out_tok = self._generate_raw(prompt, context)
        latency_ms = (time.perf_counter() - t0) * 1000

        cost = (
            in_tok / 1_000_000 * self.meta.cost_per_1m_input
            + out_tok / 1_000_000 * self.meta.cost_per_1m_output
        )
        return GenerateResult(
            text=text,
            latency_ms=latency_ms,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
        )
