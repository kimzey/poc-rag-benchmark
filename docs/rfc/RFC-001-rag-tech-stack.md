# RFC-001: RAG System Tech Stack Selection

| ฟิลด์ | ค่า |
|------|-----|
| **RFC ID** | RFC-001 |
| **ชื่อ** | RAG System Tech Stack Selection |
| **สถานะ** | 🟠 In Review |
| **ผู้เขียน** | Engineering Team |
| **วันที่สร้าง** | 2026-03-31 |
| **วันที่ update ล่าสุด** | 2026-04-01 |
| **Target audience** | Engineering Team, พี่ตั๊ก (Senior), Stakeholders |
| **Reviewers** | — |
| **Decision deadline** | — |

> **สถานะ key:**  
> 🟡 Draft — กำลังเขียน  
> 🟠 In Review — รอ feedback  
> 🟢 Accepted — ตัดสินใจแล้ว  
> 🔴 Rejected — ไม่เลือก  
> ⚫ Superseded — แทนที่ด้วย RFC อื่น

---

## 1. Executive Summary

จากการ spike ครบ 4 phases (Vector DB, RAG Framework, Embedding Model, LLM Provider) เราแนะนำ stack ดังนี้:

- เลือก **Qdrant** เป็น Vector DB เพราะ recall@10 สูงสุด (0.896) และ filtered latency ดีเยี่ยม (p50=6.28ms) — สำคัญมากสำหรับ permission-based retrieval
- เลือก **LlamaIndex** เป็น RAG framework เพราะ LOC น้อยสุด (84 lines) ในขณะที่ให้ abstraction สำหรับ component swap ตาม anti-lock-in policy
- เลือก **multilingual-e5-large** เป็น embedding model เพราะ recall = 1.0 ทั้งภาษาไทยและอังกฤษ, ฟรี, self-hostable — ไม่มี gap ระหว่าง open-source กับ OpenAI ในมิติ recall
- LLM strategy: ใช้ **Gemini 2.0 Flash** ผ่าน **OpenRouter** — weighted score สูงสุด (0.8686), Thai F1 ดีที่สุด, ราคาถูก ($0.31/1K queries), lock-in ต่ำ
- Trade-off หลักที่ยอมรับ: self-host embedding model บน CPU (ไม่มี GPU), ใช้ OpenRouter เป็น gateway เพิ่มหนึ่งชั้น dependency

---

## 2. Problem Statement

### 2.1 บริบท

เราต้องการสร้างระบบ RAG (Retrieval-Augmented Generation) สำหรับ production เพื่อให้พนักงานและลูกค้าสามารถถามคำถามเกี่ยวกับ knowledge base ภายในองค์กร และได้รับคำตอบที่แม่นยำจากเอกสารจริง

ปัจจุบันผู้ใช้ต้องค้นหาเอกสารเองด้วยตนเอง ซึ่ง:
- ใช้เวลามาก
- ได้ข้อมูลที่อาจ outdated
- ต้องรู้จะหาที่ไหน

### 2.2 Requirements หลัก

**Functional:**
- ตอบคำถามจาก knowledge base ได้ — ทั้งภาษาไทยและภาษาอังกฤษ
- รองรับ Omnichannel: Web, LINE, Discord, และ platform อื่นในอนาคต
- แยก access ระหว่าง Employee (เห็น internal docs) กับ Customer (เห็นแค่ public docs)
- Upload, index, และ manage เอกสารได้

**Non-Functional:**
- E2E latency p50 < 3 วินาที
- E2E latency p95 < 8 วินาที
- Throughput > 50 req/sec
- ภาษาไทย: Recall@5 > 80%
- Anti-vendor-lock-in: swap component ได้ภายใน 1-2 วัน

### 2.3 Constraints

- ทีมหลักเป็น Python stack
- ไม่มี GPU dedicated (ใน PoC) — self-hosted models ต้องรัน CPU ได้
- Budget ยังไม่ finalize — ต้องมี cost analysis ก่อนตัดสินใจ
- Production deployment ไม่อยู่ใน scope ของ spike นี้

---

## 3. ตัวเลือกที่ประเมิน

### 3.1 Vector Database

