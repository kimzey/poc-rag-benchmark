# WangchanBERTa — Thai-Specific Embedding Model

## คืออะไร

WangchanBERTa (`airesearch/wangchanberta-base-att-spm-uncased`) เป็น BERT-based model ที่ train เฉพาะภาษาไทย พัฒนาโดย VISTEC (Vidyasirimedhi Institute of Science and Technology) ร่วมกับ depa Thailand ใช้ SentencePiece tokenizer ที่ออกแบบมาสำหรับภาษาไทยโดยเฉพาะ

- License: Apache 2.0
- Dimensions: 768
- Max tokens: 416
- Cost: $0 (self-hosted)
- Vendor lock-in: 0
- Self-hostable: ✅
- เหมาะสำหรับ: Thai-only workloads

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/embedding-model/models/wangchanberta.py
benchmarks/embedding-model/base.py
```

---

## โครงสร้าง Code (`models/wangchanberta.py`)

### Class: `WangchanBERTaModel`

```python
class WangchanBERTaModel(BaseEmbeddingModel):
    MODEL_ID = "airesearch/wangchanberta-base-att-spm-uncased"

    def __init__(self)
    @property
    def meta(self) -> ModelMeta
    def _encode_raw(self, texts: list[str]) -> np.ndarray
```

---

## อธิบาย Code ทีละส่วน

### `__init__()` — ใช้ HuggingFace transformers โดยตรง

```python
def __init__(self) -> None:
    from transformers import AutoTokenizer, AutoModel
    self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_ID)
    self._model = AutoModel.from_pretrained(self.MODEL_ID)
    self._model.eval()  # inference mode — ปิด dropout
```

WangchanBERTa ใช้ `transformers` โดยตรง ไม่ผ่าน sentence-transformers (เพราะต้องการ manual mean pooling)

`model.eval()` — สำคัญ: ปิด dropout และ batch normalization ให้ consistent results

---

### `meta` property

```python
ModelMeta(
    name="WangchanBERTa",
    dimensions=768,       # BERT base hidden size
    max_tokens=416,       # ต่ำกว่า standard BERT 512 (สำรอง special tokens)
    cost_per_1m_tokens=0.0,
    vendor_lock_in=0,
    self_hostable=True,
)
```

---

### `_encode_raw()` — Manual Mean Pooling

```python
def _encode_raw(self, texts: list[str]) -> np.ndarray:
    import torch

    all_embeddings: list[np.ndarray] = []
    batch_size = 16

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        # 1. Tokenize
        encoded = self._tokenizer(
            batch,
            padding=True,        # pad สั้นให้เท่ากันใน batch
            truncation=True,
            max_length=416,
            return_tensors="pt",
        )

        # 2. Forward pass (ไม่คำนวณ gradient)
        with torch.no_grad():
            outputs = self._model(**encoded)
            # outputs.last_hidden_state: (batch, seq_len, 768)

        # 3. Mean Pooling — เฉลี่ย token embeddings (ไม่รวม padding)
        attention_mask = encoded["attention_mask"].unsqueeze(-1)  # (batch, seq, 1)
        token_embs = outputs.last_hidden_state                    # (batch, seq, 768)

        summed = (token_embs * attention_mask).sum(dim=1)         # (batch, 768)
        counts = attention_mask.sum(dim=1).clamp(min=1e-9)        # (batch, 1)
        mean_pooled = (summed / counts).numpy()                   # (batch, 768)

        all_embeddings.append(mean_pooled)

    return np.concatenate(all_embeddings, axis=0).astype(np.float32)
```

---

## Mean Pooling คืออะไร?

BERT คืนค่า hidden state สำหรับทุก token ใน sequence แต่ต้องการ **single vector** ต่อ sentence จึงต้องทำ pooling:

```
Input: "บริษัทมีนโยบายวันหยุดกี่วัน"
Tokens: [CLS] บริ ษัท มี นโย บาย วัน หยุด กี่ วัน [SEP] [PAD] [PAD]
Token embeddings: (13, 768)
Attention mask: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]  ← ไม่รวม PAD

Mean pooling:
  summed = sum(token_embs × mask) along seq dim = (768,)
  count  = sum(mask) = 11
  mean   = summed / 11 = (768,)  ← sentence embedding
```

`attention_mask × token_embs` → ไม่รวม padding tokens ในการเฉลี่ย

---

## ทำไมไม่ใช้ `[CLS]` token?

BERT-style models มักใช้ `[CLS]` token embedding เป็น sentence representation แต่ **WangchanBERTa** ไม่ได้ถูก fine-tune ให้ `[CLS]` มีความหมายระดับ sentence — mean pooling ให้ผลดีกว่า

---

## SentencePiece Tokenizer

WangchanBERTa ใช้ SentencePiece (SPM) tokenizer ที่ train บนข้อมูลไทยขนาดใหญ่:
- จัดการ Thai character segmentation ได้ดีกว่า WordPiece standard
- ไม่ต้องการ pre-tokenization (ภาษาไทยไม่มี space ระหว่างคำ)
- vocabulary 25,000 tokens เน้นภาษาไทย

---

## จุดเด่น / จุดด้อย

| จุดเด่น | จุดด้อย |
|--------|---------|
| Tokenizer ออกแบบมาสำหรับ Thai โดยเฉพาะ | Max 416 tokens — ไม่รองรับ document ยาว |
| ไม่มีค่า API | Dimensions 768 (น้อยกว่า 1024) |
| Apache 2.0 | ไม่ดีสำหรับ English |
| VISTEC/depa research quality | Inference ช้ากว่าเพราะ manual pooling |
| เหมาะกับ Thai-only use case | community เล็กกว่า BGE/E5 |

---

## ผลใน Benchmark (Phase 3)

- **Thai Recall:** สูงสำหรับ Thai-specific texts แต่จำกัดด้วย max_tokens 416
- **English Recall:** ต่ำ (ไม่ได้ออกแบบมาสำหรับ English)
- **Latency:** ช้าเพราะ manual batching + torch operations
- เหมาะสำหรับ: Thai-only document corpus ที่ไม่มีภาษาอังกฤษ
