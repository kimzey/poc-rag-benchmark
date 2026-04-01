# Cohere Embed Multilingual v3

## คืออะไร

`embed-multilingual-v3` เป็น embedding model จาก Cohere รองรับ 100+ ภาษารวมถึงภาษาไทย มีจุดเด่นคือรองรับ **input_type** parameter ที่แยก query กับ document embeddings ให้ชัดเจน (คล้าย E5 แต่ใช้ API parameter แทน text prefix)

- License: proprietary (commercial)
- Dimensions: 1024
- Max tokens: 512
- Cost: $0.10/1M tokens
- Vendor lock-in: 6/10
- Self-hostable: ❌

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/embedding-model/models/cohere_v3.py
benchmarks/embedding-model/base.py
```

---

## โครงสร้าง Code (`models/cohere_v3.py`)

### Class: `CohereEmbedV3Model`

```python
class CohereEmbedV3Model(BaseEmbeddingModel):
    MODEL = "embed-multilingual-v3.0"

    def __init__(self) -> None
    @property
    def meta(self) -> ModelMeta
    def _encode_raw(self, texts: list[str]) -> np.ndarray
    def encode_queries(self, texts: list[str]) -> EmbedResult   # override
    def encode_passages(self, texts: list[str]) -> EmbedResult  # override
```

---

## อธิบาย Code ทีละส่วน

### `__init__()` — Cohere client initialization

```python
def __init__(self) -> None:
    import cohere
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        raise EnvironmentError("COHERE_API_KEY not set — skipping Cohere")
    self._client = cohere.Client(api_key=api_key)
    self._input_type = "search_document"  # default: encode passages
```

---

### `meta` property

```python
ModelMeta(
    name="Cohere embed-multilingual-v3",
    dimensions=1024,
    max_tokens=512,
    cost_per_1m_tokens=0.10,
    vendor_lock_in=6,      # ต่ำกว่า OpenAI เพราะ Cohere มี API ที่ยืดหยุ่นกว่า
    self_hostable=False,
)
```

---

### `_encode_raw()` — Cohere Embed API กับ input_type

```python
def _encode_raw(self, texts: list[str]) -> np.ndarray:
    resp = self._client.embed(
        texts=texts,
        model=self.MODEL,
        input_type=self._input_type,  # "search_query" หรือ "search_document"
    )
    return np.array(resp.embeddings, dtype=np.float32)
```

**Cohere `input_type`:**
- `"search_document"` — encode documents/passages สำหรับ indexing
- `"search_query"` — encode queries สำหรับ retrieval
- `"classification"` — classification tasks
- `"clustering"` — clustering tasks

---

### `encode_queries()` / `encode_passages()` — Override เพื่อ switch input_type

```python
def encode_queries(self, texts: list[str]) -> EmbedResult:
    self._input_type = "search_query"
    t0 = time.perf_counter()
    raw = self._encode_raw(texts)
    self._input_type = "search_document"  # reset
    return EmbedResult(embeddings=raw.astype("float32"), latency_ms=...)

def encode_passages(self, texts: list[str]) -> EmbedResult:
    self._input_type = "search_document"
    ...
```

Pattern เหมือน E5 แต่ใช้ API parameter แทน text prefix

---

## เปรียบเทียบ: Cohere vs E5 vs OpenAI

| | Cohere v3 | Multilingual E5 | OpenAI small |
|---|---|---|---|
| Dimensions | 1024 | 1024 | 1536 |
| Max tokens | 512 | 512 | 8,191 |
| Cost/1M | $0.10 | $0 | $0.02 |
| Query/doc separation | API param | text prefix | ไม่ต้อง |
| Thai support | ดี | ดี | ปานกลาง |
| Lock-in | 6 | 0 | 8 |

---

## จุดเด่น / จุดด้อย

| จุดเด่น | จุดด้อย |
|--------|---------|
| `input_type` API ชัดเจนกว่า prefix | $0.10/1M — แพงกว่า OpenAI small |
| Multilingual quality ดี | Max 512 tokens |
| Cohere platform มี features เพิ่มเติม | Cohere SDK เป็น proprietary |
| Lock-in ต่ำกว่า OpenAI (6 vs 8) | ไม่ self-hostable |

---

## วิธีใช้ใน Benchmark

```bash
# ต้องมี COHERE_API_KEY ใน .env
echo "COHERE_API_KEY=..." >> .env

# รันทุก model รวม commercial
python evaluate.py --models all
```
