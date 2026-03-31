# spike-rak — เอกสารประกอบโปรเจค

> **RAG Spike Research** — การวิจัยเชิงทดลองเพื่อเลือก Tech Stack สำหรับระบบ RAG ใน Production

---

## โปรเจคนี้คืออะไร?

`spike-rak` เป็น **Spike Research Project** ที่ทำขึ้นเพื่อประเมินและเปรียบเทียบ components ต่างๆ ที่จะใช้ในระบบ RAG (Retrieval-Augmented Generation) ก่อนนำไปใช้ใน Production จริง

**RAG คืออะไร?**  
RAG เป็นสถาปัตยกรรมที่ให้ LLM (AI) ตอบคำถามโดยอิงจากเอกสารที่เราใส่เข้าไป ไม่ใช่แค่ความรู้ที่ model เรียนมา — เหมาะสำหรับ internal knowledge base, FAQ bot, customer support ฯลฯ

**ทำไมต้องทำ Spike?**  
มี components ให้เลือกหลายตัวในแต่ละส่วน (Vector DB, Framework, Embedding Model ฯลฯ) แต่ละตัวมี trade-off ต่างกัน — Spike นี้จะทดลองจริงแล้วสรุปเป็น RFC เพื่อให้ทีมตัดสินใจร่วมกัน

---

## โครงสร้างโปรเจค

```
spike-rak/
├── api/                    ← Phase 4: FastAPI server (RAG API + Auth)
├── benchmarks/
│   ├── vector-db/          ← Phase 1: Vector DB benchmark scripts
│   ├── rag-framework/      ← Phase 2: RAG framework comparison
│   ├── embedding-model/    ← Phase 3: Embedding model evaluation
│   └── llm-provider/       ← Phase 3.5: LLM provider comparison
├── tests/
│   ├── integration/        ← Phase 5: End-to-end integration tests (7 scenarios)
│   └── load/               ← Phase 5: Locust load tests
├── docker/                 ← Docker Compose สำหรับ Vector DBs (Phase 1)
├── datasets/               ← Test datasets
├── docs/                   ← เอกสารนี้
│   ├── phases/             ← เอกสารแต่ละ Phase
│   └── guides/             ← คู่มือการใช้งาน
├── plan.md                 ← Research plan ฉบับเต็ม
├── SETUP.md                ← Setup & quick-start guide (ภาษาอังกฤษ)
├── pyproject.toml          ← Dependencies ทุก phase (จัดการโดย uv)
└── Makefile                ← คำสั่งลัดทุก phase
```

---

## 6 Phases ของการวิจัย

| Phase | หัวข้อ | เอกสาร |
|-------|--------|--------|
| Phase 1 | Vector Database Comparison | [phases/phase-1-vector-db.md](phases/phase-1-vector-db.md) |
| Phase 2 | RAG Framework Comparison | [phases/phase-2-rag-framework.md](phases/phase-2-rag-framework.md) |
| Phase 3 | Embedding Model Comparison | [phases/phase-3-embedding.md](phases/phase-3-embedding.md) |
| Phase 3.5 | LLM Provider Comparison | [phases/phase-3.5-llm-provider.md](phases/phase-3.5-llm-provider.md) |
| Phase 4 | API Layer & Authentication Design | [phases/phase-4-api-auth.md](phases/phase-4-api-auth.md) |
| Phase 5 | Integration Testing | [phases/phase-5-integration.md](phases/phase-5-integration.md) |
| Phase 6 | RFC Document & Knowledge Sharing | [phases/phase-6-rfc.md](phases/phase-6-rfc.md) |

---

## คู่มือการใช้งาน

| คู่มือ | เนื้อหา |
|--------|--------|
| [guides/quickstart.md](guides/quickstart.md) | ติดตั้ง + เริ่มต้นใช้งาน ทุก phase |
| [guides/api-usage.md](guides/api-usage.md) | วิธีใช้ API Server อย่างละเอียด (Phase 4) |
| [guides/benchmarking.md](guides/benchmarking.md) | วิธีรัน benchmark + อ่านผลลัพธ์ทุก phase |
| [guides/adding-adapters.md](guides/adding-adapters.md) | วิธีเพิ่ม adapter ใหม่ (Vector DB, Embedding, LLM, RAG) |
| [glossary.md](glossary.md) | คำศัพท์ RAG สำหรับทีม |

---

## เริ่มต้นอย่างรวดเร็ว

```bash
# 1. ติดตั้ง uv (ถ้ายังไม่มี)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Setup
cp .env.example .env
make setup

# 3. เลือก phase ที่ต้องการ
make install-api && make api-run          # Phase 4: API Server
make install-test && make test-integration # Phase 5: Integration Tests
make up-db && make install && make benchmark-quick  # Phase 1: Vector DB
```

ดูรายละเอียดเพิ่มเติมที่ [guides/quickstart.md](guides/quickstart.md)

---

## สิ่งที่ต้องการก่อนเริ่ม

| เครื่องมือ | เวอร์ชัน | จำเป็นสำหรับ |
|-----------|---------|------------|
| Python | ≥ 3.11 | ทุก phase |
| uv | ≥ 0.5 | ทุก phase |
| Docker | ใดก็ได้ | Phase 1 เท่านั้น |
| OPENROUTER_API_KEY | — | Phase 2, 3.5, 4 (optional) |
| OPENAI_API_KEY | — | Phase 3 OpenAI models (optional) |

---

## หลักการ Anti-Vendor-Lock-in

โปรเจคนี้ออกแบบโดยยึดหลัก **ไม่ผูกติดกับ vendor เดียว**:
- ทุก component อยู่หลัง interface — สามารถ swap ได้โดยแก้ config
- ทดสอบกับ ≥ 2 providers เสมอ เพื่อพิสูจน์ว่า swap ได้จริง
- ใช้ standard protocols (OpenAI-compatible API)
- Data format export/import ได้

ดูรายละเอียด architecture ใน [plan.md](../plan.md) หัวข้อ Section 4
