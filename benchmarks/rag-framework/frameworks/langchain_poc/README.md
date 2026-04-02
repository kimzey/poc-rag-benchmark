# LangChain RAG Pipeline

## คืออะไร

LangChain เป็น framework สำหรับสร้าง LLM applications โดยเน้นความยืดหยุ่นในการ compose components ผ่าน LCEL (LangChain Expression Language) ใช้ `TextLoader` โหลดเอกสาร, `RecursiveCharacterTextSplitter` chunk, `FAISS` เป็น in-memory vector store, และ LCEL pipe chain เชื่อม retrieve + generate

- LOC: ~100 บรรทัด
- จุดเด่น: ecosystem ใหญ่, LCEL composable, source tracking
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
        model=config.EMBEDDING_MODEL,
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,  # OpenRouter endpoint
    )
else:
    from langchain_huggingface import HuggingFaceEmbeddings
    self._embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

self._llm = ChatOpenAI(
    model=config.LLM_MODEL,
    api_key=config.OPENROUTER_API_KEY,
    base_url=config.OPENROUTER_BASE_URL,
    temperature=0.1,
    max_tokens=512,
)
```

> `base_url` / `api_key` เป็น parameter ใหม่ (LangChain ≥ 0.2) แทน `openai_api_base` / `openai_api_key` แบบเก่า

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

# 5. สร้าง retriever + prompt
retriever = self._vectorstore.as_retriever(search_kwargs={"k": config.TOP_K})
prompt = PromptTemplate.from_template(_PROMPT_TEMPLATE)

# 6. LCEL chain — pattern จาก official LangChain docs
chain_from_docs = (
    RunnablePassthrough.assign(context=lambda x: _format_docs(x["context"]))
    | prompt
    | self._llm
    | StrOutputParser()
)
self._chain = RunnableParallel(
    context=retriever,
    question=RunnablePassthrough(),
).assign(answer=chain_from_docs)
```

**`RecursiveCharacterTextSplitter`:** split ด้วย **characters** ไม่ใช่ words, ลอง split ด้วย `["\n\n", "\n", " ", ""]` ตามลำดับ

**`FAISS`:** Facebook AI Similarity Search — fast in-memory ANN, เร็วกว่า numpy linear scan แต่ไม่ต้องมี server

**`langchain_text_splitters`:** package แยกใหม่ (LangChain ≥ 0.2) แทน `langchain.text_splitter` เก่า

---

### LCEL Chain (Modern API)

```
question
    ↓
RunnableParallel ──┬── context: retriever → [Document, ...]
                  └── question: passthrough → "..."
    ↓
.assign(answer=chain_from_docs)
    ↓
RunnablePassthrough.assign(context=format_docs)   ← join docs เป็น string
    ↓ prompt
PromptTemplate → "Context: ...\n\nQuestion: ..."
    ↓ llm
ChatOpenAI → AIMessage
    ↓ parser
StrOutputParser → "answer string"
```

**ทำไมต้องแบ่งเป็น 2 chain:**
- `RunnableParallel` เก็บ `context` เป็น `list[Document]` ไว้เพื่อดึง source metadata
- `chain_from_docs` รับ context ที่ format เป็น string แล้วส่งเข้า prompt

---

### `query()` — Chain invoke

```python
def query(self, question: str, top_k: int = config.TOP_K) -> RAGResult:
    t0 = time.perf_counter()

    result = self._chain.invoke(question)
    # result = {"context": [Document, ...], "question": "...", "answer": "..."}

    sources = [doc.metadata.get("source", "") for doc in result["context"]]
    chunks  = [doc.page_content for doc in result["context"]]

    return RAGResult(
        answer=result["answer"],
        sources=sources,
        latency_ms=(time.perf_counter() - t0) * 1000,
        retrieved_chunks=chunks,
    )
```

`result["answer"]` — คำตอบจาก LLM (ผ่าน `StrOutputParser` แล้ว เป็น plain string)
`result["context"]` — `list[Document]` ที่ retrieve มา (เก็บไว้ใน `RunnableParallel`)

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

## Package Imports (LangChain ≥ 0.2)

| สิ่งที่ใช้ | Package | หมายเหตุ |
|---|---|---|
| `RecursiveCharacterTextSplitter` | `langchain_text_splitters` | แยกออกจาก `langchain` แล้ว |
| `PromptTemplate` | `langchain_core.prompts` | ย้ายมาจาก `langchain.prompts` |
| `RunnableParallel`, `RunnablePassthrough` | `langchain_core.runnables` | LCEL core |
| `StrOutputParser` | `langchain_core.output_parsers` | parse AIMessage → str |
| `TextLoader`, `FAISS` | `langchain_community` | third-party integrations |
| `ChatOpenAI`, `OpenAIEmbeddings` | `langchain_openai` | OpenAI-specific |
| `HuggingFaceEmbeddings` | `langchain_huggingface` | HF-specific |

---

## ข้อดี / ข้อด้อย

| ข้อดี | ข้อด้อย |
|------|---------|
| Ecosystem ใหญ่มาก (integrations หลายร้อยตัว) | API เปลี่ยนบ่อย (legacy → LCEL) |
| LCEL pipe syntax ยืดหยุ่น composable | หลาย abstraction layer ทำให้ debug ยาก |
| FAISS เร็ว ไม่ต้อง server | `chunk_size` เป็น characters (อาจสับสน) |
| Source tracking ผ่าน `RunnableParallel` | setup chain ซับซ้อนกว่า bare metal |
| `StrOutputParser` จัดการ output format ให้ | |