ทดสอบ 4 ตัว: **Qdrant**, **pgvector**, **Milvus**, **OpenSearch**

**Benchmark results — 10K vectors (1536 dim):**

| Metric | **Qdrant** ✅ | pgvector | Milvus | OpenSearch |
|--------|------------|---------|--------|------------|
| Index throughput (docs/s) | 595.2 | 73.3 | **907.9** | 185.8 |
| Query latency p50 (ms) | 10.87 | **7.92** | 2.37 | 19.72 |
| Query latency p95 (ms) | 38.27 | **12.37** | 10.17 | 36.87 |
| Filtered latency p50 (ms) | **6.28** | 23.32 | 1.18 | 19.10 |
| Filtered latency p95 (ms) | **15.00** | 30.92 | 1.85 | 25.57 |
| **Recall@10** | **0.896** | 0.429 | 0.277 | 0.793 |

**Benchmark results — 100K vectors (scale test):**

| Metric | **Qdrant** ✅ | pgvector | Milvus | OpenSearch |
|--------|------------|---------|--------|------------|
| Query latency p50 (ms) | **25.71** | 26.71 | 19.43 | 52.51 |
| Query latency p95 (ms) | **100.58** | 77.58 | 505.26 ⚠️ | 253.79 |
| Filtered latency p50 (ms) | **26.36** | 256.03 ❌ | 21.45 | 61.31 |
| Filtered latency p95 (ms) | **46.55** | 1,609.63 ❌ | 45.18 | 97.41 |

**คำแนะนำ: เลือก Qdrant** — recall สูงสุด, filtered latency ดีที่สุดที่ scale ทั้ง 10K และ 100K

---

### 3.2 RAG Framework

ทดสอบ 4 approach: **LlamaIndex**, **LangChain**, **Haystack**, **Bare Metal**

**Benchmark results — Phase 2 (10 queries, embedding=text-embedding-3-small, LLM=gpt-4o-mini):**

| Framework | Chunks | Index (ms) | LOC | คุณภาพ (10 คำถาม) |
|-----------|--------|-----------|-----|-----------------|
| **LlamaIndex** ✅ | 17 | 1,596 | **84** | ✅ ตอบถูกทุกข้อ |
| bare_metal | 5 | 964 | 103 | ✅ ตอบถูกทุกข้อ |
| langchain | 33 | 1,691 | 97 | ✅ ตอบถูกทุกข้อ |
| haystack | 5 | **863** | 142 | ✅ ตอบถูกทุกข้อ |

**Build vs Buy Summary (ผลจาก spike):**

| Factor | Bare Metal | LlamaIndex (เลือก) |
|--------|-----------|-----------------|
| Lines of Code | 103 | **84** |
| ต้องเขียน chunking เอง | ✅ ต้อง | ❌ มีให้ |
| Component swap | ยาก (manual) | ง่าย (built-in) |
| Advanced features (reranking) | ต้องเขียนเอง | มี built-in |
| Debug transparency | สูงสุด | ปานกลาง |

**คำแนะนำ: เลือก LlamaIndex** — LOC น้อยสุด, abstraction ดี, รองรับ features ที่ต้องการในอนาคต

---

### 3.3 Embedding Model

ทดสอบ 5 model: **BGE-M3**, **multilingual-E5-large**, **mxbai-embed-large**, **text-embedding-3-large**, **text-embedding-3-small**

**Benchmark results — Phase 3 (10 queries: Thai + English, weighted score):**

| Model | Thai Recall@3 | Eng Recall@3 | Latency (ms) | Cost/1M | Lock-in | **Score** |
|-------|-------------|------------|-------------|---------|---------|---------|
| **multilingual-e5-large** ✅ | **1.000** | **1.000** | **29.9** | $0 | 0 | **0.9472** |
| BGE-M3 | 0.833 | 1.000 | 53.4 | $0 | 0 | 0.7349 |
| mxbai-embed-large-v1 | 0.833 | 1.000 | **24.5** | $0 | 0 | 0.7000 |
| OpenAI text-embedding-3-small | 1.000 | 1.000 | 312.2 | $0.02 | 9 | 0.6144 |
| OpenAI text-embedding-3-large | 1.000 | 1.000 | 301.7 | $0.13 | 9 | 0.4555 |

