# Phase 2: RAG Framework Comparison

## คืออะไร?

**RAG Framework** คือชุด library/tools ที่ช่วย orchestrate pipeline ของ RAG ระบบ — ตั้งแต่การ load เอกสาร, chunking, embedding, retrieval จนถึงการส่งให้ LLM ตอบ

Phase นี้เปรียบเทียบสองแนวทางหลัก:
- **ใช้ Framework สำเร็จรูป** — LlamaIndex, LangChain, Haystack
- **Build from Scratch (Bare Metal)** — เขียนเอง ใช้แค่ libraries ที่จำเป็น

---

## ทำไมต้องเปรียบเทียบ?

การเลือก "build vs buy" สำหรับ RAG framework มีผลต่อ:
- **Flexibility** — แก้ไข/ปรับ pipeline ได้มากแค่ไหน
- **Abstraction overhead** — framework ซ่อน complexity แต่อาจซ่อนปัญหาด้วย
- **Vendor lock-in** — ถ้าใช้ framework แล้วต้องเปลี่ยน จะยากแค่ไหน
- **Learning curve** — ทีม maintain code ได้หรือเปล่า

---

## ตัวเลือกที่ทดสอบ

| Framework | ประเภท | License | จุดเด่น |
|-----------|--------|---------|--------|
| **LlamaIndex** | RAG-focused framework | MIT | Data indexing ดี, retrieval หลากหลาย |
| **LangChain** | General-purpose LLM framework | MIT | Ecosystem ใหญ่ที่สุด, chains & agents |
| **Haystack** | Production-focused pipeline | Apache 2.0 | Pipeline-based, Deepset, production-ready |
| **Bare Metal** | Custom implementation | — | Full control, ไม่มี abstraction overhead |

---

## โครงสร้างโค้ด

```
benchmarks/rag-framework/
├── evaluate.py               ← script หลัก — รัน evaluation ทุก framework
├── base.py                   ← abstract interface (RAGPipeline)
├── config.py                 ← configuration (dataset, models, metrics)
├── frameworks/
│   ├── llamaindex_poc/
│   │   └── pipeline.py       ← LlamaIndex implementation
│   ├── langchain_poc/
│   │   └── pipeline.py       ← LangChain implementation
│   ├── haystack_poc/
│   │   └── pipeline.py       ← Haystack implementation
│   └── bare_metal/
│       └── pipeline.py       ← Custom implementation (no framework)
└── results/                  ← ผลลัพธ์ JSON
```

### หลักการออกแบบ (Anti-Lock-in)

ทุก framework implement `RAGPipeline` interface เดียวกัน:
```python
class RAGPipeline(ABC):
    def index_documents(self, documents): ...
    def query(self, question: str) -> RAGResponse: ...
```

ทำให้ **เปรียบเทียบได้อย่างยุติธรรม** และพิสูจน์ว่า swap framework ได้โดยไม่แก้ application code

---

## สิ่งที่วัด (Metrics)

| Metric | ความหมาย |
|--------|---------|
| **Indexing time** | เวลาในการ index เอกสารชุดทดสอบ |
| **Query latency** | เวลาตอบคำถาม (p50, p95) |
| **Answer quality** | คุณภาพคำตอบ (ประเมิน manually หรือ LLM-as-judge) |
| **Code complexity** | จำนวนบรรทัด, ความยากในการ maintain |
| **Flexibility** | ความง่ายในการปรับ pipeline |
| **Dependency size** | ขนาด library (~2GB สำหรับ framework, ~50MB สำหรับ bare metal) |

---

## วิธีใช้งาน

### ข้อกำหนดเบื้องต้น
- OPENROUTER_API_KEY ใน `.env` (สำหรับ LLM responses)
- ถ้าไม่มี API key — รัน `--no-llm` เพื่อทดสอบแค่ indexing/retrieval

> ⚠️ `make install-rag` จะ download ~2GB (torch + LlamaIndex + LangChain + Haystack)

### Step 1: ติดตั้ง dependencies

```bash
make install-rag
# หรือ: uv sync --group bench-rag
# คาดว่าใช้เวลา 5-15 นาที (download ~2GB)
```

### Step 2: กรอก API Key (ถ้ามี)

```bash
# .env
OPENROUTER_API_KEY=sk-or-...
RAG_LLM_MODEL=openai/gpt-4o-mini   # default model
```

### Step 3: รัน Evaluation

```bash
# รันทุก 4 frameworks (ต้องการ API key)
make rag-eval

# รันโดยไม่ใช้ LLM — ทดสอบแค่ indexing + retrieval
make rag-eval-no-llm

# รัน framework เดียว
make rag-eval-framework F=llamaindex
make rag-eval-framework F=langchain
make rag-eval-framework F=haystack
make rag-eval-framework F=bare_metal
```

### Step 4: ดูผลลัพธ์

```bash
ls benchmarks/rag-framework/results/
# llamaindex_results.json
# langchain_results.json
# haystack_results.json
# bare_metal_results.json
```

---

## ผลลัพธ์ที่ได้ (Output)

1. **JSON result files** — latency, answer quality per framework
2. **Code complexity analysis** — เปรียบเทียบจำนวนบรรทัดและความซับซ้อน
3. **Recommendation** — ควร build vs ใช้ framework + ถ้าใช้ framework ควรเลือกตัวไหน

---

## คำถามที่ต้องตอบได้หลัง Phase 2

1. Build from scratch ได้ประสิทธิภาพใกล้เคียง framework หรือเปล่า?
2. Framework ไหนที่ flexibility สูงที่สุด โดยที่ abstraction ไม่มากเกินไป?
3. LangChain ซึ่งมี ecosystem ใหญ่ที่สุด — มี vendor lock-in risk มากแค่ไหน?
4. Production readiness — framework ไหนที่ทีมเราจะ maintain ได้ในระยะยาว?
