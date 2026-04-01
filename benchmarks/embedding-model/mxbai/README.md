# MxBai Embed Large v1 — mixedbread.ai

## คืออะไร

mxbai-embed-large-v1 เป็น embedding model จาก mixedbread.ai ออกแบบมาเน้น English ก่อน แต่รองรับ multilingual ด้วย มีประสิทธิภาพสูงใน MTEB benchmark สำหรับ English retrieval tasks

- License: Apache 2.0
- Dimensions: 1024
- Max tokens: 512
- Cost: $0 (self-hosted)
- Vendor lock-in: 0
- Self-hostable: ✅

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/embedding-model/models/mxbai.py
benchmarks/embedding-model/base.py
```

---

## โครงสร้าง Code (`models/mxbai.py`)

### Class: `MxbaiEmbedLargeModel`

```python
class MxbaiEmbedLargeModel(BaseEmbeddingModel):
    def __init__(self)
    @property
    def meta(self) -> ModelMeta
    def _encode_raw(self, texts: list[str]) -> np.ndarray
```

---

## อธิบาย Code ทีละส่วน

### `__init__()` — โหลด model

```python
def __init__(self) -> None:
    from sentence_transformers import SentenceTransformer
    self._model = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")
```

โหลดจาก HuggingFace Hub ขนาด ~670MB

---

### `meta` property

```python
ModelMeta(
    name="mxbai-embed-large-v1",
    dimensions=1024,
    max_tokens=512,
    cost_per_1m_tokens=0.0,
    vendor_lock_in=0,
    self_hostable=True,
)
```

---

### `_encode_raw()` — Standard sentence-transformers encode

```python
def _encode_raw(self, texts: list[str]) -> np.ndarray:
    return self._model.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,
        batch_size=16,
    )
```

ไม่ต้องการ prefix พิเศษ (ต่างจาก E5) — encode ได้เลย

---

## เปรียบเทียบกับ E5 Large

| ประเด็น | MxBai | Multilingual E5 |
|--------|-------|----------------|
| Prefix requirement | ไม่ต้อง | ต้อง (query: / passage:) |
| English strength | แข็งมาก | ดี |
| Thai support | ปานกลาง | ดีกว่า (Microsoft multilingual) |
| License | Apache 2.0 | MIT |
| Max tokens | 512 | 512 |

---

## จุดเด่น / จุดด้อย

| จุดเด่น | จุดด้อย |
|--------|---------|
| ใช้งานง่าย ไม่ต้อง prefix | Thai recall อาจต่ำกว่า BGE-M3 |
| English retrieval แข็งมาก | Max 512 tokens |
| Apache 2.0 | mixedbread.ai เป็น company เล็ก (ecosystem เล็กกว่า) |
| MTEB ranking สูงสำหรับ English | |

---

## ผลใน Benchmark (Phase 3)

- **English Recall:** สูง
- **Thai Recall:** ปานกลาง (ต่ำกว่า BGE-M3 สำหรับภาษาไทย)
- **Latency:** ปานกลาง
- ดีสำหรับ English-only หรือ mixed corpus ที่ English เป็นส่วนใหญ่