> Open-source vs Commercial quality gap: **ไม่มี** — mE5 recall เท่ากับ OpenAI แต่ฟรีและ self-hostable

**คำแนะนำ: เลือก multilingual-e5-large** — recall สมบูรณ์แบบทั้ง 2 ภาษา, ไม่มีค่าใช้จ่าย, latency 29.9ms

---

### 3.4 LLM Provider Strategy

ทดสอบ 4 approach: **OpenRouter**, **OpenAI Direct**, **Anthropic Direct**, **Ollama (self-hosted)**

**Benchmark results — Phase 3.5 (7 providers, 10 queries):**

| Provider | Model | Overall F1 | Thai F1 | Latency (ms) | Cost/10q | Lock-in | **Score** |
|---------|-------|-----------|---------|-------------|---------|---------|---------|
| **OpenRouter** ✅ | **gemini-2.0-flash** | **0.4601** | **0.4785** | **1,066** | **$0.0031** | 2 | **0.8686** |
| OpenRouter | llama-3.1-70b | 0.4586 | 0.4654 | 2,195 | $0.0119 | 0 | 0.8008 |
| OpenRouter | gpt-4o | **0.4689** | 0.4061 | 1,503 | $0.0809 | 3 | 0.6117 |
| OpenRouter | gpt-4o-mini | 0.4334 | 0.4394 | 2,377 | $0.0049 | 3 | 0.5645 |
| OpenAI Direct | gpt-4o-mini | 0.4360 | 0.4438 | 1,440 | $0.0049 | 9 | 0.5002 |
| OpenRouter | deepseek-r1 | 0.4264 | 0.3974 | 2,993 | $0.0045 | 1 | 0.4850 |
| OpenAI Direct | gpt-4o | 0.4651 | 0.3997 | 1,192 | $0.0812 | 9 | 0.4552 |

> OpenRouter vs Direct: `gpt-4o-mini` ผ่าน OpenRouter ได้ score 0.5645 vs Direct 0.5002 — lock-in penalty ส่งผลชัดเจน

**คำแนะนำ: เลือก OpenRouter + gemini-2.0-flash** — best weighted score, Thai F1 สูงสุด, ราคาถูก, lock-in ต่ำ

---

### 3.5 API & Authentication Design

PoC ใน Phase 4 ทดสอบ: **FastAPI + JWT + RBAC + Permission-filtered Retrieval**

**Auth Strategy Comparison:**

| Strategy | Pros | Cons | Verdict |
|----------|------|------|---------|
| JWT + RBAC | Simple, stateless, well-understood | Role explosion ถ้า permission ซับซ้อน | ✅ PoC ใช้ |
| JWT + ABAC | Fine-grained, policy-based | ซับซ้อนกว่า | พิจารณาถ้า RBAC ไม่พอ |
| OAuth 2.0 + OIDC | Standard, SSO support | Complex flow management | Production recommendation |
| API Key + Scoped Perms | Simple for service-to-service | ไม่เหมาะ end-user auth | ใช้สำหรับ bot integrations |

**คำแนะนำ:**

> **[TODO หลัง Phase 4]** ยืนยัน/ปรับ auth design จาก PoC results

---

## 4. Recommended Architecture

> **[TODO หลัง Phase 1-5 เสร็จ — กรอกส่วนนี้ทั้งหมด]**

### 4.1 Selected Tech Stack

| Component | ตัวที่เลือก | เหตุผลหลัก |
|-----------|-----------|-----------|
| **Vector DB** | Qdrant | Recall@10=0.896 สูงสุด, filtered latency ดีที่สุด (p50=6.28ms) |
| **RAG Framework** | LlamaIndex | LOC น้อยสุด (84), abstraction ดี, component swap ง่าย |
| **Embedding Model** | multilingual-e5-large | Recall=1.0 ทั้งไทยและอังกฤษ, ฟรี, self-hostable |
| **LLM Provider** | OpenRouter (gemini-2.0-flash) | Weighted score สูงสุด (0.8686), Thai F1 ดีสุด, ราคาถูก |
| **API Framework** | FastAPI | async, auto docs, Python ecosystem |
| **Auth** | JWT + RBAC | Simple, stateless, permission-filtered retrieval พิสูจน์ใน PoC |

