# Bare Metal RAG — Hand-rolled Pipeline

## คืออะไร

Bare Metal เป็นการ implement RAG pipeline โดยไม่ใช้ framework ใดเลย เขียนทุก step ด้วย Python/numpy โดยตรง จุดประสงค์คือเป็น **baseline** วัดว่าต้องใช้ code เท่าไรถ้าไม่มี abstraction layer

- Framework: ไม่มี (pure Python + numpy)
- Embedding: sentence-transformers หรือ OpenAI API
- LLM: OpenRouter (OpenAI-compatible)
- Vector store: numpy array ใน memory
- LOC: ~130 บรรทัด

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/rag-framework/frameworks/bare_metal/pipeline.py
benchmarks/rag-framework/base.py     # BaseRAGPipeline interface
benchmarks/rag-framework/config.py   # configuration
```

---

## โครงสร้าง Code (`pipeline.py`)

### Class: `BareMetalRAGPipeline`

```python
class BareMetalRAGPipeline(BaseRAGPipeline):
    def __init__(self)
    def build_index(self, doc_paths: list[str]) -> IndexStats
    def query(self, question: str, top_k: int) -> RAGResult

    # Private helpers
    def _embed(self, texts: list[str]) -> np.ndarray
    def _chunk_text(self, text: str) -> list[str]
```

---

## อธิบาย Code ทีละส่วน

### `__init__()` — เลือก embedding backend

```python
if _is_openai_model(config.EMBEDDING_MODEL):
    self._openai_embed = OpenAI(api_key=config.OPENAI_API_KEY)
else:
    from sentence_transformers import SentenceTransformer
    self._embedder = SentenceTransformer(config.EMBEDDING_MODEL)

# LLM ผ่าน OpenRouter (OpenAI-compatible endpoint)
self._llm = OpenAI(
    api_key=config.OPENROUTER_API_KEY,
    base_url=config.OPENROUTER_BASE_URL,
)

self._chunks: list[str] = []       # เก็บ text chunks
self._sources: list[str] = []      # เก็บ source path ต่อ chunk
self._embeddings: np.ndarray = None # matrix (n_chunks, dims)
```

---

### `_chunk_text()` — Word-based Sliding Window

```python
def _chunk_text(self, text: str) -> list[str]:
    words = text.split()              # split ด้วย whitespace
    step = CHUNK_SIZE - CHUNK_OVERLAP  # 500 - 50 = 450 words per step
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + CHUNK_SIZE]))
        i += step
    return chunks
```

- Chunk ด้วยคำ (word tokens) ไม่ใช่ character
- Sliding window ด้วย step = 450 คำ, overlap = 50 คำ (context continuity)
- **ข้อจำกัด:** `split()` ไม่รองรับ Thai word segmentation — ภาษาไทยจะถูกตัดที่ space

---

### `_embed()` — Encode texts to vectors

```python
def _embed(self, texts: list[str]) -> np.ndarray:
    if self._openai_embed is not None:
        resp = self._openai_embed.embeddings.create(
            model=config.EMBEDDING_MODEL, input=texts
        )
        vecs = np.array([d.embedding for d in resp.data], dtype=np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.where(norms == 0, 1, norms)  # L2-normalize
    
    return self._embedder.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,  # sentence-transformers normalize ให้
        batch_size=32,
    )
```

สลับระหว่าง OpenAI API และ sentence-transformers ขึ้นอยู่กับ `EMBEDDING_MODEL` config

---

### `build_index()` — โหลดเอกสาร + สร้าง embedding matrix

```python
def build_index(self, doc_paths: list[str]) -> IndexStats:
    t0 = time.perf_counter()
    self._chunks = []
    self._sources = []

    for path in doc_paths:
        text = Path(path).read_text(encoding="utf-8")
        chunks = self._chunk_text(text)
        self._chunks.extend(chunks)
        self._sources.extend([str(path)] * len(chunks))  # track source ต่อ chunk

    self._embeddings = self._embed(self._chunks)  # shape: (n_chunks, dims)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return IndexStats(num_chunks=len(self._chunks), indexing_time_ms=elapsed_ms, framework=self.name)
```

Vector store = numpy array ใน memory ไม่มี external dependency

---

### `query()` — Cosine similarity ด้วย numpy dot product

```python
def query(self, question: str, top_k: int) -> RAGResult:
    t0 = time.perf_counter()

    # 1. Embed query
    q_emb = self._embed([question])[0]  # shape: (dims,)

    # 2. Cosine similarity = dot product ของ L2-normalized vectors
    scores = self._embeddings @ q_emb   # shape: (n_chunks,)

    # 3. Top-k chunks
    top_idx = np.argsort(scores)[::-1][:top_k]
    retrieved = [self._chunks[i] for i in top_idx]
    sources   = [self._sources[i] for i in top_idx]

    # 4. สร้าง context string
    context = "\n\n---\n\n".join(retrieved)

    # 5. Generate ด้วย LLM
    prompt = _RAG_PROMPT.format(context=context, question=question)
    response = self._llm.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=512,
    )
    answer = response.choices[0].message.content or ""

    return RAGResult(answer=answer, sources=sources, latency_ms=..., retrieved_chunks=retrieved)
```

**Cosine similarity trick:** เมื่อ L2-normalize vectors แล้ว dot product = cosine similarity

---

### RAG Prompt

```
You are a helpful assistant. Answer the question using ONLY the context below.
If the answer is not in the context, say "ไม่พบข้อมูลในเอกสาร (No information found in documents)."

Context:
{context}

Question: {question}

Answer:
```

---

## Data Flow

```
doc_paths
    ↓ read_text()
raw text
    ↓ _chunk_text()
list[str] chunks (500 words, overlap 50)
    ↓ _embed()
np.ndarray (n_chunks × dims)  ← stored as self._embeddings
                                                ↓ (at query time)
question → _embed() → q_emb (1 × dims)
                ↓ matrix multiply (@)
scores (n_chunks,) → argsort → top-k indices
                ↓
context string → LLM prompt → answer
```

---

## ข้อดี / ข้อด้อย

| ข้อดี | ข้อด้อย |
|------|---------|
| ควบคุมได้ทุกขั้นตอน 100% | ต้องเขียน code เองทุกอย่าง |
| Debug ง่าย ไม่มี magic | ไม่มี caching, persistence |
| ไม่มี framework version conflicts | Thai chunking ไม่ดี (ไม่มี word segmentation) |
| เข้าใจง่ายสำหรับคนใหม่ | ใช้งาน production ไม่ได้ |
| numpy cosine sim O(n×d) — เหมาะ dataset เล็ก | Linear scan ช้าเมื่อ corpus ใหญ่ |
