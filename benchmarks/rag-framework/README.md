# Phase 2 — RAG Framework Benchmark

## ภาพรวม

Phase 2 เปรียบเทียบ RAG framework 4 แบบ ได้แก่ **Bare Metal**, **LlamaIndex**, **LangChain**, และ **Haystack** โดยวัด indexing speed, query latency, ความซับซ้อนของ code (LOC), และความง่ายในการสลับ component

---

## โครงสร้างโฟลเดอร์

```
benchmarks/rag-framework/
├── base.py              # Abstract base class (BaseRAGPipeline)
├── config.py            # Configuration (model, chunking, API keys)
├── evaluate.py          # Evaluation runner หลัก
├── frameworks/
│   ├── bare_metal/
│   │   └── pipeline.py  # Hand-rolled RAG (numpy + OpenRouter)
│   ├── llamaindex_poc/
│   │   └── pipeline.py  # LlamaIndex pipeline
│   ├── langchain_poc/
│   │   └── pipeline.py  # LangChain pipeline
│   └── haystack_poc/
│       └── pipeline.py  # Haystack v2 pipeline
├── results/             # ผลลัพธ์ JSON
├── bare_metal/          # เอกสารอธิบาย Bare Metal
├── llamaindex/          # เอกสารอธิบาย LlamaIndex
├── langchain/           # เอกสารอธิบาย LangChain
└── haystack/            # เอกสารอธิบาย Haystack
```

---

## Design Pattern: Abstract Base Class

ทุก framework ต้อง implement `BaseRAGPipeline` (ABC) จาก `base.py`:

```python
class BaseRAGPipeline(ABC):
    def build_index(doc_paths: list[str]) -> IndexStats
    # โหลดเอกสาร → chunk → embed → สร้าง index

    def query(question: str, top_k: int) -> RAGResult
    # embed query → retrieve → generate answer

    @property
    def loc() -> int
    # นับ non-blank lines ใน pipeline.py (วัดความซับซ้อน)
```

### Data Structures

```python
@dataclass
class IndexStats:
    num_chunks: int        # จำนวน chunk ที่สร้าง
    indexing_time_ms: float
    framework: str

@dataclass
class RAGResult:
    answer: str            # คำตอบจาก LLM
    sources: list[str]     # path ของเอกสารที่ดึงมา
    latency_ms: float      # เวลาทั้งหมด (embed + retrieve + generate)
    retrieved_chunks: list[str]  # text ของ chunk ที่ดึงมา
```

---

## RAG Pipeline Flow

```
เอกสาร (hr_policy_th.md, tech_docs_en.md, faq_mixed.md)
    ↓
[Chunking]  → แบ่งข้อความเป็น chunks ขนาด 500 คำ, overlap 50 คำ
    ↓
[Embedding] → แปลง chunk เป็น dense vector
    ↓
[Index]     → เก็บ vector ใน vector store (numpy / FAISS / Haystack InMemory)
    ↓ (query time)
[Query Embed] → แปลง question เป็น vector
    ↓
[Retrieve]  → หา top-k chunks ที่ใกล้เคียงที่สุด (cosine similarity)
    ↓
[Generate]  → ส่ง context + question ให้ LLM → ได้คำตอบ
```

---

## Configuration (`config.py`)

| ตัวแปร | ค่า default | คำอธิบาย |
|--------|------------|---------|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | embedding model (sentence-transformers หรือ OpenAI) |
| `LLM_MODEL` | `openai/gpt-4o-mini` | LLM ผ่าน OpenRouter |
| `CHUNK_SIZE` | `500` | ขนาด chunk (คำ) |
| `CHUNK_OVERLAP` | `50` | overlap ระหว่าง chunk |
| `TOP_K` | `3` | จำนวน chunk ที่ retrieve |
| `OPENROUTER_API_KEY` | `.env` | API key สำหรับ LLM |
| `OPENAI_API_KEY` | `.env` | API key สำหรับ OpenAI embedding (optional) |

---

## Evaluation Runner (`evaluate.py`)

### ขั้นตอนการทำงาน

```
1. โหลดเอกสาร 3 ชุด: hr_policy_th.md, tech_docs_en.md, faq_mixed.md
2. สำหรับแต่ละ framework:
   a. build_index(doc_paths) → บันทึก IndexStats
   b. query(question) สำหรับทุก question → บันทึก RAGResult + latency
3. แสดงตาราง Rich:
   - Indexing stats (chunks, time)
   - Query latency (min/avg/max/p95)
   - Component swap-ability assessment
4. บันทึกผลเป็น JSON ใน results/
```

### วิธีรัน

```bash
# ต้องมี OPENROUTER_API_KEY ใน .env
make rag-eval
# หรือ
python evaluate.py

# เลือก framework เฉพาะ
python evaluate.py --frameworks bare_metal langchain

# ทดสอบเฉพาะ retrieval (ไม่เรียก LLM)
python evaluate.py --no-llm

# เลือก question เฉพาะข้อ
python evaluate.py --questions 1 2 3
```

---

## Metrics ที่วัด

| Metric | คำอธิบาย |
|--------|----------|
| **num_chunks** | จำนวน chunk ที่ index ได้ |
| **indexing_time_ms** | เวลา build index (ms) |
| **query latency min/avg/max/p95** | latency ของ query (ms) |
| **LOC** | จำนวน non-blank lines ใน pipeline.py |
| **Swap-ability** | ความง่ายในการเปลี่ยน component (manual assessment) |

---

## สรุปเปรียบเทียบ Framework

| Framework | LOC (approx) | Swap-ability | จุดเด่น | จุดด้อย |
|-----------|-------------|-------------|---------|---------|
| bare_metal | ~130 | Full control | ควบคุมได้ทุกขั้นตอน | ต้องเขียน code เอง |
| llamaindex | ~105 | Settings-based | boilerplate น้อย | Global state, debug ยาก |
| langchain | ~125 | LCEL composable | composable, ecosystem ใหญ่ | Legacy chain API |
| haystack | ~175 | Component DAG | type-safe, explicit wiring | verbose, learning curve |

---

## เอกสารแต่ละ Framework

- [Bare Metal](frameworks/bare_metal/README.md)
- [LlamaIndex](frameworks/llamaindex_poc/README.md)
- [LangChain](frameworks/langchain_poc/README.md)
- [Haystack](frameworks/haystack_poc/README.md)
