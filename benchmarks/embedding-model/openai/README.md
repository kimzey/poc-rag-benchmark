# OpenAI Embeddings — text-embedding-3-small / text-embedding-3-large

## คืออะไร

OpenAI Embedding API เป็น commercial embedding service จาก OpenAI รองรับ 2 model:
- **text-embedding-3-small** — ราคาถูก ขนาดกะทัดรัด เหมาะ production ที่ cost-sensitive
- **text-embedding-3-large** — คุณภาพสูงสุด ขนาด vector ใหญ่กว่า

ทั้งสอง model support **dimension reduction** — สามารถตัด dimensions ให้เล็กลงได้โดยไม่กระทบ quality มากนัก

- License: proprietary
- Cost: small $0.02/1M tokens, large $0.13/1M tokens
- Vendor lock-in: 8/10 (proprietary API + pricing)
- Self-hostable: ❌

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/embedding-model/models/openai_small.py
benchmarks/embedding-model/models/openai_large.py
benchmarks/embedding-model/base.py
```

---

## โครงสร้าง Code

### `openai_small.py` — text-embedding-3-small

```python
class OpenAISmallModel(BaseEmbeddingModel):
    MODEL = "text-embedding-3-small"

    def __init__(self) -> None:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not set — skipping OpenAI Small")
        self._client = OpenAI(api_key=api_key)

    @property
    def meta(self) -> ModelMeta:
        return ModelMeta(
            name="OpenAI text-embedding-3-small",
            dimensions=1536,
            max_tokens=8191,
            cost_per_1m_tokens=0.020,
            vendor_lock_in=8,
            self_hostable=False,
        )

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        resp = self._client.embeddings.create(
            model=self.MODEL,
            input=texts,
        )
        return np.array([d.embedding for d in resp.data], dtype=np.float32)
```

### `openai_large.py` — text-embedding-3-large

โครงสร้างเหมือนกัน แต่:
- `MODEL = "text-embedding-3-large"`
- `dimensions=3072`
- `cost_per_1m_tokens=0.130`

---

## อธิบาย Code ทีละส่วน

### `__init__()` — API Key validation

```python
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not set — skipping OpenAI Small")
self._client = OpenAI(api_key=api_key)
```

ถ้าไม่มี `OPENAI_API_KEY` ใน env จะ raise `EnvironmentError` → evaluation runner จะ skip model นี้อัตโนมัติ

---

### `_encode_raw()` — OpenAI Embeddings API

```python
def _encode_raw(self, texts: list[str]) -> np.ndarray:
    resp = self._client.embeddings.create(
        model=self.MODEL,
        input=texts,    # list of strings — OpenAI จัดการ batching เอง
    )
    return np.array([d.embedding for d in resp.data], dtype=np.float32)
```

- ส่ง list ทั้งหมดให้ OpenAI จัดการ batching เอง (ไม่ต้อง split เอง)
- `resp.data` = list ของ `Embedding` objects เรียงตามลำดับ input

**ข้อจำกัด:** OpenAI API มี rate limits และ max tokens per request (~8,191 tokens per input)

**ไม่มี normalize:** OpenAI คืนค่า L2-normalized embeddings อยู่แล้ว (base class normalize อีกรอบ แต่ idempotent)

---

## ความแตกต่าง small vs large

| | text-embedding-3-small | text-embedding-3-large |
|---|---|---|
| Dimensions | 1536 | 3072 |
| Cost/1M tokens | $0.020 | $0.130 |
| Quality (MTEB) | ดี | ดีกว่า |
| Storage/query | น้อยกว่า | มากกว่า (2x) |
| Use case | Production cost-sensitive | Quality-first |

---

## Dimension Reduction (Feature ของ OpenAI)

OpenAI text-embedding-3 รองรับ `dimensions` parameter:
```python
resp = client.embeddings.create(
    model="text-embedding-3-small",
    input=texts,
    dimensions=512  # ลดจาก 1536 → 512
)
```

> benchmark นี้ไม่ได้ใช้ feature นี้ — encode เต็ม dimensions

---

## จุดเด่น / จุดด้อย

| จุดเด่น | จุดด้อย |
|--------|---------|
| Quality สูง (SOTA สำหรับ English) | ต้องจ่ายเงิน ($0.02-0.13/1M) |
| Max 8,191 tokens (context ยาวมาก) | ข้อมูลส่งออก OpenAI server |
| ไม่ต้องดูแล infrastructure | Lock-in สูง (proprietary API) |
| Dimension reduction support | Rate limits |
| Multilingual รองรับ แต่ไม่ได้เน้น | ไม่ self-hostable |

---

## วิธีใช้ใน Benchmark

```bash
# ต้องมี OPENAI_API_KEY ใน .env
echo "OPENAI_API_KEY=sk-..." >> .env

# รันทุก model รวม OpenAI
python evaluate.py --models all
```

ดูผลที่ `benchmarks/embedding-model/results/` และ `docs/BENCHMARK_SUMMARY.md`
