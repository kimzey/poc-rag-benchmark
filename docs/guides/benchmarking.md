# คู่มือการรัน Benchmark & อ่านผลลัพธ์

คู่มือนี้อธิบายวิธีรัน benchmark ทุก phase แล้วตีความผลลัพธ์เพื่อเลือก component ที่เหมาะสม

---

## ภาพรวม: Benchmark ทั้ง 4 หมวด

| Phase | Benchmark | สิ่งที่วัด | ต้องการ |
|-------|-----------|----------|--------|
| 1 | Vector DB | Insert speed, query latency, recall, memory | Docker |
| 2 | RAG Framework | Indexing speed, answer quality, LOC complexity | OPENROUTER_API_KEY (optional) |
| 3 | Embedding Model | Retrieval recall, latency, cost | OPENAI_API_KEY (optional) |
| 3.5 | LLM Provider | Response quality, latency, cost/token | API keys ตาม provider |

---

## Phase 1: Vector DB Benchmark

### ข้อกำหนด

- Docker running
- ไม่ต้องการ API key

### วิธีรัน

```bash
# 1. Start Vector DBs
make up-db

# 2. ติดตั้ง deps
make install

# 3. รัน benchmark
make benchmark-quick          # 10K vectors (~5-10 นาที)
make benchmark-medium         # 100K vectors (~30-60 นาที)
make benchmark-all            # ทั้งสองขนาด

# รัน DB เดียว + กำหนดขนาด
make benchmark-db DB=qdrant N=50000

# 4. หยุด DBs เมื่อเสร็จ
make down-db
```

### ผลลัพธ์อยู่ที่ไหน

```
benchmarks/vector-db/results/
├── qdrant_10k_results.json
├── pgvector_10k_results.json
├── milvus_10k_results.json
└── opensearch_10k_results.json
```

### วิธีอ่านผลลัพธ์

| Metric | ความหมาย | ค่าที่ดี | ทำไมสำคัญ |
|--------|---------|---------|----------|
| **Insert throughput** (docs/sec) | ความเร็ว indexing | สูงกว่า = ดีกว่า | กระทบเวลา re-index ทั้ง collection |
| **Query latency p50** (ms) | latency ปกติ | < 10ms | ส่งผลต่อ UX โดยตรง |
| **Query latency p95** (ms) | latency ที่ load สูง | < 50ms | ถ้าสูง = ไม่ consistent |
| **Query latency p99** (ms) | worst case | < 100ms | tail latency ที่ต้อง monitor |
| **Recall@10** (%) | ความแม่นยำ | > 95% | ค้นเจอเอกสารที่ถูกต้องไหม |
| **Memory usage** (MB) | RAM ที่ใช้ | ต่ำกว่า = ประหยัด | กระทบ infrastructure cost |

### เปรียบเทียบอย่างไร

1. **Recall สำคัญที่สุด** — ถ้า recall ต่ำ ข้อมูลอื่นไม่มีความหมาย
2. **Latency ต้องอยู่ใน budget** — ดูที่ p95 ไม่ใช่แค่ p50
3. **Operational complexity** — ต้องดูแลง่ายแค่ไหน (Milvus ต้อง etcd + minio, pgvector แค่ Postgres)
4. **Scale** — ผล 10K อาจต่างจาก 100K มาก ดูทั้งสองขนาด

---

## Phase 2: RAG Framework Benchmark

### วิธีรัน

```bash
make install-rag

# รันทุก framework (ต้องการ OPENROUTER_API_KEY)
make rag-eval

# รัน indexing เท่านั้น (ไม่ต้องการ API key)
make rag-eval-no-llm

# รัน framework เดียว
make rag-eval-framework F=bare_metal
make rag-eval-framework F=llamaindex
make rag-eval-framework F=langchain
make rag-eval-framework F=haystack
```

### ผลลัพธ์อยู่ที่ไหน

```
benchmarks/rag-framework/results/
```

### วิธีอ่านผลลัพธ์

| Metric | ความหมาย | ทำไมสำคัญ |
|--------|---------|----------|
| **Indexing time** (ms) | เวลา build index | re-index ต้องเร็วพอ |
| **Num chunks** | จำนวน chunks ที่สร้าง | มาก = granular แต่ slow; น้อย = fast แต่อาจ miss context |
| **Query latency** (ms) | retrieve + generate | ส่งผลต่อ UX |
| **Answer quality** | ดูด้วยตาเอง | framework สร้าง prompt ต่างกัน → คำตอบต่างกัน |
| **Lines of code** | LOC ของ pipeline.py | proxy สำหรับ complexity — น้อย = maintain ง่าย |

### เปรียบเทียบอย่างไร

- **Bare Metal vs Framework** — bare metal มี LOC มากกว่า แต่ control ได้ทุกอย่าง
- **Build vs Buy** — ถ้า framework มี magic ที่ debug ยาก อาจไม่คุ้ม
- **Breaking changes** — framework ที่ release major version บ่อย = risk สูง
- **ดู output ของแต่ละ framework** — คำตอบเหมือนกันไหม? ถ้าต่างกันมาก ต้องวิเคราะห์ว่าทำไม

---

## Phase 3: Embedding Model Benchmark

### วิธีรัน

