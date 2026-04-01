# Haystack v2 RAG Pipeline

## คืออะไร

Haystack (by deepset) เป็น framework ที่ออกแบบ RAG pipeline เป็น **DAG (Directed Acyclic Graph)** ของ components ที่เชื่อมต่อกันผ่าน named sockets ทุก connection ถูก validate ตอน build time — ทำให้ type-safe และ debug ง่ายกว่า framework อื่น

- LOC: ~175 บรรทัด (verbose ที่สุด)
- จุดเด่น: explicit wiring, type-safe, DAG visualizable
- Vector store: InMemoryDocumentStore
- Prompt: Jinja2 template

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/rag-framework/frameworks/haystack_poc/pipeline.py
benchmarks/rag-framework/base.py     # BaseRAGPipeline interface
benchmarks/rag-framework/config.py
```

---

## โครงสร้าง Code (`pipeline.py`)

### Class: `HaystackRAGPipeline`

```python
class HaystackRAGPipeline(BaseRAGPipeline):
    def __init__(self)
    def build_index(self, doc_paths: list[str]) -> IndexStats
    def query(self, question: str, top_k: int) -> RAGResult

    # Private helper
    def _chunk_text(self, text: str) -> list[str]
```

---

## อธิบาย Code ทีละส่วน

### `__init__()` — Document store + Document Embedder

```python
from haystack.document_stores.in_memory import InMemoryDocumentStore

self._doc_store = InMemoryDocumentStore()
self._use_openai_embed = config.EMBEDDING_MODEL.startswith("text-embedding")

if self._use_openai_embed:
    from haystack.components.embedders import OpenAIDocumentEmbedder
    self._doc_embedder = OpenAIDocumentEmbedder(
        model=config.EMBEDDING_MODEL,
        api_key=Secret.from_token(config.OPENAI_API_KEY),
    )
else:
    from haystack.components.embedders import SentenceTransformersDocumentEmbedder
    self._doc_embedder = SentenceTransformersDocumentEmbedder(
        model=config.EMBEDDING_MODEL, progress_bar=False
    )
    self._doc_embedder.warm_up()  # โหลด model เข้า memory ล่วงหน้า
```

Haystack แยก **document embedder** (ใช้ตอน index) กับ **text embedder** (ใช้ตอน query) ออกจากกัน

`warm_up()` — สำหรับ sentence-transformers ต้องเรียกก่อนใช้ (โหลด weights)

**Compatibility fix:** code นี้มี workaround สำหรับ `openai` 1.71 ที่ยังไม่มี `ChatCompletionMessageCustomToolCall`:
```python
try:
    from openai.types.chat import ChatCompletionMessageCustomToolCall as _
except ImportError:
    import openai.types.chat as _oai_chat
    _oai_chat.ChatCompletionMessageCustomToolCall = ChatCompletionMessageToolCall
```

---

### `build_index()` — Embed documents + Build DAG pipeline

```python
# 1. สร้าง Haystack Document objects จาก chunks
raw_docs: list[Document] = []
for path in doc_paths:
    text = Path(path).read_text(encoding="utf-8")
    for i, chunk in enumerate(self._chunk_text(text)):
        raw_docs.append(
            Document(content=chunk, meta={"source": str(path), "chunk_id": i})
        )

# 2. Embed documents และเขียนลง document store
embedded_docs = self._doc_embedder.run(raw_docs)["documents"]
self._doc_store.write_documents(embedded_docs)

# 3. สร้าง query pipeline (DAG)
self._pipeline = Pipeline()

# เพิ่ม components
self._pipeline.add_component("embedder", query_embedder)
self._pipeline.add_component("retriever",
    InMemoryEmbeddingRetriever(document_store=self._doc_store, top_k=config.TOP_K)
)
self._pipeline.add_component("prompt_builder",
    PromptBuilder(template=_PROMPT_TEMPLATE)  # Jinja2 template
)
self._pipeline.add_component("llm",
    OpenAIGenerator(
        model=config.LLM_MODEL,
        api_key=Secret.from_token(config.OPENROUTER_API_KEY),
        api_base_url=config.OPENROUTER_BASE_URL,
        generation_kwargs={"temperature": 0.1, "max_tokens": 512},
    )
)

