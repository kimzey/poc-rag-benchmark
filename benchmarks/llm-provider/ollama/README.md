# Ollama — Self-Hosted LLM

## คืออะไร

Ollama เป็น tool สำหรับรัน open-weight LLM บน local machine ของตัวเอง รองรับ model หลากหลาย (Llama, Mistral, Gemma, Qwen ฯลฯ) ข้อมูลทั้งหมดอยู่บน infrastructure ของตัวเอง ไม่ออกไปที่ external server และไม่มีค่า API ใดๆ

Ollama expose OpenAI-compatible endpoint ที่ `http://localhost:11434/v1` ทำให้ใช้ `openai` SDK ปกติได้

- Cost: $0 (ใช้ hardware ของตัวเอง)
- Vendor lock-in: 0 (fully open)
- Self-hostable: ✅
- OpenAI-compatible: ✅
- Default model: `llama3.1:8b`

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/llm-provider/providers/ollama.py
benchmarks/llm-provider/base.py
benchmarks/llm-provider/config.py
```

---

## โครงสร้าง Code (`providers/ollama.py`)

```python
class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_id: str | None = None) -> None:
        self._model_id = model_id or config.OLLAMA_MODEL  # default: llama3.1:8b
        self._meta = ProviderMeta(
            name=f"Ollama / {self._model_id}",
            model_id=self._model_id,
            provider="ollama",
            cost_per_1m_input=0.0,
            cost_per_1m_output=0.0,
            vendor_lock_in=0,      # fully open
            self_hostable=True,
            openai_compatible=True,
        )
```

---

## อธิบาย Code ทีละส่วน

### `_generate_raw()` — OpenAI SDK ชี้ไป Ollama local endpoint

```python
def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
    from openai import OpenAI, APIConnectionError

    # ใช้ openai SDK แต่ชี้ไป Ollama local endpoint
    client = OpenAI(
        base_url=f"{config.OLLAMA_BASE_URL}/v1",  # "http://localhost:11434/v1"
        api_key="ollama",                          # Ollama ไม่ validate key value
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

    text   = resp.choices[0].message.content or ""
    usage  = resp.usage
    # Ollama อาจไม่ส่ง token counts เสมอไป
    in_tok  = usage.prompt_tokens if usage else 0
    out_tok = usage.completion_tokens if usage else 0
    return text.strip(), in_tok, out_tok
```

**Pattern:** เหมือนกับ OpenRouter ทุกอย่าง เพียงแต่ `base_url` ชี้ไป `localhost:11434`

**Error handling:** ถ้า Ollama ไม่รันอยู่จะได้ `APIConnectionError` → แปลงเป็น `EnvironmentError` พร้อม message แนะนำวิธีแก้

---

## Config ที่เกี่ยวข้อง

```python
# ใน benchmarks/llm-provider/config.py
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
```

สามารถ override ผ่าน `.env`:
```bash
OLLAMA_BASE_URL=http://192.168.1.100:11434  # remote server
OLLAMA_MODEL=qwen2.5:7b                     # เปลี่ยน model
```

---

## วิธี Setup Ollama

```bash
# 1. Install Ollama
brew install ollama   # macOS
# หรือดู https://ollama.ai

# 2. Start Ollama server
ollama serve

# 3. Pull model
ollama pull llama3.1:8b   # ~4GB

# 4. ทดสอบ
curl http://localhost:11434/api/generate -d '{"model":"llama3.1:8b","prompt":"Hello"}'
```

---

## Models ที่แนะนำสำหรับ RAG

| Model | Size | Thai | English | VRAM |
|-------|------|------|---------|------|
| llama3.1:8b | 4.7GB | ปานกลาง | ดี | 8GB+ |
| qwen2.5:7b | 4.4GB | ดี | ดี | 8GB+ |
| llama3.1:70b | 40GB | ดี | ดีมาก | 48GB+ |
| gemma2:9b | 5.4GB | ปานกลาง | ดี | 8GB+ |

---

## Token Counts

Ollama อาจไม่ส่ง `usage` ใน response เสมอไป (ขึ้นกับ model):
```python
in_tok  = usage.prompt_tokens if usage else 0
out_tok = usage.completion_tokens if usage else 0
```

ถ้า token count = 0 จะทำให้ cost estimation = $0 (ถูกต้อง เพราะ Ollama ฟรีอยู่แล้ว)

---

## Privacy & Security

| มิติ | ค่า |
|-----|-----|
| Privacy score | **1.0** (ข้อมูลไม่ออกจาก machine เลย) |
| Reliability | 0.70 (ขึ้นกับ hardware + ไม่มี SLA) |
| Ease of switching | 0.8 (pull model ใหม่ + restart) |
| Vendor lock-in | **0** |

---

## จุดเด่น / จุดด้อย

| จุดเด่น | จุดด้อย |
|--------|---------|
| Privacy สูงสุด — ข้อมูลไม่ออก machine | ช้ากว่า cloud APIs บน CPU |
| ฟรี 100% (ไม่มีค่า API) | ต้องมี hardware เพียงพอ (VRAM) |
| Vendor lock-in = 0 | ไม่มี SLA, reliability ขึ้นกับ hardware |
| OpenAI-compatible endpoint | ต้อง manage model ด้วยตัวเอง |
| ใช้ได้ offline | Thai quality อาจต่ำกว่า cloud models |
| เปลี่ยน model ง่าย (`ollama pull`) | |
