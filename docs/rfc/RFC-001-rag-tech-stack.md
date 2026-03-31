# RFC-001: RAG System Tech Stack Selection

| ฟิลด์ | ค่า |
|------|-----|
| **RFC ID** | RFC-001 |
| **ชื่อ** | RAG System Tech Stack Selection |
| **สถานะ** | 🟡 Draft |
| **ผู้เขียน** | Engineering Team |
| **วันที่สร้าง** | 2026-03-31 |
| **วันที่ update ล่าสุด** | 2026-03-31 |
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

> **[TODO หลัง Phase 1-5 เสร็จ]**  
> สรุปสั้น 3-5 ประโยค: เราเลือกอะไร เพราะอะไร และ trade-off หลักคืออะไร
>
> ตัวอย่างโครงสร้าง:
> - เราเลือก **[Vector DB]** เพราะ [เหตุผล 1-2 ข้อ]
> - เราเลือก **[RAG Approach]** เพราะ [เหตุผล]
> - เราเลือก **[Embedding Model]** เพราะ [เหตุผล]
> - LLM strategy: ใช้ **[Provider/Model]** ผ่าน **[OpenRouter/Direct]**
> - Trade-off หลักที่ยอมรับ: [...]

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

**ตาราง scoring** (เติมหลัง Phase 1 เสร็จ):

| Criteria | Weight | Qdrant | pgvector | Milvus | OpenSearch |
|----------|--------|--------|----------|--------|------------|
| Performance (QPS) | 20% | — | — | — | — |
| Recall Accuracy | 15% | — | — | — | — |
| Scalability | 15% | — | — | — | — |
| Operational Complexity | 15% | — | — | — | — |
| Filtering Capability | 10% | — | — | — | — |
| Thai Text Support | 5% | — | — | — | — |
| Managed Service Options | 5% | — | — | — | — |
| Community & Ecosystem | 5% | — | — | — | — |
| Cost (TCO) | 5% | — | — | — | — |
| Migration Ease | 5% | — | — | — | — |
| **Total** | 100% | **—** | **—** | **—** | **—** |

> *คะแนน 1-5 scale (5 = ดีที่สุด)*

**Benchmark results** (เติมหลัง Phase 1 เสร็จ):

| Metric | Qdrant | pgvector | Milvus | OpenSearch |
|--------|--------|----------|--------|------------|
| Insert throughput (docs/sec) | — | — | — | — |
| Query latency p50 (ms) | — | — | — | — |
| Query latency p95 (ms) | — | — | — | — |
| Recall@10 | — | — | — | — |
| Memory usage (10K vectors) | — | — | — | — |
| Memory usage (100K vectors) | — | — | — | — |

**คำแนะนำ:**

> **[TODO หลัง Phase 1]** เลือก _____ เพราะ _____

---

### 3.2 RAG Framework

ทดสอบ 4 approach: **LlamaIndex**, **LangChain**, **Haystack**, **Bare Metal**

**ตาราง scoring** (เติมหลัง Phase 2 เสร็จ):

| Criteria | Weight | LlamaIndex | LangChain | Haystack | Bare Metal |
|----------|--------|------------|-----------|----------|------------|
| Flexibility / Customization | 20% | — | — | — | — |
| Production Readiness | 15% | — | — | — | — |
| Debugging & Observability | 15% | — | — | — | — |
| Learning Curve | 10% | — | — | — | — |
| Vendor Lock-in Risk | 15% | — | — | — | — |
| Community & Support | 5% | — | — | — | — |
| Upgrade & Breaking Changes | 10% | — | — | — | — |
| Performance Overhead | 5% | — | — | — | — |
| Thai Language Pipeline | 5% | — | — | — | — |
| **Total** | 100% | **—** | **—** | **—** | **—** |

**Build vs Buy Summary:**

| Factor | Build from Scratch | Use Framework |
|--------|-------------------|---------------|
| Time to PoC | 2-4 สัปดาห์ | 2-5 วัน |
| Time to Production | 2-3 เดือน | 2-4 สัปดาห์ |
| Vendor Lock-in | ไม่มี | Medium risk |
| Debugging | ง่าย | ยากกว่า (abstraction) |
| Maintenance | สูง | ต่ำ-กลาง |

**คำแนะนำ:**

> **[TODO หลัง Phase 2]** เลือก _____ เพราะ _____

---

### 3.3 Embedding Model

ทดสอบ 5 model: **BGE-M3**, **multilingual-E5-large**, **mxbai-embed-large**, **text-embedding-3-large**, **text-embedding-3-small**

**ตาราง scoring** (เติมหลัง Phase 3 เสร็จ):

| Criteria | Weight | BGE-M3 | mE5-large | mxbai | OAI-large | OAI-small |
|----------|--------|--------|-----------|-------|-----------|-----------|
| Thai Retrieval Quality | 25% | — | — | — | — | — |
| English Retrieval Quality | 15% | — | — | — | — | — |
| Latency | 15% | — | — | — | — | — |
| Cost (per 1M tokens) | 15% | — | — | — | — | — |
| Self-hosting Feasibility | 10% | — | — | — | — | — |
| Dimension / Storage Cost | 5% | — | — | — | — | — |
| Max Token Length | 5% | — | — | — | — | — |
| Vendor Lock-in Risk | 10% | — | — | — | — | — |
| **Total** | 100% | **—** | **—** | **—** | **—** | **—** |

