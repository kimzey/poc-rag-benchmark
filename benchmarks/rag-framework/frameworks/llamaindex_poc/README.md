# LlamaIndex RAG Pipeline

## คืออะไร

LlamaIndex (เดิมชื่อ GPT Index) เป็น framework สำหรับสร้าง LLM applications โดยเน้นด้าน data ingestion และ retrieval ใช้ `SimpleDirectoryReader` โหลดเอกสาร, `VectorStoreIndex` สร้าง vector index อัตโนมัติ, และ `QueryEngine` รวม retrieve + generate ในขั้นตอนเดียว

- LOC: ~105 บรรทัด
- จุดเด่น: boilerplate น้อยที่สุด
- ข้อระวัง: ใช้ global `Settings` object

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/rag-framework/frameworks/llamaindex_poc/pipeline.py
benchmarks/rag-framework/base.py     # BaseRAGPipeline interface
benchmarks/rag-framework/config.py
```

---

## โครงสร้าง Code (`pipeline.py`)

### Class: `LlamaIndexRAGPipeline`

```python
class LlamaIndexRAGPipeline(BaseRAGPipeline):
    def __init__(self)
    def build_index(self, doc_paths: list[str]) -> IndexStats
    def query(self, question: str, top_k: int) -> RAGResult
```

---

## อธิบาย Code ทีละส่วน

### `__init__()` — Global Settings (⚠️ footgun)

```python
from llama_index.core import Settings

# Fix: LlamaIndex ตรวจสอบ model name กับ OpenAI API
# "openai/gpt-4o-mini" → "gpt-4o-mini"
llm_model_name = config.LLM_MODEL.split("/")[-1]

Settings.llm = LlamaOpenAI(
    model=llm_model_name,
    api_key=config.OPENROUTER_API_KEY,
    api_base=config.OPENROUTER_BASE_URL,
    temperature=0.1,
    max_tokens=512,
)

if config.EMBEDDING_MODEL.startswith("text-embedding"):
    Settings.embed_model = OpenAIEmbedding(model=..., api_key=...)
else:
    Settings.embed_model = HuggingFaceEmbedding(model_name=...)

Settings.chunk_size = config.CHUNK_SIZE
Settings.chunk_overlap = config.CHUNK_OVERLAP
```

**⚠️ ข้อระวัง Global State:** `Settings` เป็น singleton global object ถ้ารัน multiple pipelines พร้อมกัน จะ conflict กัน (race condition ใน multi-threaded)

**เหตุผล strip prefix:** LlamaIndex ต้องการชื่อ model ที่ OpenAI รู้จัก เช่น `"gpt-4o-mini"` ไม่ใช่ `"openai/gpt-4o-mini"` (format ของ OpenRouter)

---

### `build_index()` — Auto chunking + embedding

```python
def build_index(self, doc_paths: list[str]) -> IndexStats:
    t0 = time.perf_counter()

    # โหลดเอกสาร — รองรับ .txt, .md, .pdf, .docx อัตโนมัติ
    docs = SimpleDirectoryReader(input_files=doc_paths).load_data()

    # สร้าง vector index — chunk, embed, store ทำอัตโนมัติ
    self._index = VectorStoreIndex.from_documents(docs, show_progress=False)

    # สร้าง query engine พร้อม custom prompt
    self._query_engine = self._index.as_query_engine(
        similarity_top_k=config.TOP_K,
        text_qa_template=PromptTemplate(_RAG_PROMPT),
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    num_chunks = len(self._index.docstore.docs)  # นับ chunks จาก docstore
    return IndexStats(num_chunks=num_chunks, indexing_time_ms=elapsed_ms, framework=self.name)
```

**`SimpleDirectoryReader`:** โหลดไฟล์หลาย format อัตโนมัติ (ไม่ต้องเขียน loader เอง)

**`VectorStoreIndex.from_documents()`:** ทำ chunking + embedding + indexing ในบรรทัดเดียว ตาม `Settings.chunk_size` ที่กำหนดไว้

---

### `query()` — Single call retrieve + generate

```python
def query(self, question: str, top_k: int) -> RAGResult:
    t0 = time.perf_counter()

    response = self._query_engine.query(question)
    # ขั้นตอนใน query_engine:
    # 1. embed question
    # 2. retrieve top-k nodes
    # 3. build prompt
    # 4. call LLM
    # 5. return Response object

    sources = [n.metadata.get("file_path", "") for n in response.source_nodes]
    chunks  = [n.text for n in response.source_nodes]

    return RAGResult(
        answer=str(response),
        sources=sources,
        latency_ms=(time.perf_counter() - t0) * 1000,
        retrieved_chunks=chunks,
    )
```

Query engine รวม retrieve + generate ใน `.query()` call เดียว — สะดวกแต่ debug ยาก

`response.source_nodes` — list ของ `NodeWithScore` ที่ retrieve มา

---

### RAG Prompt Template

```
You are a helpful assistant. Answer using ONLY the provided context.
If the answer is not in the context, say 'ไม่พบข้อมูลในเอกสาร (No information found in documents).'

Context information is below.
---------------------
{context_str}
---------------------
Query: {query_str}
Answer:
```

LlamaIndex ใช้ `{context_str}` และ `{query_str}` เป็น placeholder (ต่างจาก `{context}`, `{question}` ของ frameworks อื่น)

---

## Data Flow

```
doc_paths
    ↓ SimpleDirectoryReader.load_data()
list[Document]
    ↓ VectorStoreIndex.from_documents()
    │  ├── chunk (ตาม Settings.chunk_size/overlap)
    │  ├── embed (ตาม Settings.embed_model)
    │  └── store ใน in-memory VectorStore
VectorStoreIndex + QueryEngine
    ↓ (query time)
question → query_engine.query()
    │  ├── embed question
    │  ├── retrieve top-k nodes
    │  ├── build prompt จาก PromptTemplate
    │  └── call LLM (Settings.llm)
Response (answer + source_nodes)
```

---

## ข้อดี / ข้อด้อย

| ข้อดี | ข้อด้อย |
|------|---------|
| Code น้อยที่สุด (~105 LOC) | Global `Settings` — ไม่ safe ใน concurrent |
| SimpleDirectoryReader รองรับหลาย format | Debug ยาก (retrieve + generate ซ่อนใน engine) |
| ระบบ node/chunk อัตโนมัติ | ต้อง strip model prefix (compat issue) |
| Abstraction สูง = ใช้งานง่าย | Version changes บ่อย (breaking changes) |
| ต่อยอด: graph index, multi-modal | |
