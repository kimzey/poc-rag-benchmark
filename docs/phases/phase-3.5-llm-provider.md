# Phase 3.5: LLM Provider Comparison

## คืออะไร?

**LLM Provider** คือ service หรือ model ที่ทำหน้าที่ "สมอง" ของระบบ RAG — รับ context (เอกสารที่ retrieve มา) + คำถามผู้ใช้ แล้วสร้างคำตอบ

```
[Context จาก Vector DB] + [คำถามผู้ใช้]
                │
                ▼
           [LLM Provider]
                │
                ▼
         คำตอบที่สมบูรณ์
```

Phase นี้เปรียบเทียบ LLM providers หลายตัวทั้งในแง่ **คุณภาพ**, **ความเร็ว**, และ **ราคา**

---

## ทำไมต้องเปรียบเทียบ?

- LLM providers มีความต่างกันมากในแง่ cost/quality trade-off
- **OpenRouter** ช่วยลด lock-in ด้วยการเป็น unified API gateway สำหรับหลาย providers
- ต้องการ fallback strategy ในกรณีที่ provider หนึ่งล่ม
- บางงาน model เล็กพอเพียง ไม่ต้องใช้ model ใหญ่ราคาแพง

---

## ตัวเลือกที่ทดสอบ

| Provider | Model ตัวอย่าง | ราคา | หมายเหตุ |
|---------|--------------|------|--------|
| **OpenRouter** | gpt-4o-mini, claude-3-haiku | ตามจริง | Unified gateway — เปลี่ยน model ได้ง่าย |
| **OpenAI Direct** | gpt-4o, gpt-4o-mini | ตามจริง | Direct API, เสถียร |
| **Anthropic Direct** | claude-3-haiku, claude-3-sonnet | ตามจริง | Direct API, คุณภาพสูง |
| **Ollama** | llama3, mistral | ฟรี (local) | รันบนเครื่องตัวเอง, ไม่มี cost |

---

## โครงสร้างโค้ด

```
benchmarks/llm-provider/
├── evaluate.py               ← script หลัก
├── base.py                   ← abstract interface (LLMClient)
├── config.py                 ← configuration (prompts, models)
├── providers/
│   ├── openrouter.py         ← OpenRouter adapter (OpenAI-compatible API)
│   ├── openai_direct.py      ← OpenAI direct adapter
│   ├── anthropic_direct.py   ← Anthropic direct adapter
│   └── ollama.py             ← Ollama local adapter
└── requirements.txt
```

### หลักการออกแบบ (Anti-Lock-in)

ทุก provider implement interface เดียวกัน:
```python
class LLMClient(ABC):
    def complete(self, messages: list, context: str) -> LLMResponse: ...
```

**OpenRouter** เป็นตัวอย่างของการลด lock-in — ใช้ OpenAI-compatible API แต่เปลี่ยน model ได้แค่เปลี่ยน string เดียว (`openai/gpt-4o-mini` → `anthropic/claude-3-haiku`)

---

## สิ่งที่วัด (Metrics)

| Metric | ความหมาย |
|--------|---------|
| **Response latency** | เวลาตอบ (Time to First Token + Total) |
| **Answer quality** | ความถูกต้องและความสมบูรณ์ของคำตอบ |
| **Cost per query** | ค่าใช้จ่ายต่อ 1 คำถาม (input + output tokens) |
| **Thai language quality** | คุณภาพตอบคำถามภาษาไทย |
| **Context utilization** | ใช้ข้อมูลจาก context ได้ถูกต้องแค่ไหน |

---

## วิธีใช้งาน

### ข้อกำหนดเบื้องต้น

| Provider | API Key ที่ต้องการ |
|---------|-----------------|
| OpenRouter | `OPENROUTER_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Ollama | ไม่ต้องการ (local) — ต้องติดตั้ง Ollama ก่อน |

### Step 1: ติดตั้ง dependencies

```bash
make install-llm
# หรือ: uv sync --group bench-llm
```

### Step 2: กรอก API Keys

```bash
# .env
OPENROUTER_API_KEY=sk-or-...
# OPENAI_API_KEY=sk-...         # optional
# ANTHROPIC_API_KEY=sk-ant-...  # optional
```

### Step 3: รัน Evaluation

```bash
# รัน default provider (openrouter + gpt-4o-mini)
make llm-eval

# รันทุก providers ที่มี API key กรอกไว้
make llm-eval-all

# รัน provider เดียว
make llm-eval-provider P=openrouter
make llm-eval-provider P=openai
make llm-eval-provider P=anthropic
make llm-eval-provider P=ollama

# ปรับ top-k context documents
make llm-eval-topk K=5
```

### Ollama (Local Model)

```bash
# ติดตั้ง Ollama ก่อน: https://ollama.ai
ollama pull llama3.2
ollama pull mistral

# แล้วรัน evaluation
make llm-eval-provider P=ollama
```

---

## ผลลัพธ์ที่ได้ (Output)

1. **Latency comparison** — response time แต่ละ provider
2. **Quality scores** — คุณภาพคำตอบ (manual evaluation + LLM-as-judge)
3. **Cost analysis** — ค่าใช้จ่ายต่อ query แต่ละ provider
4. **Thai language quality** — เปรียบเทียบคุณภาพภาษาไทย
5. **Recommendation** — provider + model ที่แนะนำสำหรับ production

---

## OpenRouter คืออะไร?

OpenRouter เป็น **API aggregator** — ให้ access หลาย LLM providers ผ่าน OpenAI-compatible endpoint เดียว

```
Code ของเรา  →  OpenRouter API  →  OpenAI / Anthropic / Google / etc.
```

ข้อดี:
- เปลี่ยน model ได้แค่เปลี่ยน string — ไม่ต้องแก้ code
- Fallback อัตโนมัติถ้า provider หนึ่งล่ม
- Compare cost ระหว่าง models ได้ง่าย
- ใช้ OpenAI SDK เดิม — ไม่ต้องเรียน API ใหม่

---

## คำถามที่ต้องตอบได้หลัง Phase 3.5

1. OpenRouter vs Direct API — latency ต่างกันมากแค่ไหน? (overhead ของ proxy)
2. GPT-4o-mini vs Claude-3-haiku — quality/cost trade-off ในภาษาไทย
3. Ollama local model พอสำหรับ use case เราไหม? (ลด cost ได้เยอะ)
4. Context window ที่ต้องการเป็นเท่าไหร่? (ส่งผลต่อ model selection)
