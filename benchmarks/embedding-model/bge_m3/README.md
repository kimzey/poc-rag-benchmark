# BGE-M3 — BAAI General Embedding M3

## คืออะไร

BGE-M3 (BAAI/bge-m3) เป็น embedding model แบบ multilingual จาก Beijing Academy of Artificial Intelligence (BAAI) รองรับภาษาได้มากกว่า 100 ภาษา รวมถึงภาษาไทย มีความสามารถ 3 แบบในโมเดลเดียว (M3 = Multi-Functionality, Multi-Linguality, Multi-Granularity)

- License: Apache 2.0
- Dimensions: 1024
- Max tokens: 8,192 (รองรับ context ยาวมาก)
- Cost: $0 (self-hosted)
- Vendor lock-in: 0 (fully open-source)
- Self-hostable: ✅

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/embedding-model/models/bge_m3.py
benchmarks/embedding-model/base.py     # BaseEmbeddingModel interface
```

---

## โครงสร้าง Code (`models/bge_m3.py`)

### Class: `BGEM3Model`

```python
class BGEM3Model(BaseEmbeddingModel):
    def __init__(self)
    @property
    def meta(self) -> ModelMeta
    def _encode_raw(self, texts: list[str]) -> np.ndarray
```

---

## อธิบาย Code ทีละส่วน

### `__init__()` — โหลด model ผ่าน sentence-transformers

```python
def __init__(self) -> None:
    from sentence_transformers import SentenceTransformer
    self._model = SentenceTransformer("BAAI/bge-m3")
```

- โหลด model จาก HuggingFace Hub ครั้งแรก (~560MB) จะ cache ไว้ใน `~/.cache/huggingface/`
- ใช้ `sentence-transformers` library เป็น wrapper บน PyTorch transformer

---

### `meta` property — Model metadata

```python
@property
def meta(self) -> ModelMeta:
    return ModelMeta(
        name="BGE-M3",
        dimensions=1024,
        max_tokens=8192,
        cost_per_1m_tokens=0.0,   # ไม่มีค่าใช้จ่าย API
        vendor_lock_in=0,          # Apache 2.0, fully open
        self_hostable=True,
    )
```

`max_tokens=8192` — ข้อดีเด่นของ BGE-M3 คือรองรับ context ยาวถึง 8K tokens (มาก model อื่นสูงสุด 512)

---

### `_encode_raw()` — Encode ด้วย sentence-transformers

```python
def _encode_raw(self, texts: list[str]) -> np.ndarray:
    return self._model.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,  # L2-normalize ให้เลย
        batch_size=32,
    )
```

- `normalize_embeddings=True` — BGE-M3 normalize ใน `_encode_raw()` เองแล้ว (base class จะ normalize อีกรอบ แต่ไม่เป็นไร เพราะ norm ของ normalized vector = 1)
- `batch_size=32` — ส่ง 32 texts ต่อ forward pass (เหมาะกับ VRAM ทั่วไป)

**Base class `encode()` จะ L2-normalize อีกครั้ง** (safe เพราะ idempotent) และวัด latency

---

## BGE-M3 Three Capabilities (M3)

| Capability | คำอธิบาย |
|-----------|---------|
| **Dense Retrieval** | Embedding ปกติ (ที่ใช้ใน benchmark นี้) |
| **Sparse Retrieval** | SPLADE-style (BM25-like, keyword matching) |
| **Multi-Vector** | ColBERT-style (late interaction) |

benchmark นี้ใช้แค่ Dense Retrieval ผ่าน sentence-transformers

---

## จุดเด่น / จุดด้อย

| จุดเด่น | จุดด้อย |
|--------|---------|
| Max 8,192 tokens — รองรับ document ยาว | Model ใหญ่ (~560MB download) |
| Multilingual แข็งแกร่ง (> 100 ภาษา รวม Thai) | ช้ากว่า model เล็ก เมื่อรัน CPU-only |
| Apache 2.0 — ใช้เชิงพาณิชย์ได้ | ต้องมี RAM > 4GB |
| ไม่มีค่าใช้จ่าย API | |
| MTEB leaderboard ติดอันดับต้น | |

---

## ผลใน Benchmark (Phase 3)

- **Thai Recall:** สูง — BGE-M3 ถูก train ด้วยข้อมูล Thai จำนวนมาก
- **English Recall:** สูง
- **Latency:** ปานกลาง (model ใหญ่กว่า E5 small)
- **Cost:** $0/1M tokens
- **Vendor Lock-in:** 0

ดูผลเต็มได้ที่ `benchmarks/embedding-model/results/` และ `docs/BENCHMARK_SUMMARY.md`
