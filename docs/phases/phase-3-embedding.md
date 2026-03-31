# Phase 3: Embedding Model Comparison

## คืออะไร?

**Embedding Model** คือ AI model ที่แปลงข้อความ (text) ให้กลายเป็น vector ตัวเลข — ตัวเลขเหล่านี้แทน "ความหมาย" ของข้อความ ข้อความที่มีความหมายใกล้กันจะได้ vector ที่ใกล้กันด้วย

```
"นโยบายลาพักร้อน"  →  [0.12, -0.87, 0.34, 0.91, ...]  (768 มิติ)
"วันหยุดประจำปี"   →  [0.11, -0.85, 0.36, 0.89, ...]  (คล้ายกัน ✓)
"ราคาอาหาร"        →  [-0.45, 0.23, -0.67, 0.12, ...]  (ต่างกันมาก ✓)
```

Embedding Model เป็น component ที่สำคัญมากใน RAG เพราะ **คุณภาพของ retrieval ขึ้นอยู่กับ embedding model โดยตรง** — ถ้า model แปลงความหมายผิด การค้นหาก็จะผิดตามไปด้วย

---

## ทำไมต้องเปรียบเทียบ?

โดยเฉพาะสำหรับ **ภาษาไทย** — ไม่ใช่ทุก model ที่รองรับได้ดี:
- OpenAI embeddings — คุณภาพสูง แต่ต้องจ่ายเงิน และ data ออกนอก
- Open-source models (BGE-M3, multilingual-E5) — ฟรี รันบน local
- Model ที่ train บนภาษาไทยโดยเฉพาะ vs multilingual general models

---

## ตัวเลือกที่ทดสอบ

| Model | ผู้พัฒนา | ขนาด | ต้องการ API? | Thai Support |
|-------|--------|------|------------|------------|
| **BGE-M3** | BAAI | ~570MB | ไม่ (local) | ดี (multilingual) |
| **multilingual-E5-large** | Microsoft | ~560MB | ไม่ (local) | ดี (94 ภาษา) |
| **mxbai-embed-large** | mixedbread | ~335MB | ไม่ (local) | ปานกลาง |
| **text-embedding-3-large** | OpenAI | — | ใช่ | ดีมาก |
| **text-embedding-3-small** | OpenAI | — | ใช่ | ดี (เร็ว+ถูก) |

---

## โครงสร้างโค้ด

```
benchmarks/embedding-model/
├── evaluate.py               ← script หลัก
├── base.py                   ← abstract interface (EmbeddingModel)
├── config.py                 ← configuration (test queries, models)
├── models/
│   ├── bge_m3.py             ← BGE-M3 adapter (local)
│   ├── multilingual_e5.py    ← multilingual-E5 adapter (local)
│   ├── mxbai.py              ← mxbai adapter (local)
│   ├── openai_large.py       ← OpenAI text-embedding-3-large adapter
│   └── openai_small.py       ← OpenAI text-embedding-3-small adapter
└── requirements.txt
```

---

## สิ่งที่วัด (Metrics)

| Metric | ความหมาย |
|--------|---------|
| **Embedding latency** | เวลาแปลงข้อความ 1 ชุด (ms) |
| **Throughput** | จำนวนข้อความที่ embed ได้ต่อวินาที |
| **Recall@K** | ความแม่นยำ — ค้นหาเจอเอกสารที่ใช่ใน top-K ไหม |
| **MRR (Mean Reciprocal Rank)** | คุณภาพการ rank ผลลัพธ์ |
| **Thai language quality** | ทดสอบด้วย Thai queries โดยเฉพาะ |
| **Cost per 1M tokens** | ค่าใช้จ่าย (สำหรับ API models) |

---

## วิธีใช้งาน

### ข้อกำหนดเบื้องต้น
- Open-source models: ไม่ต้องการ API key (แต่ต้องมี disk ~1.5GB + RAM ~4GB)
- OpenAI models: ต้องการ `OPENAI_API_KEY`

> ⚠️ Model download ครั้งแรกอาจใช้เวลา 5-15 นาที แต่จะ cache ไว้ที่ `.cache/`

### Step 1: ติดตั้ง dependencies

```bash
make install-embed
# หรือ: uv sync --group bench-embed
```

### Step 2: กรอก API Key (ถ้าต้องการ OpenAI)

```bash
# .env
OPENAI_API_KEY=sk-...
```

### Step 3: รัน Evaluation

```bash
# รัน open-source models ทั้งหมด (ไม่ต้องการ API key)
make embed-eval

# รันทุก models รวม OpenAI (ต้องการ OPENAI_API_KEY)
make embed-eval-all

# รัน model เดียว
make embed-eval-model M=bge_m3
make embed-eval-model M=multilingual_e5
make embed-eval-model M=mxbai
make embed-eval-model M=openai_large    # ต้องการ OPENAI_API_KEY
make embed-eval-model M=openai_small    # ต้องการ OPENAI_API_KEY

# ปรับ top-k
make embed-eval-topk K=5
```

### ชื่อ model ที่ใช้ได้

| ชื่อ M= | Model จริง |
|---------|-----------|
| `bge_m3` | BAAI/bge-m3 |
| `multilingual_e5` | intfloat/multilingual-e5-large |
| `mxbai` | mixedbread-ai/mxbai-embed-large-v1 |
| `openai_large` | text-embedding-3-large |
| `openai_small` | text-embedding-3-small |

---

## ผลลัพธ์ที่ได้ (Output)

1. **Recall@K scores** — แต่ละ model ดึงเอกสารที่ถูกต้องได้แม่นแค่ไหน
2. **Latency comparison** — local models vs API models
3. **Thai language benchmark** — ทดสอบ queries ภาษาไทยโดยเฉพาะ
4. **Cost analysis** — Open-source vs API (ต่อ 1M tokens)
5. **Recommendation** — model ที่เหมาะสมสำหรับ use case เรา

---

## คำถามที่ต้องตอบได้หลัง Phase 3

1. BGE-M3 (open-source) เทียบกับ OpenAI embeddings — quality ต่างกันมากแค่ไหนสำหรับภาษาไทย?
2. คุ้มไหมที่จะจ่าย OpenAI embeddings เทียบกับรันบน local?
3. latency ของ local model (CPU inference) ยอมรับได้ใน production หรือต้องการ GPU?
4. Model ไหนที่ภาษาไทย + ภาษาอังกฤษ mixed content ทำงานได้ดีที่สุด?
