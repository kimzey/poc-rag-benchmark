# Multilingual E5 Large — Microsoft

## คืออะไร

Multilingual E5 Large (`intfloat/multilingual-e5-large`) เป็น embedding model จาก Microsoft รองรับ 100+ ภาษา และมีการออกแบบพิเศษคือต้องใส่ **prefix** ตอน encode: `"query: "` สำหรับคำถาม และ `"passage: "` สำหรับ document — prefix นี้เป็นส่วนหนึ่งของ training protocol

- License: MIT
- Dimensions: 1024
- Max tokens: 512
- Cost: $0 (self-hosted)
- Vendor lock-in: 0
- Self-hostable: ✅

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/embedding-model/models/multilingual_e5.py
benchmarks/embedding-model/base.py
```

---

## โครงสร้าง Code (`models/multilingual_e5.py`)

### Class: `MultilingualE5LargeModel`

```python
class MultilingualE5LargeModel(BaseEmbeddingModel):
    def __init__(self)
    @property
    def meta(self) -> ModelMeta
    def _encode_raw(self, texts: list[str]) -> np.ndarray
    def encode_queries(self, texts: list[str]) -> EmbedResult   # override
    def encode_passages(self, texts: list[str]) -> EmbedResult  # override
```

---

## อธิบาย Code ทีละส่วน

### `__init__()` — โหลด model

```python
from sentence_transformers import SentenceTransformer
self._model = SentenceTransformer("intfloat/multilingual-e5-large")
self._is_query = False  # flag สำหรับ prefix toggling
```

---

### `_encode_raw()` — เพิ่ม prefix ก่อน encode

```python
_QUERY_PREFIX = "query: "
_PASSAGE_PREFIX = "passage: "

def _encode_raw(self, texts: list[str]) -> np.ndarray:
    # เลือก prefix ตาม flag _is_query
    prefixed = [
        (_QUERY_PREFIX if self._is_query else _PASSAGE_PREFIX) + t
        for t in texts
    ]
    return self._model.encode(
        prefixed,
        show_progress_bar=False,
        normalize_embeddings=True,
        batch_size=16,   # batch เล็กกว่า BGE-M3 เพราะ input ยาวขึ้น (มี prefix)
    )
```

**ทำไมต้องมี prefix?** E5 models ถูก train ด้วย contrastive learning บน query-passage pairs โดยมี prefix เป็นส่วนหนึ่งของ input — การ encode โดยไม่มี prefix จะได้ recall ต่ำกว่า

---

### `encode_queries()` / `encode_passages()` — Override สำหรับ prefix switching

```python
def encode_queries(self, texts: list[str]) -> EmbedResult:
    """Encode queries with 'query: ' prefix."""
    self._is_query = True
    t0 = time.perf_counter()
    raw = self._encode_raw(texts)
    self._is_query = False  # reset หลังใช้
    return EmbedResult(embeddings=raw.astype("float32"), latency_ms=...)

def encode_passages(self, texts: list[str]) -> EmbedResult:
    """Encode passages with 'passage: ' prefix."""
    self._is_query = False
    t0 = time.perf_counter()
    raw = self._encode_raw(texts)
    return EmbedResult(...)
```

Base class `encode()` ใช้ `passage:` prefix เสมอ (default `_is_query=False`)

การ encode query ที่ถูกต้องต้องเรียก `encode_queries()` แทน `encode()`

---

## สำคัญ: Query vs Passage Encoding

```python
# ❌ ผิด — encode query ด้วย "passage: " prefix
model.encode(["วันหยุดมีกี่วัน"])

# ✅ ถูก — encode query ด้วย "query: " prefix
model.encode_queries(["วันหยุดมีกี่วัน"])

# ✅ ถูก — encode corpus ด้วย "passage: " prefix
model.encode_passages(["ข้อ 5. พนักงานมีวันหยุดประจำปี 10 วัน..."])
```

---

## meta property

```python
ModelMeta(
    name="multilingual-e5-large",
    dimensions=1024,
    max_tokens=512,    # สั้นกว่า BGE-M3 (8192)
    cost_per_1m_tokens=0.0,
    vendor_lock_in=0,
    self_hostable=True,
)
```

---

## จุดเด่น / จุดด้อย

| จุดเด่น | จุดด้อย |
|--------|---------|
| MIT license — ใช้เชิงพาณิชย์ได้ | Max 512 tokens — ไม่รองรับ document ยาว |
| Microsoft research quality | ต้องจำใส่ prefix (ลืม = recall ลด) |
| Multilingual ดี | batch_size เล็ก (16) เพราะ input ยาวขึ้น |
| ไม่มีค่า API | |

---

## ผลใน Benchmark (Phase 3)

- **Thai Recall:** ดี แต่ต่ำกว่า BGE-M3 เล็กน้อย (max_tokens 512 vs 8192)
- **English Recall:** ดี
- **Latency:** ปานกลาง
- Prefix requirement สำคัญมาก — evaluation runner ต้องเรียก `encode_queries()` ไม่ใช่ `encode()`
