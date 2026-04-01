# Phase 3 — Embedding Model Benchmark

## ภาพรวม

Phase 3 เปรียบเทียบ embedding model 7 ตัว (open-source 4 ตัว + commercial 3 ตัว) โดยวัด Thai/English retrieval quality (Recall@k, MRR), latency, cost, และ vendor lock-in

---

## โครงสร้างโฟลเดอร์

```
benchmarks/embedding-model/
├── base.py              # Abstract base class (BaseEmbeddingModel)
├── config.py            # Configuration + paths
├── evaluate.py          # Evaluation runner หลัก
├── models/
│   ├── bge_m3.py        # BAAI/bge-m3 (open-source)
│   ├── multilingual_e5.py  # intfloat/multilingual-e5-large (open-source)
│   ├── mxbai.py         # mixedbread-ai/mxbai-embed-large-v1 (open-source)
│   ├── wangchanberta.py # airesearch/wangchanberta (Thai-specific)
│   ├── openai_small.py  # text-embedding-3-small (commercial)
│   ├── openai_large.py  # text-embedding-3-large (commercial)
│   └── cohere_v3.py     # embed-multilingual-v3 (commercial)
├── results/             # ผลลัพธ์ JSON
├── bge_m3/              # เอกสาร BGE-M3
├── multilingual_e5/     # เอกสาร Multilingual E5
├── mxbai/               # เอกสาร MxBai
├── wangchanberta/       # เอกสาร WangchanBERTa
├── openai/              # เอกสาร OpenAI Embeddings
└── cohere/              # เอกสาร Cohere
```

---

## Design Pattern: Abstract Base Class

```python
class BaseEmbeddingModel(ABC):
    @property
    def meta(self) -> ModelMeta: ...
    # คืนค่า metadata: name, dimensions, max_tokens, cost, lock_in, self_hostable

    def _encode_raw(self, texts: list[str]) -> np.ndarray: ...
    # subclass override — อาจคืนค่าที่ normalize แล้วหรือยังก็ได้

    def encode(self, texts: list[str]) -> EmbedResult:
    # public method — L2-normalize เสมอ, วัด latency
```

### Data Structures

```python
@dataclass
class EmbedResult:
    embeddings: np.ndarray  # shape (n, dims), L2-normalized
    latency_ms: float

@dataclass
class ModelMeta:
    name: str
    dimensions: int
    max_tokens: int
    cost_per_1m_tokens: float  # 0.0 = open-source
    vendor_lock_in: int        # 0 = fully open, 10 = hard lock-in
    self_hostable: bool
```

---

## รายการ Model

### Open-source (self-hosted, ฟรี)

| Model | Dimensions | Max Tokens | License | จุดเด่น |
|-------|-----------|-----------|---------|---------|
| BGE-M3 | 1024 | 8192 | Apache 2.0 | Multilingual แข็งแกร่ง |
| Multilingual E5 Large | 1024 | 512 | MIT | Microsoft, ต้องใส่ prefix |
| MxBai Embed Large | 1024 | 512 | Apache 2.0 | English/multilingual ดี |
| WangchanBERTa | 768 | 416 | Apache 2.0 | Thai-specific, VISTEC |

### Commercial (API-based)

| Model | Dimensions | Cost/1M tokens | Lock-in |
|-------|-----------|--------------|---------|
| OpenAI text-embedding-3-small | 1536 | $0.02 | สูง (8) |
| OpenAI text-embedding-3-large | 3072 | $0.13 | สูง (8) |
| Cohere embed-multilingual-v3 | 1024 | $0.10 | กลาง (6) |

---

## Evaluation Flow

```
1. โหลด corpus: hr_policy_th.md, tech_docs_en.md, faq_mixed.md
2. Chunk ด้วย word-based sliding window (CHUNK_SIZE=500, OVERLAP=50)
3. สร้าง ground truth ด้วย token overlap heuristic
4. สำหรับแต่ละ model:
   a. encode corpus chunks
   b. สำหรับแต่ละ question:
      - encode query
      - cosine similarity retrieval
      - คำนวณ Recall@k และ MRR
   c. แยก Thai vs English questions
5. คำนวณ weighted score
6. แสดงตาราง + บันทึก JSON
```

---

## Scoring Weights

| มิติ | น้ำหนัก | คำอธิบาย |
|-----|---------|---------|
| Thai Retrieval Recall | 25% | ประสิทธิภาพภาษาไทย (สำคัญที่สุด) |
| English Retrieval Recall | 15% | ประสิทธิภาพภาษาอังกฤษ |
| Latency | 15% | ความเร็ว encode |
| Cost | 15% | ราคาต่อ 1M tokens |
| Vendor Lock-in (ต่ำ=ดี) | 10% | อิสระจาก vendor |
| Dimension Efficiency | 5% | มิติต่ำ = storage/memory น้อย |
| Max Tokens | 5% | รองรับ context ยาว |
| Self-hostable | 10% | deploy บน infrastructure ตัวเองได้ |

> Higher-is-better metrics normalized 0→1; lower-is-better (latency, cost, dims, lock-in) inverted

---

## วิธีรัน

```bash
# รัน open-source models เท่านั้น
make embed-eval
# หรือ
python evaluate.py

# รวม OpenAI (ต้องมี OPENAI_API_KEY)
python evaluate.py --models all

# ปรับ top-k
python evaluate.py --top-k 5
```

---

## เอกสารแต่ละ Model

- [BGE-M3](bge_m3/README.md)
- [Multilingual E5](multilingual_e5/README.md)
- [MxBai Embed Large](mxbai/README.md)
- [WangchanBERTa](wangchanberta/README.md)
- [OpenAI Embeddings](openai/README.md)
- [Cohere Embed v3](cohere/README.md)