```bash
make install-embed

# Open-source models (ไม่ต้องการ API key)
make embed-eval

# ทุก models รวม OpenAI (ต้องการ OPENAI_API_KEY)
make embed-eval-all

# Model เดียว
make embed-eval-model M=bge_m3
make embed-eval-model M=multilingual_e5
make embed-eval-model M=mxbai
make embed-eval-model M=openai_large     # ต้องการ OPENAI_API_KEY
make embed-eval-model M=openai_small     # ต้องการ OPENAI_API_KEY

# Override top-k
make embed-eval-topk K=5
```

### วิธีอ่านผลลัพธ์

| Metric | ความหมาย | ทำไมสำคัญ |
|--------|---------|----------|
| **Recall@K (Thai)** | ค้นเจอเอกสารไทยที่ถูกต้องไหม | **สำคัญที่สุด** — ถ้า Thai recall ต่ำ ทุกอย่างที่ตามมาจะแย่ |
| **Recall@K (English)** | ค้นเจอเอกสาร EN ที่ถูกต้องไหม | ต้องดีด้วย ถ้า KB มีทั้ง 2 ภาษา |
| **Latency** (ms) | เวลา encode | local model อาจช้ากว่า API |
| **Dimensions** | ขนาด vector | มาก = ค้นละเอียดกว่า แต่ใช้ storage มากกว่า |
| **Cost per 1M tokens** | ค่าใช้จ่าย | $0 สำหรับ local, ~$0.02-0.13 สำหรับ OpenAI |
| **Vendor lock-in** | ผูกติดแค่ไหน | local = 0, OpenAI = สูง |

### เปรียบเทียบอย่างไร

1. **Thai recall เป็น gatekeeper** — ถ้า model ไหน Thai recall ต่ำกว่า 70% ตัดออกเลย
2. **Cost vs Quality tradeoff** — OpenAI อาจ recall สูงกว่า แต่มีค่าใช้จ่าย + lock-in
3. **Self-hosting** — open-source model ต้องมี server รัน; ถ้าไม่มี GPU อาจช้า
4. **Max token length** — ถ้าเอกสารยาว model ที่รับ token ได้มากจะได้เปรียบ

---

## Phase 3.5: LLM Provider Benchmark

### วิธีรัน

```bash
make install-llm

# Default (OpenRouter)
make llm-eval

# ทุก providers ที่มี API key
make llm-eval-all

# Provider เดียว
make llm-eval-provider P=openrouter
make llm-eval-provider P=openai
make llm-eval-provider P=anthropic

# Override top-k context
make llm-eval-topk K=5
```

### วิธีอ่านผลลัพธ์

| Metric | ความหมาย | ทำไมสำคัญ |
|--------|---------|----------|
| **Response quality** | คำตอบถูกต้อง + อ่านง่ายไหม | ต้องดูด้วยตาเอง — automated metric อาจไม่พอ |
| **Latency** (ms) | เวลาตั้งแต่ส่ง prompt ถึงได้ response | กระทบ UX โดยตรง |
| **Input tokens** | prompt tokens ที่ใช้ | ยิ่ง context ยาว ยิ่งแพง |
| **Output tokens** | completion tokens ที่สร้าง | กระทบ latency + cost |
| **Cost per call** (USD) | ค่าใช้จ่ายต่อ request | คำนวณ monthly cost ได้ |
| **Vendor lock-in** | ผูกติดแค่ไหน | OpenRouter = ต่ำ (switch model ได้ทันที) |
| **OpenAI compatible** | ใช้ OpenAI SDK ได้ไหม | ถ้า compatible = swap ง่าย |

### เปรียบเทียบอย่างไร

1. **Quality ต้องดีพอสำหรับ use case** — RAG ต้องการ model ที่ตอบจาก context ได้ดี ไม่ hallucinate
2. **Thai quality** — ไม่ใช่ทุก model ตอบภาษาไทยได้ดี
3. **Cost projection** — คำนวณว่า 10K queries/day จะเป็นเงินเท่าไหร่
4. **Reliability** — OpenRouter มี fallback ได้ vs direct API อาจล่ม

---

## Tips ทั่วไป

### รัน benchmark ซ้ำหลายรอบ

ผล benchmark ครั้งเดียวอาจไม่แม่นยำ — ถ้าเป็นไปได้ ควรรันอย่างน้อย 3 รอบแล้วดูค่าเฉลี่ย โดยเฉพาะ:
- Latency — อาจแกว่งตาม network/system load
- LLM quality — model อาจตอบต่างกันแต่ละครั้ง

### ปัจจัยที่ benchmark อาจไม่ครอบคลุม

- **Operational complexity** — ข้อมูลนี้ได้จากประสบการณ์ setup + maintain
- **Community & ecosystem** — ดูจาก GitHub stars, issue response time, documentation quality
- **Long-term viability** — company behind the project stable ไหม

### ผล benchmark ไม่ใช่คำตอบสุดท้าย

Benchmark เป็นข้อมูลประกอบการตัดสินใจ — ต้องรวมกับ:
- Team skillset
- Infrastructure ที่มีอยู่
- Budget constraints
- Timeline

ผลสุดท้ายจะถูกสรุปใน [RFC-001](../rfc/RFC-001-rag-tech-stack.md) เพื่อให้ทีมตัดสินใจร่วมกัน
