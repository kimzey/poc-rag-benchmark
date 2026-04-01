# pgvector — PostgreSQL Vector Extension

## คืออะไร

pgvector เป็น extension สำหรับ PostgreSQL ที่เพิ่มความสามารถ vector similarity search เข้าไปในฐานข้อมูลเชิงสัมพันธ์ ทำให้สามารถเก็บ vector ใน column ปกติของตาราง SQL และค้นหาด้วย ANN ได้

- License: PostgreSQL License (open-source)
- Storage: PostgreSQL MVCC (disk-based, ACID)
- Index: HNSW หรือ IVFFlat
- ข้อดีเด่น: ใช้ SQL ปกติ + vector search ในคำสั่งเดียว

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/vector-db/clients/pgvector.py  # adapter implementation
benchmarks/vector-db/clients/base.py      # interface
```

---

## โครงสร้าง Code (`clients/pgvector.py`)

### Class: `PgvectorAdapter`

```python
class PgvectorAdapter(VectorDBClient):
    name = "pgvector"

    def __init__(self, host="localhost", port=5433,
                 dbname="vectordb", user="spike", password="spike"):
        self.dsn = f"host={host} port={port} ..."
        self._conn = None

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
    self._conn = psycopg2.connect(self.dsn)
    self._conn.autocommit = False
    with self._conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    self._conn.commit()
    register_vector(self._conn)  # pgvector Python type registration
```

- เชื่อมต่อ PostgreSQL ด้วย `psycopg2`
- สร้าง extension `vector` ถ้ายังไม่มี
- `register_vector()` ลงทะเบียน Python type ให้ psycopg2 รู้จัก `vector` column

---

### `create_collection()` — สร้างตาราง + HNSW index

```python
cur.execute(f"""
    CREATE TABLE {self._table} (
        id          BIGINT PRIMARY KEY,
        embedding   vector({self.DIM}),   -- pgvector column type
        access_level TEXT,
        category    TEXT,
        source      TEXT
    )
""")
cur.execute(f"""
    CREATE INDEX ON {self._table}
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
""")
```

- `vector(1536)` — column type พิเศษจาก pgvector extension
- `vector_cosine_ops` — ใช้ cosine distance สำหรับ HNSW index
- `m=16, ef_construction=64` — HNSW parameters (เหมือนกับ Milvus/OpenSearch)

---

### `insert()` — batch insert ด้วย `executemany`

```python
args = [
    (idx + i, r.vector, r.metadata.get("access_level"), ...)
    for idx, r in enumerate(batch)
]
cur.executemany(
    f"INSERT INTO {self._table} (id, embedding, access_level, ...) VALUES (%s, %s, %s, ...)",
    args,
)
self._conn.commit()
```

- batch size = 500 (เล็กกว่า Qdrant/OpenSearch เพราะ SQL overhead ต่อ row)
- `r.vector` ส่งเป็น Python list — psycopg2 + pgvector แปลงเป็น `vector` SQL type อัตโนมัติ

---

### `search()` — SQL query ด้วย `<=>` operator

```python
sql = f"""
    SELECT id, access_level, category, source,
           1 - (embedding <=> %s::vector) AS score   -- cosine similarity
    FROM {self._table}
    {where}                                           -- optional filter
    ORDER BY embedding <=> %s::vector                 -- HNSW ANN
    LIMIT %s
"""
cur.execute("SET LOCAL hnsw.ef_search = 100")  # เพิ่ม accuracy ชั่วคราว
cur.execute(sql, params)
```

**pgvector operators:**
- `<=>` — cosine distance (ต่ำ = ใกล้กัน)
- `score = 1 - cosine_distance` แปลงเป็น similarity (สูง = ใกล้กัน)
- `SET LOCAL hnsw.ef_search = 100` — เพิ่มจำนวน candidate nodes ใน HNSW traversal

**Filter:** เป็น SQL WHERE clause ปกติ — pgvector ไม่มี filter DSL พิเศษ

---

### `drop_collection()`

```python
cur.execute(f"DROP TABLE IF EXISTS {self._table}")
```

ลบทั้งตาราง (พร้อม index ทั้งหมด)

---

## Infrastructure

```yaml
# docker/docker-compose.vector-db.yml
pgvector:
  image: pgvector/pgvector:pg16
  ports:
    - "5433:5432"
  environment:
    POSTGRES_DB: vectordb
    POSTGRES_USER: spike
    POSTGRES_PASSWORD: spike
```

> ใช้ port 5433 (ไม่ใช่ 5432 default) เพื่อหลีกเลี่ยง conflict กับ PostgreSQL ที่อาจรันอยู่ใน local

---

## ข้อดี / ข้อด้อย

| ข้อดี | ข้อด้อย |
|------|---------|
| รวม relational data + vector ในที่เดียว | ไม่ได้ออกแบบมาสำหรับ vector โดยเฉพาะ |
| SQL filter ยืดหยุ่นมาก (JOIN, WHERE ซับซ้อน) | Recall อาจต่ำกว่า native vector DB |
| ACID transactions | HNSW ใน PostgreSQL ช้ากว่า Qdrant/Milvus |
| ไม่ต้องเพิ่ม service ถ้ามี PostgreSQL อยู่แล้ว | |
| Familiar SQL tooling | |

---

## Use Case ที่เหมาะสม

- มี PostgreSQL อยู่แล้ว และต้องการเพิ่ม vector search โดยไม่เพิ่ม infrastructure
- ต้องการ filter ที่ซับซ้อน (JOIN กับ table อื่น, subquery)
- ข้อมูลไม่ได้ใหญ่มาก (< 10M vectors) และ latency requirement ไม่ keenly strict
