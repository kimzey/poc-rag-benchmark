# คู่มือเพิ่ม Adapter ใหม่

โปรเจคนี้ออกแบบเป็น **pluggable architecture** — ทุก component อยู่หลัง Abstract Base Class (ABC) ทำให้เพิ่มตัวเลือกใหม่ได้โดยไม่ต้องแก้โค้ดที่มีอยู่

---

## หลักการ: Port & Adapter Pattern

```
evaluate.py (runner)
      │
      ▼
  ABC Interface (base.py)       ← contract ที่ adapter ทุกตัวต้องทำตาม
      │
      ├── adapter_a.py          ← implementation ตัวที่ 1
      ├── adapter_b.py          ← implementation ตัวที่ 2
      └── new_adapter.py        ← ตัวใหม่ที่คุณจะเพิ่ม
```

**กฎสำคัญ:** Runner (`evaluate.py`) ไม่เคยเรียก adapter โดยตรง — เรียกผ่าน ABC เท่านั้น ทำให้ swap ได้โดยไม่แก้ runner

---

## 1. เพิ่ม Vector DB Adapter

### Base class: `VectorDBClient`

ไฟล์: `benchmarks/vector-db/clients/base.py`

```python
class VectorDBClient(ABC):
    DIM = 1536  # Match OpenAI text-embedding-3-small

    def connect(self) -> None: ...
    def create_collection(self, name: str) -> None: ...
    def insert(self, records: list[BenchmarkRecord]) -> None: ...
    def search(self, query_vector, top_k, filter=None) -> list[SearchResult]: ...
    def count(self) -> int: ...
    def drop_collection(self) -> None: ...
    @property
    def name(self) -> str: ...
```

### ขั้นตอน

**1. สร้างไฟล์ adapter**

```bash
# ตัวอย่าง: เพิ่ม Weaviate
touch benchmarks/vector-db/clients/weaviate.py
```

**2. Implement ทุก abstract method**

```python
# benchmarks/vector-db/clients/weaviate.py
from .base import VectorDBClient, BenchmarkRecord, SearchResult

class WeaviateClient(VectorDBClient):
    @property
    def name(self) -> str:
        return "weaviate"

    def connect(self) -> None:
        # เชื่อมต่อ Weaviate
        ...

    def create_collection(self, name: str) -> None:
        # สร้าง collection/class
        ...

    def insert(self, records: list[BenchmarkRecord]) -> None:
        # Batch insert vectors + metadata
        ...

    def search(self, query_vector, top_k=10, filter=None) -> list[SearchResult]:
        # ANN search with optional metadata filter
        ...

    def count(self) -> int:
        ...

    def drop_collection(self) -> None:
        ...
```

**3. Register ใน `__init__.py`**

```python
# benchmarks/vector-db/clients/__init__.py
from .weaviate import WeaviateClient
```

**4. เพิ่ม Docker service** (ถ้าต้อง run locally)

แก้ `docker/docker-compose.vector-db.yml`:

```yaml
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.25.0
    container_name: spike_weaviate
    ports:
      - "8080:8080"
    environment:
      - QUERY_DEFAULTS_LIMIT=25
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
```

**5. เพิ่ม dependency**

```bash
uv add --group bench-vectordb "weaviate-client>=4.5"
```

**6. ทดสอบ**

```bash
make up-db DB=weaviate
make benchmark-db DB=weaviate N=10000
```

---

## 2. เพิ่ม RAG Framework Adapter

### Base class: `BaseRAGPipeline`

ไฟล์: `benchmarks/rag-framework/base.py`

```python
class BaseRAGPipeline(ABC):
    @property
    def name(self) -> str: ...

    def build_index(self, doc_paths: list[str]) -> IndexStats:
        """Load, chunk, embed, and store documents."""
        ...

    def query(self, question: str, top_k: int = 3) -> RAGResult:
        """Embed query → retrieve → generate."""
        ...
```

### ขั้นตอน

**1. สร้าง directory**

```bash
mkdir -p benchmarks/rag-framework/frameworks/new_framework
touch benchmarks/rag-framework/frameworks/new_framework/__init__.py
touch benchmarks/rag-framework/frameworks/new_framework/pipeline.py
```

**2. Implement pipeline**

