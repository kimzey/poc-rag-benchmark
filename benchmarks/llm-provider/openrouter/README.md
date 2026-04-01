# OpenRouter — Multi-Model LLM Gateway

## คืออะไร

OpenRouter เป็น API gateway ที่รวม LLM providers หลายราย (OpenAI, Anthropic, Google, Meta, DeepSeek ฯลฯ) ไว้ใน endpoint เดียวด้วย OpenAI-compatible API จุดเด่นสำคัญคือ **anti-vendor-lock-in** — เปลี่ยน model ได้ด้วยการเปลี่ยนแค่ `model` string

- Provider: openrouter.ai
- API compatibility: OpenAI-compatible (`/chat/completions`)
- Vendor lock-in: 3/10 (ต่ำกว่า direct providers)
- Models supported: 6 models ใน benchmark นี้

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/llm-provider/providers/openrouter.py
benchmarks/llm-provider/base.py
benchmarks/llm-provider/config.py
```

---

## โครงสร้าง Code (`providers/openrouter.py`)

### Class: `OpenRouterProvider`

```python
class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, model_id: str = DEFAULT_MODEL)
    @property
    def meta(self) -> ProviderMeta
    def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]
```

---

## Models Registry

```python
_MODELS = {
    "anthropic/claude-3.5-sonnet-20241022": {"input": 3.00, "output": 15.00, "lock_in": 3},
    "openai/gpt-4o":                        {"input": 2.50, "output": 10.00, "lock_in": 3},
    "openai/gpt-4o-mini":                   {"input": 0.15, "output": 0.60,  "lock_in": 3},
    "google/gemini-2.0-flash-001":          {"input": 0.10, "output": 0.40,  "lock_in": 2},
    "meta-llama/llama-3.1-70b-instruct":    {"input": 0.35, "output": 0.40,  "lock_in": 0},  # open-weight
    "deepseek/deepseek-chat":               {"input": 0.14, "output": 0.28,  "lock_in": 1},
}
DEFAULT_MODEL = "openai/gpt-4o-mini"
```

Lock-in ของ OpenRouter models ต่ำกว่า direct providers เพราะ:
- ใช้ OpenAI-compatible API เดียวกัน
- เปลี่ยน model string เท่านั้น ไม่ต้องเปลี่ยน SDK
- ถ้า OpenRouter หยุดให้บริการ code ยังใช้กับ OpenAI direct ได้เลย

---

## อธิบาย Code ทีละส่วน

### `__init__()` — Dynamic meta จาก model registry

```python
def __init__(self, model_id: str = DEFAULT_MODEL) -> None:
    if not config.OPENROUTER_API_KEY:
        raise EnvironmentError("OPENROUTER_API_KEY not set — skipping OpenRouter")

    specs = _MODELS.get(model_id, {"input": 0.0, "output": 0.0, "lock_in": 3})
    short_name = model_id.split("/")[-1]  # "openai/gpt-4o-mini" → "gpt-4o-mini"

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
```

หนึ่ง adapter class รองรับ **ทุก model ใน OpenRouter** เพียงส่ง `model_id` ต่างกัน — เป็นตัวอย่างของ anti-lock-in design

---

### `_generate_raw()` — OpenAI SDK ชี้ไป OpenRouter endpoint

```python
def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
    from openai import OpenAI

    # OpenAI SDK แต่ base_url ชี้ไป OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.OPENROUTER_API_KEY,
    )

    full_prompt = config.RAG_PROMPT_TEMPLATE.format(
        context=context, question=prompt
    )

    resp = client.chat.completions.create(
        model=self._model_id,     # "openai/gpt-4o-mini" format ของ OpenRouter
        messages=[
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user",   "content": full_prompt},
        ],
        max_tokens=config.MAX_NEW_TOKENS,
        temperature=config.TEMPERATURE,
    )

    text   = resp.choices[0].message.content or ""
    in_tok  = resp.usage.prompt_tokens if resp.usage else 0
    out_tok = resp.usage.completion_tokens if resp.usage else 0
    return text.strip(), in_tok, out_tok
```

**Key design:** ใช้ `openai.OpenAI` SDK ปกติ แค่ override `base_url` → ไม่ต้อง install SDK เพิ่ม

**Model ID format:** OpenRouter ใช้ `"provider/model"` format เช่น `"openai/gpt-4o-mini"`, `"anthropic/claude-3.5-sonnet-20241022"`

---

## RAG Prompt Template (จาก config.py)

```python
RAG_PROMPT_TEMPLATE = """\
Use the following context to answer the question.
If the answer is not in the context, say "ไม่พบข้อมูลในเอกสาร (Not found in documents)."

Context:
{context}

Question: {question}

Answer:"""

SYSTEM_PROMPT = "You are a helpful assistant that answers questions based on provided documents. Be concise and accurate."
```

---

## Provider Comparisons ใน benchmark

| Model via OpenRouter | Lock-in | $/1M in | $/1M out | Notes |
|---------------------|---------|---------|---------|-------|
| claude-3.5-sonnet | 3 | $3.00 | $15.00 | Anthropic model ผ่าน gateway |
| gpt-4o | 3 | $2.50 | $10.00 | OpenAI model ผ่าน gateway |
| gpt-4o-mini | 3 | $0.15 | $0.60 | Default, cost-efficient |
| gemini-2.0-flash | 2 | $0.10 | $0.40 | ถูกที่สุดใน quality models |
| llama-3.1-70b | 0 | $0.35 | $0.40 | Open-weight, zero lock-in |
| deepseek-chat | 1 | $0.14 | $0.28 | ถูกมาก, quality ดี |

---

## จุดเด่น / จุดด้อย

| จุดเด่น | จุดด้อย |
|--------|---------|
| เปลี่ยน model ได้ด้วย 1 string | เพิ่ม 1 hop (latency +20-50ms) |
| OpenAI-compatible — ไม่ต้องเปลี่ยน SDK | ข้อมูลผ่าน OpenRouter server |
| รองรับ model หลายร้อยตัว | Reliability ต่ำกว่า direct (85% vs 90%) |
| Fallback routing ถ้า provider หยุด | ราคาอาจแพงกว่า direct เล็กน้อย |
| Single API key สำหรับทุก provider | |
