# LangChain RAG Pipeline

## คืออะไร

LangChain เป็น framework สำหรับสร้าง LLM applications โดยเน้นความยืดหยุ่นในการ compose components ผ่าน "chains" ใช้ `TextLoader` โหลดเอกสาร, `RecursiveCharacterTextSplitter` chunk, `FAISS` เป็น in-memory vector store, และ `RetrievalQA` chain เชื่อม retrieve + generate

- LOC: ~125 บรรทัด
- จุดเด่น: ecosystem ใหญ่, composable (LCEL)
- index ที่ใช้: FAISS in-memory

---

## ไฟล์ที่เกี่ยวข้อง

```
benchmarks/rag-framework/frameworks/langchain_poc/pipeline.py
benchmarks/rag-framework/base.py     # BaseRAGPipeline interface
benchmarks/rag-framework/config.py
```

---

## โครงสร้าง Code (`pipeline.py`)

### Class: `LangChainRAGPipeline`

```python
class LangChainRAGPipeline(BaseRAGPipeline):
    def __init__(self)
    def build_index(self, doc_paths: list[str]) -> IndexStats
    def query(self, question: str, top_k: int) -> RAGResult
```

---

## อธิบาย Code ทีละส่วน

### `__init__()` — เลือก embedding + LLM

```python
if config.EMBEDDING_MODEL.startswith("text-embedding"):
    from langchain_openai import OpenAIEmbeddings
    self._embeddings = OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL, openai_api_key=config.OPENAI_API_KEY
    )
else:
    from langchain_huggingface import HuggingFaceEmbeddings
    self._embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

self._llm = ChatOpenAI(
    model=config.LLM_MODEL,
    openai_api_key=config.OPENROUTER_API_KEY,
    openai_api_base=config.OPENROUTER_BASE_URL,  # OpenRouter endpoint
    temperature=0.1,
    max_tokens=512,
)

self._vectorstore = None
self._chain = None
```

LangChain ใช้ `openai_api_base` override เพื่อชี้ไป OpenRouter (OpenAI-compatible endpoint)

---

### `build_index()` — Load → Split → Embed → Store → Chain

```python
# 1. Text splitter — character-based recursive
splitter = RecursiveCharacterTextSplitter(
    chunk_size=config.CHUNK_SIZE,    # 500 characters (ไม่ใช่ words!)
    chunk_overlap=config.CHUNK_OVERLAP,
)

# 2. โหลดเอกสาร
docs = []
for path in doc_paths:
    loader = TextLoader(path, encoding="utf-8")
    docs.extend(loader.load())

# 3. Split documents
chunks = splitter.split_documents(docs)

# 4. สร้าง FAISS vector store
self._vectorstore = FAISS.from_documents(chunks, self._embeddings)

# 5. สร้าง prompt template
prompt = PromptTemplate(
    template=_PROMPT_TEMPLATE,
    input_variables=["context", "question"],
)

# 6. สร้าง RetrievalQA chain (legacy API)
self._chain = RetrievalQA.from_chain_type(
    llm=self._llm,
    chain_type="stuff",        # "stuff" = ใส่ทุก chunk ใน prompt ทีเดียว
    retriever=self._vectorstore.as_retriever(
        search_kwargs={"k": config.TOP_K}
    ),
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=True,
)
```

**`RecursiveCharacterTextSplitter`:** แตกต่างจาก Bare Metal — split ด้วย **characters** ไม่ใช่ words, ลอง split ด้วย `["\n\n", "\n", " ", ""]` ตามลำดับ

**`FAISS`:** Facebook AI Similarity Search — fast in-memory ANN, เร็วกว่า numpy linear scan แต่ไม่ต้องมี server

**`chain_type="stuff"`:** เอา retrieved chunks ทั้งหมด "stuff" เข้าไปใน single prompt (เหมาะสำหรับ top_k ไม่มาก)

---

### Legacy Chain vs LCEL (Modern API)

```python
# Legacy (ที่ใช้ใน code นี้) — ยังทำงานได้ แต่ deprecated
self._chain = RetrievalQA.from_chain_type(...)

# LCEL (modern) — pipe syntax, composable
# chain = vectorstore.as_retriever() | prompt | llm
```

Code นี้ใช้ Legacy API เพราะเข้าใจง่ายกว่า แต่ LCEL เป็น recommended approach ใน production

---

### `query()` — Chain invoke

```python
def query(self, question: str, top_k: int) -> RAGResult:
    t0 = time.perf_counter()

    result = self._chain.invoke({"query": question})
    # chain ทำ: embed question → FAISS search → build prompt → LLM → parse

    sources = [doc.metadata.get("source", "") for doc in result["source_documents"]]
    chunks  = [doc.page_content for doc in result["source_documents"]]

    return RAGResult(
        answer=result["result"],
        sources=sources,
        latency_ms=(time.perf_counter() - t0) * 1000,
        retrieved_chunks=chunks,
    )
```

`result["result"]` — คำตอบจาก LLM
`result["source_documents"]` — list ของ `Document` ที่ retrieve มา (ได้เพราะ `return_source_documents=True`)

---

### RAG Prompt Template

```
You are a helpful assistant. Answer using ONLY the context below.
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
    ↓ TextLoader.load()
list[Document] (with metadata: source, etc.)
    ↓ RecursiveCharacterTextSplitter.split_documents()
list[Document] chunks
    ↓ FAISS.from_documents(chunks, embeddings)
FAISS vector store (in-memory)
    ↓ (build RetrievalQA chain)
chain object
    ↓ (query time)
question → chain.invoke({"query": question})
    │  ├── embed question
    │  ├── FAISS similarity search (top-k)
    │  ├── format prompt
    │  └── LLM generate
result dict {"result": str, "source_documents": [...]}
```

---

## ข้อดี / ข้อด้อย

| ข้อดี | ข้อด้อย |
|------|---------|
| Ecosystem ใหญ่มาก (integrations หลายร้อยตัว) | API เปลี่ยนบ่อย (legacy → LCEL) |
| LCEL pipe syntax ยืดหยุ่น | `RetrievalQA` deprecated ใน version ใหม่ |
| FAISS เร็ว ไม่ต้อง server | `chunk_size` เป็น characters (อาจสับสน) |
| Source tracking ดี | หลาย abstraction layer ทำให้ debug ยาก |
| `return_source_documents=True` ง่าย | |