```python
# benchmarks/rag-framework/frameworks/new_framework/pipeline.py
from benchmarks.rag_framework.base import BaseRAGPipeline, RAGResult, IndexStats

class NewFrameworkPipeline(BaseRAGPipeline):
    @property
    def name(self) -> str:
        return "new_framework"

    def build_index(self, doc_paths: list[str]) -> IndexStats:
        # Load → chunk → embed → store
        ...

    def query(self, question: str, top_k: int = 3) -> RAGResult:
        # Embed → retrieve → generate
        ...
```

**3. Register + เพิ่ม deps**

```bash
uv add --group bench-rag "new-framework>=1.0"
```

**4. ทดสอบ**

```bash
make rag-eval-framework F=new_framework
```

---

## 3. เพิ่ม Embedding Model Adapter

### Base class: `BaseEmbeddingModel`

ไฟล์: `benchmarks/embedding-model/base.py`

```python
class BaseEmbeddingModel(ABC):
    @property
    def meta(self) -> ModelMeta: ...

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        """Encode texts → float32 array (len(texts), dims)."""
        ...
```

> **Note:** ไม่ต้อง implement `encode()` — base class จัดการ L2-normalization + timing ให้แล้ว ต้อง implement แค่ `_encode_raw()`

### ขั้นตอน

**1. สร้างไฟล์**

```bash
touch benchmarks/embedding-model/models/cohere_embed.py
```

**2. Implement**

```python
# benchmarks/embedding-model/models/cohere_embed.py
import numpy as np
from ..base import BaseEmbeddingModel, ModelMeta

class CohereEmbedModel(BaseEmbeddingModel):
    @property
    def meta(self) -> ModelMeta:
        return ModelMeta(
            name="Cohere embed-multilingual-v3.0",
            dimensions=1024,
            max_tokens=512,
            cost_per_1m_tokens=0.1,     # USD
            vendor_lock_in=7,            # 0-10 scale
            self_hostable=False,
        )

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        import cohere
        co = cohere.Client()
        response = co.embed(texts=texts, model="embed-multilingual-v3.0")
        return np.array(response.embeddings, dtype=np.float32)
```

**3. Register ใน `__init__.py`**

```python
# benchmarks/embedding-model/models/__init__.py
from .cohere_embed import CohereEmbedModel
```

**4. เพิ่ม deps + ทดสอบ**

```bash
uv add --group bench-embed "cohere>=5.0"
make embed-eval-model M=cohere_embed
```

---

## 4. เพิ่ม LLM Provider Adapter

### Base class: `BaseLLMProvider`

ไฟล์: `benchmarks/llm-provider/base.py`

```python
class BaseLLMProvider(ABC):
    @property
    def meta(self) -> ProviderMeta: ...

    def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
        """Returns (answer_text, input_tokens, output_tokens)."""
        ...
```

> **Note:** ไม่ต้อง implement `generate()` — base class จัดการ timing + cost calculation ให้แล้ว

### ขั้นตอน

**1. สร้างไฟล์**

```bash
touch benchmarks/llm-provider/providers/groq.py
```

**2. Implement**

```python
# benchmarks/llm-provider/providers/groq.py
from ..base import BaseLLMProvider, ProviderMeta

class GroqProvider(BaseLLMProvider):
    @property
    def meta(self) -> ProviderMeta:
        return ProviderMeta(
            name="Groq / Llama 3.1 70B",
            model_id="llama-3.1-70b-versatile",
            provider="groq",
            cost_per_1m_input=0.59,
            cost_per_1m_output=0.79,
            vendor_lock_in=3,
            self_hostable=False,
            openai_compatible=True,
        )

    def _generate_raw(self, prompt: str, context: str) -> tuple[str, int, int]:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
        # ... call API
        return (answer, input_tokens, output_tokens)
```

**3. Register + ทดสอบ**

```bash
uv add --group bench-llm "openai>=1.30"  # Groq uses OpenAI-compatible API
make llm-eval-provider P=groq
```

---

## Checklist สำหรับ Adapter ใหม่

- [ ] Implement ทุก abstract method จาก base class
- [ ] ใส่ `meta` / `name` property ให้ครบ
- [ ] Register ใน `__init__.py`
- [ ] เพิ่ม dependency ใน `pyproject.toml` (group ที่ตรง)
- [ ] ทดสอบ standalone ได้
- [ ] เพิ่ม env var ใน `.env.example` (ถ้ามี API key)
- [ ] Update `docs/phases/phase-*.md` ที่เกี่ยวข้อง