# 4. Connect sockets — DAG edges
self._pipeline.connect("embedder.embedding", "retriever.query_embedding")
self._pipeline.connect("retriever.documents", "prompt_builder.documents")
self._pipeline.connect("prompt_builder.prompt", "llm.prompt")
```

**DAG Structure:**
```
embedder ──(embedding)──→ retriever ──(documents)──→ prompt_builder ──(prompt)──→ llm
```

`pipeline.connect("A.output_socket", "B.input_socket")` — explicit wiring ตาม socket names ที่ defined ใน component แต่ละตัว

---

### Pipeline Socket Connections

| From | Socket | To | Socket |
|------|--------|----|--------|
| embedder | embedding | retriever | query_embedding |
| retriever | documents | prompt_builder | documents |
| prompt_builder | prompt | llm | prompt |

Haystack validate connections ตอน `build()` — ถ้า socket type ไม่ match จะ error ทันที

---

### `query()` — Run DAG pipeline

```python
def query(self, question: str, top_k: int) -> RAGResult:
    t0 = time.perf_counter()

    result = self._pipeline.run(
        {
            "embedder": {"text": question},        # input ไปยัง embedder
            "prompt_builder": {"question": question},  # input ไปยัง prompt_builder
        },
        include_outputs_from={"retriever"},  # ขอ intermediate output จาก retriever ด้วย
    )

    answer = (result.get("llm") or {}).get("replies", [""])[0]
    retrieved_docs = (result.get("retriever") or {}).get("documents", [])
    sources = [d.meta.get("source", "") for d in retrieved_docs]
    chunks  = [d.content for d in retrieved_docs]

    return RAGResult(answer=answer, sources=sources, latency_ms=..., retrieved_chunks=chunks)
```

`pipeline.run(inputs)` — dict ของ `{component_name: {socket_name: value}}`

`include_outputs_from={"retriever"}` — ปกติ Haystack คืนแค่ output ของ leaf nodes (llm) ถ้าต้องการ intermediate results ต้องระบุ component name นี้

---

### RAG Prompt (Jinja2 Template)

```jinja2
You are a helpful assistant. Answer using ONLY the context below.
If the answer is not in the context, say "ไม่พบข้อมูลในเอกสาร (No information found in documents)."

Context:
{% for doc in documents %}
{{ doc.content }}
{% endfor %}

Question: {{ question }}

Answer:
```

Haystack ใช้ **Jinja2** template (ต่างจาก framework อื่น) — รองรับ for loops, conditionals ใน prompt

---

## Data Flow

```
doc_paths → chunk → Document objects
    ↓ doc_embedder.run()
embedded Documents (with embedding field)
    ↓ doc_store.write_documents()
InMemoryDocumentStore
                        ↓ (build query pipeline)
                    Pipeline DAG (4 components, 3 edges)
                        ↓ (query time)
question → pipeline.run({
    "embedder": {"text": question},
    "prompt_builder": {"question": question}
})
    ├── embedder: text → embedding vector
    ├── retriever: embedding → top-k Documents
    ├── prompt_builder: documents + question → prompt string
    └── llm: prompt → replies list
result dict → extract answer + retrieved_docs
```

---

## ข้อดี / ข้อด้อย

| ข้อดี | ข้อด้อย |
|------|---------|
| Type-safe connections — validate ตอน build | Verbose ที่สุด (~175 LOC) |
| DAG visualizable (`pipeline.draw()`) | Learning curve สูงกว่า |
| Intermediate outputs inspect ได้ | ต้องแยก doc_embedder / text_embedder |
| Jinja2 template ยืดหยุ่น | `warm_up()` ต้องเรียก manual |
| Component-based — swap ง่าย | `include_outputs_from` ต้องระบุ explicit |
| ไม่มี global state (ต่างจาก LlamaIndex) | compat workaround กับ openai library |
