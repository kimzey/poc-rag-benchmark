# Phase 3.5 — LLM Provider Benchmark

## ภาพรวม

Phase 3.5 เปรียบเทียบ LLM provider/model 11 ชุด ได้แก่ **OpenRouter** (6 models), **OpenAI Direct** (2 models), **Anthropic Direct** (2 models), และ **Ollama** (self-hosted) โดยวัด RAG answer quality (token-overlap F1), cost, latency, และ vendor lock-in

---

## โครงสร้างโฟลเดอร์

```
benchmarks/llm-provider/
├── base.py              # Abstract base class (BaseLLMProvider)
├── config.py            # Configuration + prompts
├── evaluate.py          # Evaluation runner + TF-IDF retrieval
├── providers/
│   ├── openrouter.py    # OpenRouter gateway (6 models)
│   ├── openai_direct.py # OpenAI Direct API (2 models)
│   ├── anthropic_direct.py  # Anthropic Direct API (2 models)
│   └── ollama.py        # Self-hosted Ollama
├── results/             # ผลลัพธ์ JSON
├── openrouter/          # เอกสาร OpenRouter
├── openai/              # เอกสาร OpenAI Direct
├── anthropic/           # เอกสาร Anthropic Direct
└── ollama/              # เอกสาย Ollama
```

---

## Design Pattern: Abstract Base Class

```python
class BaseLLMProvider(ABC):
    @property
    def meta(self) -> ProviderMeta: ...
    # คืนค่า metadata: name, model_id, provider, costs, lock_in

    def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]: ...
    # subclass override → (answer_text, input_tokens, output_tokens)
    # raise EnvironmentError ถ้า API key หายหรือ service ไม่พร้อม

    def generate(self, prompt: str, context: str) -> GenerateResult:
    # public method — วัด latency + คำนวณ cost อัตโนมัติ
```

### Data Structures

```python
@dataclass
class GenerateResult:
    text: str            # คำตอบที่ generate
    latency_ms: float    # wall time ทั้งหมด
    input_tokens: int    # จำนวน prompt tokens
    output_tokens: int   # จำนวน completion tokens
    cost_usd: float      # ราคาโดยประมาณ (USD)

@dataclass
class ProviderMeta:
    name: str
    model_id: str
    provider: str        # "openrouter" | "openai" | "anthropic" | "ollama"
    cost_per_1m_input: float
    cost_per_1m_output: float
    vendor_lock_in: int  # 0 = fully open, 10 = hard lock-in
    self_hostable: bool
    openai_compatible: bool  # ใช้ OpenAI-compatible API ได้
```

---

## รายการ Provider/Model

### OpenRouter (via gateway)

| Model | Input $/1M | Output $/1M | Lock-in |
|-------|-----------|------------|---------|
| claude-3.5-sonnet | $3.00 | $15.00 | 3 |
| gpt-4o | $2.50 | $10.00 | 3 |
| gpt-4o-mini | $0.15 | $0.60 | 3 |
| gemini-2.0-flash | $0.10 | $0.40 | 2 |
| llama-3.1-70b | $0.35 | $0.40 | 0 (open-weight) |
| deepseek-chat | $0.14 | $0.28 | 1 |

### OpenAI Direct

| Model | Input $/1M | Output $/1M | Lock-in |
|-------|-----------|------------|---------|
| gpt-4o | $2.50 | $10.00 | 8 |
| gpt-4o-mini | $0.15 | $0.60 | 8 |

### Anthropic Direct

| Model | Input $/1M | Output $/1M | Lock-in |
|-------|-----------|------------|---------|
| claude-3-5-sonnet | $3.00 | $15.00 | 8 |
| claude-3-haiku | $0.25 | $1.25 | 8 |

### Ollama (self-hosted)

| Model | Cost | Lock-in | Self-hosted |
|-------|------|---------|------------|
| llama3.1:8b (default) | $0 | 0 | ✅ |

---

## TF-IDF Retrieval (ไม่ต้องใช้ GPU)

evaluate.py ใช้ TF-IDF แทน neural embedding สำหรับ retrieval:

```
_tokenize()     → regex-based, รองรับ Thai + English
_build_tfidf()  → คำนวณ TF ต่อ chunk, IDF ระดับ corpus
_tfidf_score()  → sum(TF × IDF) สำหรับ query tokens
_retrieve()     → sort by score → top-k chunks
```

**ข้อดี:** ไม่ต้องใช้ GPU, ไม่มี dependency หนัก, รันได้บน CI/CD

---

## Answer Quality: Token-overlap F1

```python
def _f1_score(prediction, reference):
    # tokenize ทั้งสอง
    # precision = common / predicted
    # recall    = common / reference
    # F1 = 2 * P * R / (P + R)
```

- Language-agnostic (ใช้ได้ทั้ง Thai + English)
- ไม่ต้องใช้ semantic similarity

---

## Scoring Weights

| มิติ | น้ำหนัก | วิธีวัด |
|-----|---------|--------|
| Overall Quality (F1) | 20% | token-overlap F1 เทียบ expected answer |
| Vendor Lock-in (ต่ำ=ดี) | 20% | meta.vendor_lock_in |
| Cost | 15% | blended input/output cost |
| Latency | 15% | avg latency ms |
| Thai Quality (F1) | 10% | F1 เฉพาะ Thai questions |
| Reliability | 10% | static score ตาม provider type |
| Privacy | 5% | ollama=1.0, openrouter=0.5, direct=0.4 |
| Ease of Switching | 5% | openrouter=1.0, ollama=0.8, direct=0.3-0.4 |

---

## วิธีรัน

```bash
# รัน default (openrouter gpt-4o-mini)
make llm-eval
# หรือ
python evaluate.py

# รันทุก provider
python evaluate.py --providers all

# เลือก provider เฉพาะ
python evaluate.py --providers openrouter_gpt4o_mini ollama

# เปรียบเทียบ OpenRouter models
python evaluate.py --providers openrouter_gpt4o_mini openrouter_claude_sonnet openrouter_gemini_flash
```

---

## Static Scores

| Provider type | Reliability | Privacy | Ease of Switch |
|--------------|------------|---------|---------------|
| ollama | 70% | 100% | 80% |
| openrouter | 85% | 50% | 100% |
| openai | 90% | 40% | 40% |
| anthropic | 90% | 40% | 30% |

---

## เอกสารแต่ละ Provider

- [OpenRouter](openrouter/README.md)
- [OpenAI Direct](openai/README.md)
- [Anthropic Direct](anthropic/README.md)
- [Ollama](ollama/README.md)
