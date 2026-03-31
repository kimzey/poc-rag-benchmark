"""Phase 3.5 — Anthropic Direct provider adapter.

Calls Anthropic API directly using the anthropic SDK.
Included to measure lock-in cost vs OpenRouter routing.

Usage: set ANTHROPIC_API_KEY in .env
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from base import BaseLLMProvider, ProviderMeta

_MODELS: dict[str, dict] = {
    "claude-3-5-sonnet-20241022": {
        "input": 3.00,
        "output": 15.00,
    },
    "claude-3-haiku-20240307": {
        "input": 0.25,
        "output": 1.25,
    },
}

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"


class AnthropicDirectProvider(BaseLLMProvider):

    def __init__(self, model_id: str = DEFAULT_MODEL) -> None:
        if not config.ANTHROPIC_API_KEY:
            raise EnvironmentError("ANTHROPIC_API_KEY not set — skipping Anthropic Direct")
        self._model_id = model_id
        specs = _MODELS.get(model_id, {"input": 0.0, "output": 0.0})
        short_name = model_id.split("-")[1] if "-" in model_id else model_id
        self._meta = ProviderMeta(
            name=f"Anthropic Direct / {model_id}",
            model_id=model_id,
            provider="anthropic",
            cost_per_1m_input=specs["input"],
            cost_per_1m_output=specs["output"],
            vendor_lock_in=8,   # proprietary SDK + API format — high lock-in
            self_hostable=False,
            openai_compatible=False,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        full_prompt = config.RAG_PROMPT_TEMPLATE.format(
            context=context, question=prompt
        )
        msg = client.messages.create(
            model=self._model_id,
            max_tokens=config.MAX_NEW_TOKENS,
            system=config.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": full_prompt}],
        )
        text = msg.content[0].text if msg.content else ""
        in_tok  = msg.usage.input_tokens
        out_tok = msg.usage.output_tokens
        return text.strip(), in_tok, out_tok
