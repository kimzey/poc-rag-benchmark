"""Phase 3.5 — OpenAI Direct provider adapter.

Calls OpenAI API directly (no intermediary).
Included for baseline comparison against OpenRouter routing.

Usage: set OPENAI_API_KEY in .env
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from base import BaseLLMProvider, ProviderMeta

_MODELS: dict[str, dict] = {
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    },
}

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIDirectProvider(BaseLLMProvider):

    def __init__(self, model_id: str = DEFAULT_MODEL) -> None:
        if not config.OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY not set — skipping OpenAI Direct")
        self._model_id = model_id
        specs = _MODELS.get(model_id, {"input": 0.0, "output": 0.0})
        self._meta = ProviderMeta(
            name=f"OpenAI Direct / {model_id}",
            model_id=model_id,
            provider="openai",
            cost_per_1m_input=specs["input"],
            cost_per_1m_output=specs["output"],
            vendor_lock_in=8,   # direct dependency — high lock-in
            self_hostable=False,
            openai_compatible=True,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
        from openai import OpenAI

        client = OpenAI(api_key=config.OPENAI_API_KEY)
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
