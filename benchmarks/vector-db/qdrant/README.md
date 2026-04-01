# Qdrant — Vector Database

## คืออะไร

Qdrant เป็น Vector Database ที่เขียนด้วย Rust ออกแบบมาสำหรับงาน vector similarity search โดยเฉพาะ รองรับทั้ง REST API และ gRPC, มี filter ที่ยืดหยุ่น, และ type-safe payload (ที่เก็บ metadata)

- License: Apache 2.0
- Storage: in-memory หรือ disk-based
- Index: HNSW (Hierarchical Navigable Small World)

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/vector-db/clients/qdrant.py   # adapter implementation
benchmarks/vector-db/clients/base.py     # interface
```

---

## โครงสร้าง Code (`clients/qdrant.py`)

### Class: `QdrantAdapter`

```python
class QdrantAdapter(VectorDBClient):
    name = "Qdrant"

    def __init__(self, host="localhost", port=6333):
        ...

    def connect(self) -> None
    def create_collection(self, name: str) -> None
    def insert(self, records: list[BenchmarkRecord]) -> None
    def search(self, query_vector, top_k, filter) -> list[SearchResult]
    def count(self) -> int
    def drop_collection(self) -> None
```

---

## อธิบาย Code ทีละส่วน

### `connect()`

```python
def connect(self) -> None:
    self._client = QdrantClient(host=self.host, port=self.port, timeout=30)
```

สร้าง `QdrantClient` เชื่อมต่อ REST API ที่ `localhost:6333`

---

### `create_collection()`

```python
self._client.create_collection(
    collection_name=name,
    vectors_config=VectorParams(size=self.DIM, distance=Distance.COSINE),
)
```

- ถ้า collection ชื่อเดิมมีอยู่แล้วจะ delete ก่อน (clean slate)
- `size=1536` — ตาม DIM ของ OpenAI text-embedding-3-small
- `distance=Distance.COSINE` — ใช้ cosine similarity

> Qdrant จัดการ HNSW index อัตโนมัติเมื่อสร้าง collection — ไม่ต้องกำหนด index params แยก (ต่างจาก Milvus/pgvector)

---

### `insert()`

```python
points = [
    PointStruct(id=i, vector=r.vector, payload=r.metadata)
    for i, r in enumerate(records)
]
# Batch in chunks of 1000
for i in range(0, len(points), batch_size):
    self._client.upsert(
        collection_name=self._collection,
        points=points[i : i + batch_size],
    )
```

- แปลง `BenchmarkRecord` เป็น `PointStruct` (Qdrant data model)
- `payload` = metadata (access_level, category, source) เก็บเป็น JSON บน point
- upsert แบบ batch ขนาด 1,000 รายการ (ลด overhead ของ HTTP round-trips)

---

### `search()`

```python
# สร้าง filter จาก dict
if filter:
    must = [
        FieldCondition(key=k, match=MatchValue(value=v))
        for k, v in filter.items()
    ]
    qdrant_filter = Filter(must=must)

hits = self._client.query_points(
    collection_name=self._collection,
    query=query_vector,
    limit=top_k,
    query_filter=qdrant_filter,
).points
```

**Filter syntax ของ Qdrant:** ใช้ `Filter(must=[FieldCondition(...)])` เป็น structured object แทน string expression

ตัวอย่าง filter: `{"access_level": "internal"}` → ค้นหาเฉพาะ documents ระดับ internal

---

### `count()`

```python
return self._client.count(collection_name=self._collection).count
```

---

### `drop_collection()`

```python
self._client.delete_collection(self._collection)
```

---

## Infrastructure

```yaml
# docker/docker-compose.vector-db.yml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"   # REST API
    - "6334:6334"   # gRPC
```

---

## ข้อดี / ข้อด้อย

| ข้อดี | ข้อด้อย |
|------|---------|
| Pure vector DB, optimized สำหรับงานนี้โดยเฉพาะ | ไม่มี full-text search built-in |
| Filter ยืดหยุ่น, type-safe payload | ต้องการ separate service (ไม่ใช่ extension) |
| HNSW index อัตโนมัติ, config ง่าย | |
| Rust-based, memory efficient | |
| REST + gRPC + Python SDK | |

---

## ผลการ Benchmark (10K vectors, dim=1536)

ดูผลเต็มได้ที่ `benchmarks/vector-db/results/` และ `docs/BENCHMARK_SUMMARY.md`

| Metric | ค่าที่ได้ |
|--------|---------|
| Index throughput | สูง (native vector DB) |
| Search p50 | ต่ำ |
| Search p95 | ต่ำ |
| Recall@10 | สูง |
| Filtered p95 | ต่ำ (filter ถูก push down ที่ index) |
