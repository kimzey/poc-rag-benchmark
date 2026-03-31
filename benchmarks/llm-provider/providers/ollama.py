"""Phase 3.5 — Ollama self-hosted provider adapter.

Ollama exposes an OpenAI-compatible endpoint at localhost.
Zero API cost, full privacy, but requires local GPU/CPU inference.

Usage: start Ollama locally, set OLLAMA_MODEL in .env (default: llama3.1:8b)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from base import BaseLLMProvider, ProviderMeta


class OllamaProvider(BaseLLMProvider):

    def __init__(self, model_id: str | None = None) -> None:
        self._model_id = model_id or config.OLLAMA_MODEL
        self._meta = ProviderMeta(
            name=f"Ollama / {self._model_id}",
            model_id=self._model_id,
            provider="ollama",
            cost_per_1m_input=0.0,
            cost_per_1m_output=0.0,
            vendor_lock_in=0,   # fully open — swap model, run anywhere
            self_hostable=True,
            openai_compatible=True,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
        from openai import OpenAI, APIConnectionError

        client = OpenAI(
            base_url=f"{config.OLLAMA_BASE_URL}/v1",
            api_key="ollama",   # Ollama ignores the key value
        )
        full_prompt = config.RAG_PROMPT_TEMPLATE.format(
            context=context, question=prompt
        )
        try:
            resp = client.chat.completions.create(
                model=self._model_id,
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user",   "content": full_prompt},
                ],
                max_tokens=config.MAX_NEW_TOKENS,
                temperature=config.TEMPERATURE,
            )
        except APIConnectionError:
            raise EnvironmentError(
                f"Cannot connect to Ollama at {config.OLLAMA_BASE_URL} — "
                "is Ollama running? (`ollama serve`)"
            )

        text = resp.choices[0].message.content or ""
        usage = resp.usage
        # Ollama may not always return token counts
        in_tok  = usage.prompt_tokens if usage else 0
        out_tok = usage.completion_tokens if usage else 0
        return text.strip(), in_tok, out_tok
