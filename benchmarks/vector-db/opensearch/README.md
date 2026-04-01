# OpenSearch — Search Engine + Vector DB

## คืออะไร

OpenSearch เป็น open-source distributed search engine (fork ของ Elasticsearch) ที่เพิ่มความสามารถ k-NN vector search ผ่าน plugin `k-NN` ทำให้สามารถรวม full-text search + vector search ในระบบเดียวกันได้

- License: Apache 2.0
- Architecture: distributed, Lucene-based
- Vector Index: HNSW ผ่าน nmslib engine
- ข้อดีเด่น: full-text search + vector search ในคำสั่งเดียว

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/vector-db/clients/opensearch.py  # adapter implementation
benchmarks/vector-db/clients/base.py        # interface
```

---

## โครงสร้าง Code (`clients/opensearch.py`)

### Class: `OpenSearchAdapter`

```python
class OpenSearchAdapter(VectorDBClient):
    name = "OpenSearch"

    def __init__(self, host="localhost", port=9200):
        self.host = host
        self.port = port
        self._client: OpenSearch | None = None
        self._index = INDEX

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
self._client = OpenSearch(
    hosts=[{"host": self.host, "port": self.port}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
    timeout=60,
)
```

- `http_compress=True` — gzip compression ลด bandwidth (มีผลมากเมื่อ insert vector จำนวนมาก)
- `use_ssl=False` — dev environment ไม่ใช้ TLS

---

### `create_collection()` — Index Mapping กับ knn_vector

```python
self._client.indices.create(
    index=name,
    body={
        "settings": {
            "index": {
                "knn": True,                           # เปิดใช้ k-NN plugin
                "knn.algo_param.ef_search": 64,        # ค่า ef ตอน search
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }
        },
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "knn_vector",              # OpenSearch vector field type
                    "dimension": self.DIM,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",   # cosine similarity
                        "engine": "nmslib",            # HNSW engine
                        "parameters": {"ef_construction": 64, "m": 16},
                    },
                },
                "access_level": {"type": "keyword"},  # keyword = exact match filter
                "category": {"type": "keyword"},
                "source": {"type": "keyword"},
            }
        },
    },
)
```

**สำคัญ:** ใน OpenSearch index คือ "collection" — schema กำหนดใน `mappings`

`"type": "knn_vector"` — field type พิเศษจาก k-NN plugin
`"engine": "nmslib"` — ใช้ nmslib เป็น HNSW engine (อีกตัวคือ `faiss`)

---

### `insert()` — Bulk API

```python
actions = [
    {
        "_index": self._index,
        "_id": str(i),
        "_source": {
            "embedding": r.vector,
            **r.metadata,       # unpack access_level, category, source
        },
    }
    for i, r in enumerate(records)
]
helpers.bulk(self._client, actions, chunk_size=500, request_timeout=120)
self._client.indices.refresh(index=self._index)
```

- `helpers.bulk()` — ส่ง bulk request ไปยัง OpenSearch (ประหยัด network round-trips)
- `chunk_size=500` — ส่งทีละ 500 documents ต่อ HTTP request
- `refresh()` — force refresh index ให้เห็น documents ทันทีใน search (ปกติ refresh ทุก 1s)

---

### `search()` — kNN Query + Bool Filter

```python
# ไม่มี filter
knn_query = {
    "knn": {
        "embedding": {
            "vector": query_vector,
            "k": top_k,
        }
    }
}

# มี filter → ห่อด้วย bool query
if filter:
    must_terms = [{"term": {k: v}} for k, v in filter.items()]
    query_body = {
        "query": {
            "bool": {
                "must": [knn_query],   # kNN เป็น must condition
                "filter": must_terms,  # metadata filter
            }
        }
    }

resp = self._client.search(
    index=self._index,
    body={**query_body, "size": top_k},
)
```

**OpenSearch Filter:** ใช้ Elasticsearch query DSL (`bool` + `term`) — แตกต่างจาก Qdrant/Milvus มากที่สุด

**หมายเหตุ:** การรวม kNN กับ `bool.filter` อาจมีผล recall เพราะ HNSW search ต้องผ่าน pre-filter ก่อน

---

### `count()`

```python
resp = self._client.count(index=self._index)
return resp["count"]
```

---

## Infrastructure

```yaml
# docker/docker-compose.vector-db.yml
opensearch:
  image: opensearchproject/opensearch:2.x
  ports:
    - "9200:9200"
  environment:
    - discovery.type=single-node
    - DISABLE_SECURITY_PLUGIN=true
    - OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g
```

- `discovery.type=single-node` — dev mode, ไม่ต้อง cluster setup
- `DISABLE_SECURITY_PLUGIN=true` — ปิด auth (dev only)
- `-Xms2g -Xmx2g` — กำหนด JVM heap (OpenSearch ใช้ Java)

---

## ข้อดี / ข้อด้อย

| ข้อดี | ข้อด้อย |
|------|---------|
| Full-text + vector search ในคำสั่งเดียว | ใช้ Java + Lucene มาก memory กว่า Rust-based DBs |
| Elasticsearch query DSL ที่ mature | k-NN เป็น plugin ไม่ใช่ first-class feature |
| Aggregations, highlight, autocomplete | JVM warmup ทำให้ latency แรกๆ สูง |
| Ecosystem ใหญ่ (Logstash, Kibana/Dashboards) | Config ซับซ้อน (index settings, mappings) |

---

## Use Case ที่เหมาะสม

- ระบบที่ต้องการทั้ง full-text search (BM25) + vector search (semantic)
- มี infrastructure OpenSearch/Elasticsearch อยู่แล้ว
- ต้องการ hybrid search (full-text + kNN ในคำสั่งเดียว)