**Thai Language Benchmark** (เติมหลัง Phase 3 เสร็จ):

| Model | Recall@3 (Thai) | Recall@5 (Thai) | Latency (ms) | Cost/1M tokens |
|-------|-----------------|-----------------|--------------|----------------|
| BGE-M3 | — | — | — | $0 (local) |
| multilingual-E5 | — | — | — | $0 (local) |
| mxbai | — | — | — | $0 (local) |
| OAI text-embedding-3-large | — | — | — | $0.13 |
| OAI text-embedding-3-small | — | — | — | $0.02 |

**คำแนะนำ:**

> **[TODO หลัง Phase 3]** เลือก _____ เพราะ _____

---

### 3.4 LLM Provider Strategy

ทดสอบ 4 approach: **OpenRouter**, **OpenAI Direct**, **Anthropic Direct**, **Ollama (self-hosted)**

**ตาราง scoring** (เติมหลัง Phase 3.5 เสร็จ):

| Criteria | Weight | OpenRouter | OpenAI Direct | Anthropic Direct | Ollama |
|----------|--------|------------|---------------|------------------|--------|
| Response Quality (RAG) | 20% | — | — | — | — |
| Anti-Vendor-Lock-in | 20% | — | — | — | — |
| Cost Flexibility | 15% | — | — | — | — |
| Latency | 15% | — | — | — | — |
| Thai Language Quality | 10% | — | — | — | — |
| Fallback / Reliability | 10% | — | — | — | — |
| Privacy / Data Control | 5% | — | — | — | — |
| Ease of Model Switching | 5% | — | — | — | — |
| **Total** | 100% | **—** | **—** | **—** | **—** |

**คำแนะนำ:**

> **[TODO หลัง Phase 3.5]** เลือก _____ เพราะ _____

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
| **Vector DB** | [TODO] | [TODO] |
| **RAG Approach** | [TODO] | [TODO] |
| **Embedding Model** | [TODO] | [TODO] |
| **LLM Provider** | [TODO] | [TODO] |
| **API Framework** | FastAPI | async, auto docs, Python ecosystem |
| **Auth** | [TODO] | [TODO] |

### 4.2 System Diagram (Final Stack)

```
[TODO: วาด diagram ของ recommended stack]

ตัวอย่างโครงสร้าง:

Client (Web / LINE / Discord)
         │
         ▼
    FastAPI + JWT/RBAC
         │
    ┌────┴────────────────────┐
    ▼                         ▼
[RAG Pipeline]           [Document Mgmt]
    │                         │
    ├── Embedding: [TODO]      ├── Chunking
    ├── Vector DB: [TODO]      └── Indexing
    └── LLM: [TODO via TODO]
```

### 4.3 Trade-offs ที่ยอมรับ

> **[TODO]** ระบุ trade-offs ที่เรายอมรับอย่างชัดเจน:
> - เรายอมรับ [X] เพื่อแลกกับ [Y]
> - เราเลือกไม่ทำ [Z] ในตอนนี้ เพราะ [เหตุผล]

### 4.4 Migration Path

> **[TODO]** ถ้าต้องเปลี่ยน component ในอนาคต:
> - เปลี่ยน Vector DB: [ทำอะไร, ใช้เวลานานแค่ไหน]
> - เปลี่ยน LLM Provider: แก้ config ไฟล์เดียว (OpenRouter)
> - เปลี่ยน Embedding Model: [ทำอะไร, re-index ใช้เวลานานแค่ไหน]

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

ประเมินที่ scale ต่างๆ:

| Component | Option A | Option B | หมายเหตุ |
|-----------|---------|---------|---------|
| **Vector DB** | — | — | — |
| **Embedding** | — | — | — |
| **LLM** | — | — | per query |
| **Infrastructure** | — | — | — |
| **Total/month** | **—** | **—** | at [X] queries/day |

### 6.2 Cost ที่ Scale ต่างๆ

| Scale | Queries/day | Est. Cost/month |
|-------|------------|-----------------|
| Small | 1,000 | — |
| Medium | 10,000 | — |
| Large | 100,000 | — |

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
| ADR-001 | Vector Database Selection | 🟡 Draft | [adr/ADR-001-vector-db.md](../adr/ADR-001-vector-db.md) |
| ADR-002 | RAG Framework Approach | 🟡 Draft | [adr/ADR-002-rag-framework.md](../adr/ADR-002-rag-framework.md) |
| ADR-003 | Embedding Model Selection | 🟡 Draft | [adr/ADR-003-embedding-model.md](../adr/ADR-003-embedding-model.md) |
| ADR-004 | LLM Provider Strategy | 🟡 Draft | [adr/ADR-004-llm-provider.md](../adr/ADR-004-llm-provider.md) |
| ADR-005 | Authentication Approach | 🟡 Draft | [adr/ADR-005-auth.md](../adr/ADR-005-auth.md) |
| ADR-006 | Anti-Vendor-Lock-in Architecture | 🟡 Draft | [adr/ADR-006-anti-lock-in.md](../adr/ADR-006-anti-lock-in.md) |

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
