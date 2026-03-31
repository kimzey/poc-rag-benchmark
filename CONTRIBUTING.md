# Contributing

คู่มือสำหรับทีมที่ต้องการ contribute หรือเพิ่ม component ใหม่เข้าไปใน spike

---

## Setup สำหรับ Development

```bash
# 1. Clone + setup
git clone <repo-url>
cd spike-rak
cp .env.example .env
make setup

# 2. ติดตั้ง deps ตาม phase ที่จะทำงาน
make install-api         # ถ้าจะแก้ API
make install-test        # ถ้าจะเขียน tests
uv sync --all-groups     # ถ้าต้องการทุกอย่าง (หนัก ~3GB)
```

---

## Dependency Management

ใช้ `uv` เท่านั้น — ไม่ใช้ pip หรือ poetry

```bash
# เพิ่ม dependency ใหม่เข้า group
uv add --group api "httpx>=0.28"
uv add --group test "pytest-cov>=5.0"

# Sync หลังจากแก้ pyproject.toml
uv sync --group <group-name>

# อย่าลืม commit uv.lock
git add pyproject.toml uv.lock
```

**Dependency groups:**
- `bench-vectordb` — Phase 1
- `bench-rag` — Phase 2
- `bench-embed` — Phase 3
- `bench-llm` — Phase 3.5
- `api` — Phase 4
- `test` — Phase 5 (auto-includes `api`)

---

## วิธีเพิ่ม Adapter ใหม่

โปรเจคออกแบบเป็น pluggable — ทุก component อยู่หลัง ABC ดูรายละเอียดเต็มที่ [`docs/guides/adding-adapters.md`](docs/guides/adding-adapters.md)

### สรุปสั้น

1. **Vector DB** — implement `VectorDBClient` ใน `benchmarks/vector-db/clients/`
2. **RAG Framework** — implement `BaseRAGPipeline` ใน `benchmarks/rag-framework/frameworks/`
3. **Embedding Model** — implement `BaseEmbeddingModel` ใน `benchmarks/embedding-model/models/`
4. **LLM Provider** — implement `BaseLLMProvider` ใน `benchmarks/llm-provider/providers/`

ทุกอันต้อง:
- Implement abstract methods ทั้งหมดจาก base class
- ใส่ metadata / meta property ให้ครบ
- Register ใน `__init__.py` ของ directory นั้น
- เพิ่ม deps ใน `pyproject.toml` (ถ้ามี)

---

## รัน Tests ก่อน Commit

```bash
make install-test
make test-integration

# ทดสอบ scenario เดียว
uv run pytest tests/integration/ -v -k "TestScenario1"
```

---

## Commit Convention

ใช้ format:

```
<type>: <short description>

<optional body>
```

Types:
- `feat` — เพิ่ม feature / adapter ใหม่
- `fix` — แก้ bug
- `docs` — แก้เอกสาร
- `bench` — เพิ่ม/แก้ benchmark
- `test` — เพิ่ม/แก้ tests
- `refactor` — refactor โดยไม่เปลี่ยน behavior
- `chore` — อื่นๆ (deps, config)

ตัวอย่าง:
```
feat: add Weaviate vector DB adapter
bench: add 500K vector benchmark scenario
docs: update Phase 1 results in RFC
```

---

## โครงสร้างที่ต้องรู้

```
benchmarks/<category>/
├── base.py              ← ABC ที่ adapter ต้อง implement
├── config.py            ← configuration / constants
├── evaluate.py          ← script หลักรัน evaluation
├── <implementations>/   ← adapter แต่ละตัว
│   ├── __init__.py
│   └── *.py
└── results/             ← output JSON (gitignored)

api/
├── auth/                ← JWT + RBAC + permissions
├── rag/                 ← retrieval + pipeline + models
├── routes/              ← FastAPI routers
├── store.py             ← in-memory stores (PoC)
└── main.py              ← app entry point
```

---

## แก้เอกสาร

- เอกสารหลักอยู่ใน `docs/`
- Phase docs: `docs/phases/phase-*.md`
- Guides: `docs/guides/*.md`
- ADRs: `docs/adr/ADR-*.md` — ใช้ format ที่มีอยู่
- RFC: `docs/rfc/RFC-001-rag-tech-stack.md` — กรอก [TODO] sections หลัง benchmark เสร็จ

---

## เพิ่ม Docker Service (Phase 1)

ถ้าจะเพิ่ม Vector DB ตัวใหม่:

1. เพิ่ม service ใน `docker/docker-compose.vector-db.yml`
2. สร้าง client adapter ใน `benchmarks/vector-db/clients/`
3. เพิ่ม deps ใน `pyproject.toml` group `bench-vectordb`
4. Register ใน `benchmarks/vector-db/clients/__init__.py`
5. ทดสอบ: `make up-db DB=<name> && make benchmark-db DB=<name>`