### 4.2 System Diagram (Final Stack)

```
Client (Web / LINE / Discord)
         │
         ▼
    FastAPI + JWT/RBAC
         │
    ┌────┴────────────────────┐
    ▼                         ▼
[RAG Pipeline - LlamaIndex]  [Document Mgmt]
    │                         │
    ├── Embedding: mE5-large  ├── Chunking (size=500, overlap=50)
    ├── Vector DB: Qdrant      └── Indexing → Qdrant
    └── LLM: gemini-2.0-flash
             via OpenRouter
```

### 4.3 Trade-offs ที่ยอมรับ

- เรายอมรับ **self-hosted embedding model บน CPU** เพื่อแลกกับ $0 cost + data privacy + no vendor lock-in (latency 29.9ms ยอมรับได้)
- เรายอมรับ **OpenRouter เป็น gateway ชั้นเพิ่ม** เพื่อแลกกับ anti-lock-in — สามารถเปลี่ยน model ได้ด้วย string เดียว
- เราเลือกไม่ใช้ **pgvector ที่ built-in กับ PostgreSQL** เพราะ recall ต่ำ (0.429) และ filtered latency พังที่ 100K scale
- เราเลือกไม่ใช้ **OpenAI embeddings** เพราะ open-source ให้ recall เท่ากันโดยไม่มีค่าใช้จ่ายและ data ไม่ออกนอก

### 4.4 Migration Path

- **เปลี่ยน Vector DB**: แก้ `VectorDBClient` adapter + `.env` — ไม่ต้องแก้ business logic, ต้อง re-index เอกสาร
- **เปลี่ยน LLM Provider/Model**: แก้ `OPENROUTER_MODEL` env var เดียว — ไม่ต้องแก้ code
- **เปลี่ยน Embedding Model**: แก้ `BaseEmbeddingModel` adapter + re-index เอกสารทั้งหมด (benchmark: 5 chunks ใช้ ~1 วินาที)
- **เปลี่ยน RAG Framework**: แก้ `BaseRAGPipeline` adapter — bare_metal implementation พร้อมใช้เป็น fallback ทันที

---

## 5. Proof-of-Concept Results

### 5.1 Integration Test Results (Phase 5)

> **[TODO หลัง Phase 5 เสร็จ]**

| Scenario | Result | หมายเหตุ |
|---------|--------|---------|
| 1. Employee upload & query | ⬜ — | — |
| 2. Customer permission filter | ⬜ — | — |
| 3. LINE webhook E2E | ⬜ — | — |
| 4. Concurrent queries (30 users) | ⬜ — | — |
| 5. Component swap | ⬜ — | — |
| 6. LLM error handling | ⬜ — | — |
| 7. Thai language E2E | ⬜ — | — |

*⬜ = ยังไม่ทดสอบ, ✅ = ผ่าน, ❌ = ไม่ผ่าน*

### 5.2 Performance vs Targets

> **[TODO หลัง Phase 5 เสร็จ]**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| E2E latency p50 | < 3s | — | ⬜ |
| E2E latency p95 | < 8s | — | ⬜ |
| Retrieval latency p95 | < 200ms | — | ⬜ |
| Throughput | > 50 req/s | — | ⬜ |
| Thai Recall@5 | > 80% | — | ⬜ |

---

## 6. Cost Analysis

> **[TODO หลัง Phase 1-3.5 เสร็จ]**

### 6.1 Monthly Cost Estimate (Production)

ประเมินจาก benchmark: ต้นทุน LLM = $0.003146 / 10 queries → $0.000315 / query

| Component | Self-hosted | Managed/Cloud | หมายเหตุ |
|-----------|------------|--------------|---------|
| **Vector DB (Qdrant)** | ~$20-50/mo (VPS) | ~$25+/mo (Qdrant Cloud) | ขึ้นกับ RAM/storage |
| **Embedding (mE5)** | $0 (CPU inference) | — | self-hosted เท่านั้น |
| **LLM (gemini-flash)** | — | $0.000315/query | ผ่าน OpenRouter |
| **Infrastructure** | ~$30-80/mo | ~$50-100/mo | API server + dependencies |

