# Phase 1 — Vector Database Benchmark

## ภาพรวม

Phase 1 เป็นการเปรียบเทียบประสิทธิภาพของ Vector Database 4 ตัว ได้แก่ **Qdrant**, **pgvector**, **Milvus**, และ **OpenSearch** โดยวัดผลด้านความเร็วในการ index, latency ในการค้นหา, การค้นหาแบบ filtered, และความแม่นยำ (Recall@10)

---

## โครงสร้างโฟลเดอร์

```
benchmarks/vector-db/
├── clients/
│   ├── base.py          # Abstract base class (VectorDBClient)
│   ├── qdrant.py        # Qdrant adapter
│   ├── pgvector.py      # PostgreSQL + pgvector adapter
│   ├── milvus.py        # Milvus adapter
│   └── opensearch.py    # OpenSearch adapter
├── utils/
│   ├── dataset.py       # สร้าง synthetic dataset และ ground truth
│   └── metrics.py       # วัด latency, recall, บันทึกผล
├── run_benchmark.py     # Script หลักสำหรับรัน benchmark
├── results/             # ผลลัพธ์ JSON (สร้างอัตโนมัติ)
├── qdrant/              # เอกสารอธิบาย Qdrant
├── pgvector/            # เอกสารอธิบาย pgvector
├── milvus/              # เอกสารอธิบาย Milvus
└── opensearch/          # เอกสารอธิบาย OpenSearch
```

---

## Design Pattern: Abstract Base Class

ทุก DB adapter ต้อง implement `VectorDBClient` (ABC) จาก `clients/base.py`:

```python
class VectorDBClient(ABC):
    DIM = 1536  # มิติของ vector (ตาม OpenAI text-embedding-3-small)

    def connect()            # เชื่อมต่อ DB
    def create_collection()  # สร้าง collection/index
    def insert()             # แทรก vector แบบ batch
    def search()             # ค้นหา ANN + optional metadata filter
    def count()              # นับจำนวน vector
    def drop_collection()    # ลบ collection
```

Pattern นี้ทำให้สามารถสลับ DB ได้โดยไม่ต้องแก้ไข benchmark runner

---

## Data Structures

### `BenchmarkRecord`
```python
@dataclass
class BenchmarkRecord:
    id: str
    vector: list[float]      # 1536-dim float vector
    metadata: dict           # access_level, category, source
```

### `SearchResult`
```python
@dataclass
class SearchResult:
    id: str
    score: float             # cosine similarity score
    metadata: dict
```

---

## Benchmark Runner (`run_benchmark.py`)

### ขั้นตอนการทำงาน

```
1. สร้าง dataset: N vectors (default 10,000) + metadata (access_level, category)
2. สร้าง brute-force ground truth สำหรับคำนวณ Recall@10
3. สำหรับแต่ละ DB:
   a. connect() → create_collection() → insert() → วัด indexing time
   b. รัน 100 ANN queries → วัด latency (p50/p95/p99/QPS)
   c. รัน 50 filtered queries (filter: access_level="internal")
   d. คำนวณ Recall@10 เทียบกับ ground truth
   e. drop_collection() (cleanup)
4. แสดงตารางสรุปด้วย Rich console
5. บันทึกผลเป็น JSON ใน results/
```

### วิธีรัน

```bash
# Docker services ต้องรันก่อน
make up-db

# รันทุก DB, 10K vectors
make benchmark-quick
# หรือ
python run_benchmark.py

# รันเฉพาะ DB เดียว
python run_benchmark.py --db qdrant

# ข้าม DB บางตัว
python run_benchmark.py --skip milvus opensearch

# ปรับขนาด dataset
python run_benchmark.py --n 50000

# ดูรายการ DB
python run_benchmark.py --list
```

---

## Metrics ที่วัด

| Metric | คำอธิบาย |
|--------|----------|
| **Index time (s)** | เวลาทั้งหมดในการ insert + build index |
| **Throughput (vec/s)** | จำนวน vector ที่ insert ได้ต่อวินาที |
| **Search p50/p95/p99 (ms)** | Latency percentiles สำหรับ ANN search |
| **Search QPS** | Query per second |
| **Filter p95 (ms)** | Latency ของ metadata-filtered search |
| **Recall@10** | สัดส่วน true neighbors ที่หาพบใน top-10 |

---

## Dataset (`utils/dataset.py`)

- `generate_dataset(n, dim=1536)` — สร้าง n random unit vectors พร้อม metadata
  - `access_level`: random จาก `["public", "internal", "confidential"]`
  - `category`: random จาก `["tech", "hr", "finance", "ops"]`
- `generate_queries(n)` — สร้าง random query vectors
- `compute_ground_truth(dataset, queries, top_k)` — คำนวณ exact kNN ด้วย numpy (O(N×Q) brute-force)

> ground truth คำนวณเฉพาะ dataset ≤ 50,000 vectors เพราะ brute-force ใช้เวลานาน

---

## Infrastructure (Docker)

Vector DB services ทั้ง 4 ตัวรันใน Docker ผ่าน `docker/docker-compose.vector-db.yml`:

| DB | Port | Notes |
|----|------|-------|
| Qdrant | 6333 | REST + gRPC |
| pgvector | 5433 | PostgreSQL + extension |
| Milvus | 19530 | + etcd + MinIO |
| OpenSearch | 9200 | Single-node, no auth |

---

## เอกสารแต่ละ DB

- [Qdrant](qdrant/README.md)
- [pgvector](pgvector/README.md)
- [Milvus](milvus/README.md)
- [OpenSearch](opensearch/README.md)
