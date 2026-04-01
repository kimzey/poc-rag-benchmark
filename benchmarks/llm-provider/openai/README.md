# OpenAI Direct — GPT-4o / GPT-4o-mini

## คืออะไร

OpenAI Direct provider เรียก OpenAI API โดยตรง ไม่ผ่าน gateway ใดๆ ใช้ `openai` Python SDK และ API key จาก OpenAI โดยตรง รองรับ 2 models: `gpt-4o` (flagship) และ `gpt-4o-mini` (cost-efficient)

- Provider: api.openai.com
- API: OpenAI Chat Completions
- Vendor lock-in: 8/10 (proprietary SDK + pricing + API format)
- Self-hostable: ❌
- OpenAI-compatible: ✅ (เป็นต้นฉบับ)

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/llm-provider/providers/openai_direct.py
benchmarks/llm-provider/base.py
benchmarks/llm-provider/config.py
```

---

## โครงสร้าง Code (`providers/openai_direct.py`)

```python
_MODELS = {
    "gpt-4o":      {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
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
            vendor_lock_in=8,     # proprietary SDK + API — high lock-in
            self_hostable=False,
            openai_compatible=True,  # เป็นต้นฉบับ OpenAI format
        )
```

---

## อธิบาย Code ทีละส่วน

### `_generate_raw()` — Direct OpenAI API call

```python
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
    text   = resp.choices[0].message.content or ""
    in_tok  = resp.usage.prompt_tokens
    out_tok = resp.usage.completion_tokens
    return text.strip(), in_tok, out_tok
```

ต่างจาก OpenRouter เพียงแค่ `base_url` — ไม่ต้อง override (ใช้ default `api.openai.com`)

---

## gpt-4o vs gpt-4o-mini

| | gpt-4o | gpt-4o-mini |
|---|---|---|
| Cost Input | $2.50/1M | $0.15/1M |
| Cost Output | $10.00/1M | $0.60/1M |
| Quality | Flagship | Good enough |
| Latency | ช้ากว่า | เร็วกว่า |
| Context | 128K tokens | 128K tokens |
| Use case | Quality-first | Cost-sensitive |

---

## Lock-in Analysis

OpenAI Direct มี lock-in = **8/10** เพราะ:

1. **Proprietary API format** — ถ้า OpenAI เปลี่ยน API ต้องแก้ code
2. **API key format** — ผูกกับ OpenAI account
3. **Pricing control** — ราคาขึ้นได้ตลอดเวลา
4. **Model naming** — `gpt-4o` ไม่ work กับ Anthropic API

> ถ้าต้องการ lock-in ต่ำกว่า ให้ใช้ OpenRouter แทน — ทั้ง gpt-4o และ gpt-4o-mini มีให้ใช้ผ่าน OpenRouter

---

## Reliability & SLA

| Metric | ค่า |
|--------|-----|
| Static reliability score | 0.90 (90%) |
| Privacy score | 0.4 (ข้อมูลออกไปที่ OpenAI) |
| Ease of switching | 0.4 (ต้องเปลี่ยน SDK ถ้าย้าย provider) |

---

## จุดเด่น / จุดด้อย

| จุดเด่น | จุดด้อย |
|--------|---------|
| Reliability สูง (SLA 99.9%) | Lock-in สูงสุด (8/10) |
| Latency ต่ำ (ไม่มี gateway hop) | ข้อมูลไปที่ OpenAI server |
| Quality ดีสุดในกลุ่ม OpenAI models | ราคาควบคุม OpenAI เอง |
| Documentation ดีมาก | ต้องใช้ OPENAI_API_KEY แยกต่างหาก |