### 6.2 Cost ที่ Scale ต่างๆ (LLM cost เป็นหลัก)

| Scale | Queries/day | LLM Cost/month | Total est./month |
|-------|------------|---------------|-----------------|
| Small | 1,000 | ~$9.45 | ~$60-80 |
| Medium | 10,000 | ~$94.50 | ~$150-200 |
| Large | 100,000 | ~$945 | ~$1,000-1,100 |

> หมายเหตุ: ถ้า switch เป็น llama-3.1-70b (self-hosted) ค่า LLM จะเป็น $0 แต่ต้องการ GPU server

---

## 7. Risks & Mitigations

| # | Risk | Probability | Impact | Mitigation |
|---|------|-------------|--------|------------|
| R1 | Thai language support ไม่ดีพอ | Medium | High | ทดสอบ Thai-specific models, custom tokenization |
| R2 | Framework เปลี่ยน API / ถูก acquire | Medium | High | Abstraction layer + multi-provider testing |
| R3 | Vector DB performance ไม่ scale | Low | High | Benchmark ที่ realistic scale, มี fallback |
| R4 | LLM API cost สูงกว่า budget | Medium | Medium | Self-hosted fallback, caching strategy |
| R5 | OpenRouter reliability ไม่พอ production | Low | High | Direct API fallback สำหรับ critical path |
| R6 | Permission-filtered search ทำให้ latency แย่ | Medium | Medium | Benchmark filtered vs unfiltered |
| R7 | Security: PII ใน LLM requests | Medium | High | Data classification + PII filter ก่อนส่ง API |

---

## 8. Implementation Roadmap

> **[TODO หลัง RFC ได้ Accepted]**

ถ้า RFC ได้รับ approval — ขั้นตอนถัดไป:

| Phase | งาน | ระยะเวลา |
|-------|-----|---------|
| Setup | Infrastructure provisioning, API keys, environments | — |
| Sprint 1 | Core RAG pipeline (selected stack) | — |
| Sprint 2 | API layer + Auth integration | — |
| Sprint 3 | Channel adapters (LINE, Web) | — |
| Sprint 4 | Production hardening, monitoring | — |
| Launch | Soft launch + monitoring | — |

---

## 9. Decision Log (ADRs)

| ADR | หัวข้อ | สถานะ | ไฟล์ |
|-----|--------|-------|------|
| ADR-001 | Vector Database Selection | 🟢 Accepted | [adr/ADR-001-vector-db.md](../adr/ADR-001-vector-db.md) |
| ADR-002 | RAG Framework Approach | 🟢 Accepted | [adr/ADR-002-rag-framework.md](../adr/ADR-002-rag-framework.md) |
| ADR-003 | Embedding Model Selection | 🟢 Accepted | [adr/ADR-003-embedding-model.md](../adr/ADR-003-embedding-model.md) |
| ADR-004 | LLM Provider Strategy | 🟢 Accepted | [adr/ADR-004-llm-provider.md](../adr/ADR-004-llm-provider.md) |
| ADR-005 | Authentication Approach | 🟡 Draft | [adr/ADR-005-auth.md](../adr/ADR-005-auth.md) |
| ADR-006 | Anti-Vendor-Lock-in Architecture | 🟢 Accepted | [adr/ADR-006-anti-lock-in.md](../adr/ADR-006-anti-lock-in.md) |

---

## Appendices

### A. Raw Benchmark Data

> [TODO] Link ไปยัง `benchmarks/*/results/` files

### B. PoC Source Code

| Component | Path |
|-----------|------|
| Vector DB benchmark | `benchmarks/vector-db/` |
| RAG Framework comparison | `benchmarks/rag-framework/` |
| Embedding evaluation | `benchmarks/embedding-model/` |
| LLM Provider comparison | `benchmarks/llm-provider/` |
| API Server PoC | `api/` |
| Integration Tests | `tests/` |

### C. Reference Materials

- MTEB Leaderboard (embedding benchmarks): https://huggingface.co/spaces/mteb/leaderboard
- OpenRouter model list & pricing: https://openrouter.ai/models
- ANN Benchmarks (vector search): http://ann-benchmarks.com
- plan.md: [../../plan.md](../../plan.md)
