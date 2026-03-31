# Phase 1: Vector Database Comparison

## คืออะไร?

**Vector Database** คือฐานข้อมูลที่ออกแบบมาเพื่อจัดเก็บและค้นหา "vector embeddings" — ตัวเลขหลายมิติที่แทนความหมายของข้อความหรือเนื้อหา

ในระบบ RAG, Vector DB คือ "ห้องสมุด" ที่เก็บเอกสารทั้งหมดในรูป vector แล้วเมื่อผู้ใช้ถามคำถาม ระบบจะแปลงคำถามเป็น vector แล้วค้นหาเอกสารที่ "ใกล้เคียง" ที่สุด

```
คำถามผู้ใช้
     │
     ▼
[Embedding Model]  →  query vector [0.12, -0.87, 0.34, ...]
     │
     ▼
[Vector DB]  →  หา top-K vectors ที่ใกล้เคียงที่สุด
     │
     ▼
เอกสารที่เกี่ยวข้องที่สุด (context สำหรับ LLM)
```

---

## ทำไมต้องเปรียบเทียบ?

Vector DB แต่ละตัวมี trade-off ต่างกัน:
- **Performance** — QPS, latency ที่ scale ใหญ่
- **Operational complexity** — ยากแค่ไหนในการดูแล production
- **Cost** — ทั้ง infrastructure cost และ managed service pricing
- **Features** — hybrid search, metadata filtering, multi-vector

---

## ตัวเลือกที่ทดสอบ

| Vector DB | ประเภท | License | จุดเด่น |
|-----------|--------|---------|--------|
| **Qdrant** | Purpose-built | Apache 2.0 | Rust-based, filtering ดี, Rust performance |
| **pgvector** | PostgreSQL extension | PostgreSQL | ใช้ร่วม Postgres ที่มีอยู่, simple setup |
| **Milvus** | Purpose-built | Apache 2.0 | Large-scale, mature, Zilliz managed option |
| **OpenSearch** | Search + Vector | Apache 2.0 | Hybrid search (text+vector), AWS managed |

---

## โครงสร้างโค้ด

```
benchmarks/vector-db/
├── run_benchmark.py          ← script หลัก — รัน benchmark ทุก DB
├── clients/
│   ├── base.py               ← abstract interface (VectorDBClient)
│   ├── qdrant.py             ← Qdrant adapter
│   ├── pgvector.py           ← pgvector adapter
│   ├── milvus.py             ← Milvus adapter
│   └── opensearch.py         ← OpenSearch adapter
├── utils/
│   ├── dataset.py            ← สร้าง/โหลด test dataset
│   └── metrics.py            ← คำนวณ benchmark metrics
├── results/                  ← ผลลัพธ์ JSON (gitignored ยกเว้น .gitkeep)
└── requirements.txt
```

### หลักการออกแบบ (Anti-Lock-in)

`clients/base.py` กำหนด interface กลาง — ทุก adapter ต้อง implement method เดียวกัน:
```python
class VectorDBClient(ABC):
    def connect(self): ...
    def insert(self, vectors, metadata): ...
    def search(self, query_vector, top_k, filters): ...
    def delete_collection(self): ...
```

การออกแบบนี้พิสูจน์ว่า **swap Vector DB ได้โดยแก้แค่ config** — business logic ไม่ต้องรู้ว่าใช้ DB อะไร

---

## สิ่งที่วัด (Metrics)

| Metric | ความหมาย | หน่วย |
|--------|---------|------|
| **Indexing throughput** | ความเร็วในการ insert vectors | docs/sec |
| **Query latency p50** | latency ปกติ (median) | ms |
| **Query latency p95** | latency ที่ 95th percentile | ms |
| **Query latency p99** | latency ที่ worst case | ms |
| **Recall@10** | ความแม่นยำของ retrieval | % (0-100) |
| **Memory usage** | RAM ที่ใช้ | MB |
| **Disk usage** | Storage ที่ใช้ | MB |

---

## วิธีใช้งาน

### ข้อกำหนดเบื้องต้น
- Docker (สำหรับรัน Vector DB containers)
- ไม่ต้องการ API key ใดๆ

### Step 1: เริ่ม Vector DBs

```bash
# เริ่มทุก DB พร้อมกัน
make up-db

# หรือเริ่มทีละตัว
make up-db DB=qdrant
make up-db DB=pgvector
make up-db DB=milvus
make up-db DB=opensearch

# ตรวจสอบสถานะ
make ps-db

# ดู logs
make logs-db           # ทุก DB
make logs-db DB=qdrant # DB เดียว
```

### Step 2: ติดตั้ง dependencies

```bash
make install
# หรือ: uv sync --group bench-vectordb
```

### Step 3: รัน Benchmark

```bash
# Quick benchmark — 10,000 vectors (~5-10 นาที)
make benchmark-quick

# Medium benchmark — 100,000 vectors (~30-60 นาที)
make benchmark-medium

# รันทั้งสองขนาด
make benchmark-all

# รัน DB เดียว กำหนดขนาดเอง
make benchmark-db DB=qdrant N=50000
```

### Step 4: ดูผลลัพธ์

ผลลัพธ์จะถูกเขียนเป็นไฟล์ JSON ใน `benchmarks/vector-db/results/`

```bash
ls benchmarks/vector-db/results/
# qdrant_10k_results.json
# pgvector_10k_results.json
# milvus_10k_results.json
# opensearch_10k_results.json
```

### Step 5: หยุด Vector DBs

```bash
make down-db    # หยุดและลบ volumes ทั้งหมด
```

---

## ผลลัพธ์ที่ได้ (Output)

1. **JSON result files** — ข้อมูล benchmark ดิบแต่ละ DB
2. **Comparison table** — ตารางเปรียบเทียบ score ตาม criteria (กรอกใน plan.md)
3. **Recommendation** — คำแนะนำ Vector DB ที่เหมาะสม พร้อมเหตุผล

---

## คำถามที่ต้องตอบได้หลัง Phase 1

1. ถ้า data ไม่เกิน 1M vectors — pgvector พอหรือไม่?
2. ถ้าต้องการ hybrid search — OpenSearch มี advantage มากแค่ไหน?
3. Operational complexity — ทีมพร้อมดูแล dedicated vector DB ไหม หรือควรใช้ managed service?
4. Cost ที่ scale ต่างกัน (10K / 100K / 1M vectors) แตกต่างกันอย่างไร?
