# Milvus — Vector Database

## คืออะไร

Milvus เป็น open-source Vector Database ที่ออกแบบมาสำหรับ production workloads ขนาดใหญ่ รองรับ distributed deployment, หลาย index type (HNSW, IVF, DiskANN), และมี schema ที่ structured

- License: Apache 2.0
- Architecture: distributed (etcd + MinIO + query node + data node)
- Index: HNSW, IVF_FLAT, IVF_SQ8, DiskANN
- ข้อดีเด่น: scale ได้สูง, cloud-native

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/vector-db/clients/milvus.py  # adapter implementation
benchmarks/vector-db/clients/base.py    # interface
```

---

## โครงสร้าง Code (`clients/milvus.py`)

### Class: `MilvusAdapter`

```python
class MilvusAdapter(VectorDBClient):
    name = "Milvus"

    def __init__(self, host="localhost", port=19530):
        self.host = host
        self.port = port
        self._collection: Collection | None = None

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
    connections.connect(alias="default", host=self.host, port=self.port)
```

Milvus ใช้ concept "connection alias" — สามารถมีหลาย connection pool ได้พร้อมกัน

---

### `create_collection()` — Schema แบบ Strongly-Typed

```python
schema = CollectionSchema(
    fields=[
        FieldSchema("id", DataType.INT64, is_primary=True),
        FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=self.DIM),
        FieldSchema("access_level", DataType.VARCHAR, max_length=32),
        FieldSchema("category", DataType.VARCHAR, max_length=64),
        FieldSchema("source", DataType.VARCHAR, max_length=256),
    ],
)
self._collection = Collection(name=name, schema=schema)

# สร้าง HNSW index แยกต่างหาก
self._collection.create_index(
    field_name="embedding",
    index_params={
        "index_type": "HNSW",
        "metric_type": "COSINE",
        "params": {"M": 16, "efConstruction": 64},
    },
)
```

**ต่างจาก Qdrant:** Milvus ต้อง define schema ทุก field ล่วงหน้า และสร้าง index แยก step

**HNSW Parameters:**
- `M=16` — จำนวน edges ต่อ node (ใหญ่ = recall ดีขึ้น, memory เพิ่ม)
- `efConstruction=64` — beam width ตอน build (ใหญ่ = quality ดี, build ช้า)

---

### `insert()` — Columnar Format

```python
self._collection.insert([
    [j + i for j in range(len(batch))],          # id (list)
    [r.vector for r in batch],                    # embedding (list of lists)
    [r.metadata.get("access_level", "") for r in batch],
    [r.metadata.get("category", "") for r in batch],
    [r.metadata.get("source", "") for r in batch],
])
self._collection.flush()   # เขียน WAL → persistent storage
self._collection.load()    # โหลด index เข้า memory สำหรับ search
```

**สำคัญ:** Milvus ต้องการข้อมูลในรูปแบบ **columnar** (list of lists ต่อ field) ไม่ใช่ row-by-row

`flush()` → เขียนข้อมูลลง disk  
`load()` → โหลด index เข้า RAM เพื่อให้ search ได้ (ต้องทำหลัง insert ทุกครั้ง)

---

### `search()` — Expression-based Filter

```python
# สร้าง filter expression เป็น string
if filter:
    parts = [f'{k} == "{v}"' for k, v in filter.items()]
    expr = " && ".join(parts)
    # ตัวอย่าง: 'access_level == "internal"'

results = self._collection.search(
    data=[query_vector],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 100}},  # ef ตอน search
    limit=top_k,
    expr=expr,
    output_fields=["access_level", "category", "source"],
)
```

**Milvus Filter:** เป็น expression string (`'field == "value"'`) — ต่างจาก Qdrant ที่เป็น structured object

`ef=100` ตอน search — ยิ่งสูง recall ยิ่งดี แต่ช้ากว่า

---

### `count()`

```python
self._collection.flush()
return self._collection.num_entities
```

ต้อง flush ก่อนเพื่อให้ count ถูกต้อง (Milvus มี eventual consistency ระหว่าง buffer กับ storage)

---

## Infrastructure

```yaml
# docker/docker-compose.vector-db.yml
milvus:
  image: milvusdb/milvus:v2.x
  ports:
    - "19530:19530"
  depends_on:
    - etcd
    - minio
```

Milvus standalone mode ต้องการ:
- **etcd** — metadata storage (collection schemas, segment info)
- **MinIO** — object storage (actual vector data)
- **Milvus** — query/index node

---

## ข้อดี / ข้อด้อย

| ข้อดี | ข้อด้อย |
|------|---------|
| Scale ได้สูง (billion vectors) | infrastructure ซับซ้อน (etcd + MinIO) |
| หลาย index type ให้เลือก | Schema strict ต้อง define ล่วงหน้า |
| Cloud-native, distributed | `load()` ทุกครั้งหลัง insert อาจลืม |
| Enterprise features (partitioning, RBAC) | Filter เป็น string expression (error-prone) |

---

## Use Case ที่เหมาะสม

- Production workloads ขนาดใหญ่ (> 100M vectors)
- ต้องการ distributed deployment
- ต้องการ index หลาย type (DiskANN สำหรับ dataset ใหญ่มาก)
