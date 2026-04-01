"""Phase 3.5 — OpenRouter provider adapter.

OpenRouter exposes an OpenAI-compatible API that routes to dozens of models.
This is the KEY candidate for anti-vendor-lock-in strategy.

Usage: set OPENROUTER_API_KEY in .env
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from base import BaseLLMProvider, ProviderMeta

# OpenRouter pricing (USD per 1M tokens, as of 2026-03)
# Source: openrouter.ai/models
_MODELS: dict[str, dict] = {
    "anthropic/claude-3.5-sonnet-20241022": {
        "input": 3.00,
        "output": 15.00,
        "lock_in": 3,   # via OpenRouter — lower lock-in than direct
    },
    "openai/gpt-4o": {
        "input": 2.50,
        "output": 10.00,
        "lock_in": 3,
    },
    "openai/gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "lock_in": 3,
    },
    "google/gemini-2.0-flash-001": {
        "input": 0.10,
        "output": 0.40,
        "lock_in": 2,
    },
    "meta-llama/llama-3.1-70b-instruct": {
        "input": 0.35,
        "output": 0.40,
        "lock_in": 0,   # open-weight model
    },
    "deepseek/deepseek-chat": {
        "input": 0.14,
        "output": 0.28,
        "lock_in": 1,
    },
}

DEFAULT_MODEL = "openai/gpt-4o-mini"


class OpenRouterProvider(BaseLLMProvider):
    """Single OpenRouter adapter — swap model via constructor arg."""

    def __init__(self, model_id: str = DEFAULT_MODEL) -> None:
        if not config.OPENROUTER_API_KEY:
            raise EnvironmentError("OPENROUTER_API_KEY not set — skipping OpenRouter")
        self._model_id = model_id
        specs = _MODELS.get(model_id, {"input": 0.0, "output": 0.0, "lock_in": 3})
        short_name = model_id.split("/")[-1]
        self._meta = ProviderMeta(
            name=f"OpenRouter / {short_name}",
            model_id=model_id,
            provider="openrouter",
            cost_per_1m_input=specs["input"],
            cost_per_1m_output=specs["output"],
            vendor_lock_in=specs["lock_in"],
            self_hostable=False,
            openai_compatible=True,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
        from openai import OpenAI

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
        )
        full_prompt = config.RAG_PROMPT_TEMPLATE.format(
            context=context, question=prompt
        )
        resp = client.chat.completions.create(
            model=self._model_id,
            messages=[
                {"role": "system", "content": config.SYSTEM_PROMPT},
                {"role": "user",   "content": full_prompt},
            ],
            max_tokens=config.MAX_NEW_TOKENS,
            temperature=config.TEMPERATURE,
        )
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        in_tok  = usage.prompt_tokens if usage else 0
        out_tok = usage.completion_tokens if usage else 0
        return text.strip(), in_tok, out_tok
