# Anthropic Direct — Claude 3.5 Sonnet / Claude 3 Haiku

## คืออะไร

Anthropic Direct provider เรียก Anthropic API โดยตรงผ่าน `anthropic` Python SDK (ไม่ใช่ OpenAI-compatible) รองรับ 2 models: `claude-3-5-sonnet-20241022` (flagship) และ `claude-3-haiku-20240307` (fast/cheap)

จุดสังเกตสำคัญ: Anthropic ใช้ API format **ต่างจาก OpenAI** — ใช้ `messages.create()` แทน `chat.completions.create()`, และ response structure ต่างกัน

- Provider: api.anthropic.com
- SDK: `anthropic` (proprietary, ไม่ใช่ OpenAI SDK)
- Vendor lock-in: 8/10
- Self-hostable: ❌
- OpenAI-compatible: ❌

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/llm-provider/providers/anthropic_direct.py
benchmarks/llm-provider/base.py
benchmarks/llm-provider/config.py
```

---

## โครงสร้าง Code (`providers/anthropic_direct.py`)

```python
_MODELS = {
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307":    {"input": 0.25, "output": 1.25},
}
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

class AnthropicDirectProvider(BaseLLMProvider):
    def __init__(self, model_id: str = DEFAULT_MODEL) -> None:
        if not config.ANTHROPIC_API_KEY:
            raise EnvironmentError("ANTHROPIC_API_KEY not set — skipping Anthropic Direct")
        self._meta = ProviderMeta(
            ...
            vendor_lock_in=8,     # proprietary SDK + non-OpenAI format — high lock-in
            self_hostable=False,
            openai_compatible=False,  # ❌ ใช้ Anthropic API format
        )
```

---

## อธิบาย Code ทีละส่วน

### `_generate_raw()` — Anthropic SDK (ต่างจาก OpenAI)

```python
def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    full_prompt = config.RAG_PROMPT_TEMPLATE.format(
        context=context, question=prompt
    )

    # Anthropic API format — ต่างจาก OpenAI
    msg = client.messages.create(
        model=self._model_id,
        max_tokens=config.MAX_NEW_TOKENS,
        system=config.SYSTEM_PROMPT,       # ← Anthropic: system แยก parameter
        messages=[
            {"role": "user", "content": full_prompt}
        ],
    )

    # Response structure ต่างจาก OpenAI
    text   = msg.content[0].text if msg.content else ""
    in_tok  = msg.usage.input_tokens     # ← Anthropic: input_tokens (ไม่ใช่ prompt_tokens)
    out_tok = msg.usage.output_tokens    # ← Anthropic: output_tokens (ไม่ใช่ completion_tokens)
    return text.strip(), in_tok, out_tok
```

---

## API Format Comparison: OpenAI vs Anthropic

| ประเด็น | OpenAI | Anthropic |
|--------|--------|----------|
| Method | `chat.completions.create()` | `messages.create()` |
| System prompt | `messages=[{"role":"system",...}]` | `system=...` parameter แยก |
| Response text | `resp.choices[0].message.content` | `msg.content[0].text` |
| Input tokens | `resp.usage.prompt_tokens` | `msg.usage.input_tokens` |
| Output tokens | `resp.usage.completion_tokens` | `msg.usage.output_tokens` |
| SDK | `openai.OpenAI` | `anthropic.Anthropic` |

---

## Claude 3.5 Sonnet vs Claude 3 Haiku

| | claude-3-5-sonnet | claude-3-haiku |
|---|---|---|
| Cost Input | $3.00/1M | $0.25/1M |
| Cost Output | $15.00/1M | $1.25/1M |
| Quality | State-of-the-art | Good, fast |
| Latency | ปานกลาง | ต่ำมาก |
| Thai capability | ดีมาก | ดี |

---

## Lock-in Analysis

Anthropic Direct มี lock-in = **8/10** เพราะ:

1. **Non-OpenAI API format** — ต้องใช้ `anthropic` SDK เฉพาะ
2. **System prompt format แตกต่าง** — ต้องแก้ code ถ้า migrate
3. **Response structure แตกต่าง** — `msg.content[0].text` vs `resp.choices[0].message.content`
4. **Token field names แตกต่าง** — `input_tokens` vs `prompt_tokens`

> ถ้าต้องการ Claude แต่ lock-in ต่ำกว่า — ใช้ OpenRouter ซึ่งรองรับ `anthropic/claude-3.5-sonnet-20241022` ผ่าน OpenAI-compatible API

---

## ทำไม Lock-in ของ Anthropic Direct = 8 แต่ OpenRouter Claude = 3?

```
Anthropic Direct:
  code → anthropic SDK → api.anthropic.com → Claude

OpenRouter (Claude):
  code → openai SDK → openrouter.ai → Anthropic → Claude
         ↑
    OpenAI-compatible, เปลี่ยน model string เท่านั้น
```

OpenRouter เป็น adapter layer ที่ทำให้เปลี่ยน model ง่ายโดยไม่เปลี่ยน SDK

---

## Reliability & Privacy

| Metric | ค่า |
|--------|-----|
| Static reliability score | 0.90 (90%) |
| Privacy score | 0.4 (ข้อมูลออกไปที่ Anthropic) |
| Ease of switching | 0.3 (ยากที่สุดเพราะ API format แตกต่าง) |
