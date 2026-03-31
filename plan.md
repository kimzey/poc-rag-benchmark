# RAG Spike Research Plan
## Retrieval-Augmented Generation — Technical Spike & Evaluation

| Item            | Detail                                                    |
|-----------------|-----------------------------------------------------------|
| Project         | RAG Spike Research (spike-rak)                            |
| Author          | Engineering Team                                          |
| Created         | 2026-03-31                                                |
| Status          | Draft                                                     |
| Target Audience | Engineering team, พี่ตั๊ก (Senior), Stakeholders          |
| DoD             | RFC Document + Knowledge Sharing Session with team consensus |

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Research Scope](#2-research-scope)
3. [Definition of Done (DoD)](#3-definition-of-done-dod)
4. [Anti-Vendor-Lock-in Principles](#4-anti-vendor-lock-in-principles)
5. [Phase 1: Vector Database Comparison](#5-phase-1-vector-database-comparison)
6. [Phase 2: RAG Framework Comparison](#6-phase-2-rag-framework-comparison)
7. [Phase 3: Embedding Model Comparison](#7-phase-3-embedding-model-comparison)
8. [Phase 3.5: LLM Provider Comparison](#8-phase-35-llm-provider-comparison)
9. [Phase 4: API Layer & Authentication Design](#9-phase-4-api-layer--authentication-design)
10. [Phase 5: Integration Testing](#10-phase-5-integration-testing)
11. [Phase 6: RFC Document & Knowledge Sharing](#11-phase-6-rfc-document--knowledge-sharing)
11. [Decision Criteria & Weighting](#11-decision-criteria--weighting)
12. [Risks & Blockers](#12-risks--blockers)
13. [Timeline & Milestones](#13-timeline--milestones)
14. [Appendices](#14-appendices)

---

## 1. Project Overview

### 1.1 วัตถุประสงค์ (Objectives)

Spike research เพื่อประเมินและเลือก Tech Stack สำหรับระบบ RAG ที่จะใช้ใน Production โดยมีเป้าหมายหลัก:

1. **เปรียบเทียบ Vector Database** ที่เหมาะสมกับ use case ของเรา
2. **เปรียบเทียบ RAG Framework** ระหว่าง build from scratch vs ใช้ framework สำเร็จรูป
3. **เปรียบเทียบ Embedding Model** ทั้ง commercial และ open-source
4. **ออกแบบ API Layer** ที่รองรับ Omnichannel (Web, LINE, Discord, etc.)
5. **ออกแบบระบบ Auth** ที่แยก Employee กับ Customer พร้อม Permission Control
6. **หลีกเลี่ยง Vendor Lock-in** — สถาปัตยกรรมต้อง swap component ได้โดยไม่ rewrite ทั้งระบบ

### 1.2 ขอบเขต (Scope)

**In Scope:**
- Vector DB evaluation (benchmarks, operational complexity, cost)
- RAG framework evaluation (flexibility, community, production readiness)
- Embedding model evaluation (quality, cost, latency, multilingual support — โดยเฉพาะภาษาไทย)
- API design สำหรับ omnichannel clients
- Auth design สำหรับ multi-tenant (employee vs customer)
- Proof-of-concept prototypes สำหรับแต่ละ approach
- Anti-vendor-lock-in architecture patterns

**Out of Scope:**
- Production deployment & infrastructure provisioning
- Full UI/UX implementation
- Fine-tuning LLM models
- Data migration จาก existing systems
- Compliance/legal review (PDPA, etc.) — จะทำแยกภายหลัง

### 1.3 System Architecture Overview (Target)

```
┌─────────────────────────────────────────────────────────┐
│                    Client Platforms                       │
│   ┌──────┐  ┌──────┐  ┌─────────┐  ┌───────────────┐   │
│   │ Web  │  │ LINE │  │ Discord │  │ Other Clients │   │
│   └──┬───┘  └──┬───┘  └────┬────┘  └──────┬────────┘   │
│      └─────────┴───────────┴───────────────┘             │
│                        │                                 │
│              ┌─────────▼──────────┐                      │
│              │   API Gateway /    │                      │
│              │   Load Balancer    │                      │
│              └─────────┬──────────┘                      │
│                        │                                 │
│              ┌─────────▼──────────┐                      │
│              │   Auth Layer       │                      │
│              │  (JWT + RBAC/ABAC) │                      │
│              └─────────┬──────────┘                      │
│                        │                                 │
│              ┌─────────▼──────────┐                      │
│              │   RAG API Service  │                      │
│              │   (FastAPI)        │                      │
│              └────┬─────┬────┬───┘                      │
│                   │     │    │                            │
│          ┌────────┘     │    └────────┐                   │
│          ▼              ▼             ▼                   │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────┐         │
│  │ Vector DB    │ │ LLM API  │ │ Document     │         │
│  │ (Retrieval)  │ │ Provider │ │ Store / Blob │         │
│  └──────────────┘ └──────────┘ └──────────────┘         │
│                                                          │
│  ┌──────────────┐ ┌──────────────┐                       │
│  │ Relational   │ │ Cache Layer  │                       │
│  │ DB (Users,   │ │ (Redis)      │                       │
│  │  Permissions)│ └──────────────┘                       │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Research Scope

### 2.1 มิติที่ต้องวิจัย (Research Dimensions)

| Dimension               | คำถามหลัก (Key Questions)                                                                 |
|--------------------------|-------------------------------------------------------------------------------------------|
| **Vector Database**      | ตัวไหนเหมาะกับ scale, cost, และ operational complexity ของเรา?                            |
| **RAG Framework**        | Build from scratch vs ใช้ framework — trade-off คืออะไร?                                  |
| **Embedding Model**      | Model ไหนรองรับภาษาไทยได้ดี? cost vs quality trade-off เป็นอย่างไร?                      |
| **API Architecture**     | ออกแบบ omnichannel API อย่างไรให้ flexible และ maintainable?                               |
| **Auth & Permissions**   | RBAC vs ABAC? แยก Employee/Customer access อย่างไร?                                       |
| **Vendor Lock-in**       | จะออกแบบ abstraction layer อย่างไรให้ swap ได้จริง?                                        |
| **Thai Language Support**| แต่ละ component รองรับภาษาไทยระดับไหน? (tokenization, search, embedding quality)          |
| **Operational Cost**     | TCO (Total Cost of Ownership) แต่ละ option เป็นอย่างไรที่ scale ต่างกัน?                  |

### 2.2 Evaluation Approach

สำหรับแต่ละ component จะประเมินใน 3 ระดับ:

1. **Desktop Research** — อ่าน docs, benchmarks, community feedback
2. **Hands-on PoC** — ทดลอง implement PoC ขนาดเล็กเพื่อวัดผลจริง
3. **Comparative Analysis** — สรุปเป็นตาราง comparison พร้อม recommendation

---

## 3. Definition of Done (DoD)

- [ ] **RFC Document** — เอกสารสรุปผลวิจัยอย่างละเอียด พร้อมตาราง comparison และ recommendation
- [ ] **PoC Prototypes** — โค้ด prototype สำหรับแต่ละ approach ที่ทดลอง (อยู่ใน repo นี้)
- [ ] **Benchmark Results** — ผลทดสอบ performance (latency, throughput, relevance)
- [ ] **Architecture Decision Records (ADRs)** — บันทึกเหตุผลของแต่ละ decision
- [ ] **Knowledge Sharing Presentation** — slide deck สำหรับ present ให้ทีมและพี่ตั๊ก
- [ ] **Team Consensus** — ทีม (รวมถึงพี่ตั๊ก) agree กับ Tech Stack ที่เลือก

---

## 4. Anti-Vendor-Lock-in Principles

หลักการออกแบบที่ต้องยึดถือตลอดทั้ง project:

### 4.1 Iron Rules

| #  | Principle                         | รายละเอียด                                                                                           |
|----|-----------------------------------|------------------------------------------------------------------------------------------------------|
| 1  | **Abstraction over Implementation** | ทุก external dependency ต้องอยู่หลัง interface/abstract class — ห้าม import ตรงใน business logic    |
| 2  | **Port & Adapter Pattern**        | ใช้ Hexagonal Architecture — core logic ไม่รู้จัก infrastructure                                     |
| 3  | **Configuration over Code**       | เปลี่ยน provider ผ่าน config/env ไม่ใช่ code change                                                 |
| 4  | **Standard Protocols**            | ใช้ standard APIs (OpenAI-compatible, S3-compatible) เมื่อเป็นไปได้                                  |
| 5  | **Data Portability**              | Data format ต้อง export/import ได้ — ห้ามใช้ proprietary format ที่ migrate ไม่ได้                   |
| 6  | **Multi-Provider Testing**        | PoC ต้องทดสอบกับอย่างน้อย 2 providers เพื่อพิสูจน์ว่า swap ได้จริง                                   |

### 4.2 Abstraction Layers to Design

```
┌─────────────────────────────────────────┐
│           Application Layer              │
│  (Business Logic — ไม่รู้จัก infra)      │
├─────────────────────────────────────────┤
│           Port Interfaces                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │VectorStore│ │Embedder  │ │LLMClient │ │
│  │Interface  │ │Interface │ │Interface │ │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ │
├────────┼────────────┼────────────┼──────┤
│        │  Adapter Layer          │       │
│  ┌─────▼────┐ ┌─────▼────┐ ┌────▼─────┐ │
│  │Milvus    │ │OpenAI    │ │OpenRouter│ │
│  │Adapter   │ │Adapter   │ │Adapter   │ │
│  ├──────────┤ ├──────────┤ ├──────────┤ │
│  │OpenSearch│ │Cohere    │ │Claude    │ │
│  │Adapter   │ │Adapter   │ │Adapter   │ │
│  ├──────────┤ ├──────────┤ ├──────────┤ │
│  │pgvector  │ │Local     │ │Ollama    │ │
│  │Adapter   │ │Model     │ │Adapter   │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────┘
```

### 4.3 Checklist: Anti-Lock-in Verification

สำหรับทุก component ที่เลือก ต้องตอบคำถามเหล่านี้ได้:

- [ ] ถ้า vendor นี้ถูก acquire หรือ deprecate เราเปลี่ยนได้ภายในกี่วัน?
- [ ] มี open-source alternative ที่ใช้แทนได้หรือไม่?
- [ ] Data ของเรา export ออกมาในรูปแบบ standard ได้หรือไม่?
- [ ] API ที่ใช้เป็น proprietary หรือ standard protocol?
- [ ] มี abstraction layer กั้นระหว่าง business logic กับ vendor-specific code หรือไม่?

---

## 5. Phase 1: Vector Database Comparison

**ระยะเวลา:** 5-7 วัน
**เป้าหมาย:** เลือก Vector DB ที่เหมาะสมที่สุดสำหรับ production RAG system

### 5.1 Candidates

| Vector DB       | Type                  | License        | หมายเหตุ                                  |
|-----------------|-----------------------|----------------|-------------------------------------------|
| **Milvus**      | Purpose-built Vector  | Apache 2.0     | Mature, large-scale, Zilliz managed option |
| **OpenSearch**   | Search + Vector       | Apache 2.0     | AWS มี managed service, text search ด้วย   |
| **pgvector**    | PostgreSQL extension  | PostgreSQL     | ใช้ร่วมกับ existing Postgres, simple setup  |
| **Qdrant**      | Purpose-built Vector  | Apache 2.0     | Rust-based, strong filtering               |
| **Weaviate**    | Purpose-built Vector  | BSD-3-Clause   | Built-in vectorizer modules                |
| **Chroma**      | Embedded/lightweight  | Apache 2.0     | เหมาะกับ prototyping, simple API            |

### 5.2 Comparison Matrix — Evaluation Criteria

| Criteria                    | Weight | Milvus | OpenSearch | pgvector | Qdrant | Weaviate | Chroma |
|-----------------------------|--------|--------|------------|----------|--------|----------|--------|
| **Performance (QPS)**       | 20%    |        |            |          |        |          |        |
| **Recall Accuracy**         | 15%    |        |            |          |        |          |        |
| **Scalability**             | 15%    |        |            |          |        |          |        |
| **Operational Complexity**  | 15%    |        |            |          |        |          |        |
| **Filtering Capability**    | 10%    |        |            |          |        |          |        |
| **Thai Text Support**       | 5%     |        |            |          |        |          |        |
| **Managed Service Options** | 5%     |        |            |          |        |          |        |
| **Community & Ecosystem**   | 5%     |        |            |          |        |          |        |
| **Cost (TCO)**              | 5%     |        |            |          |        |          |        |
| **Migration Ease**          | 5%     |        |            |          |        |          |        |
| **Total**                   | 100%   |        |            |          |        |          |        |

> หมายเหตุ: คะแนนจะเติมหลังจากทำ PoC เสร็จ (1-5 scale, 5 = ดีที่สุด)

### 5.3 PoC Benchmark Plan

**Dataset:** เตรียม test dataset ขนาด 3 ระดับ:
- Small: 10K documents
- Medium: 100K documents
- Large: 1M documents (ถ้าเป็นไปได้)

**Metrics ที่วัด:**
- Indexing throughput (docs/sec)
- Query latency (p50, p95, p99)
- Recall@10 (ความแม่นยำของ retrieval)
- Memory usage
- Disk usage
- Startup time
- Concurrent query performance

**Test Scenarios:**
- Pure vector search (ANN)
- Filtered vector search (metadata filtering)
- Hybrid search (text + vector) — ถ้า supported
- Batch insert performance
- Index rebuild time

### 5.4 Task Checklist

- [ ] เตรียม test dataset (Thai + English mixed content)
- [ ] Setup Docker Compose สำหรับแต่ละ Vector DB
- [ ] เขียน benchmark script (standardized สำหรับทุก DB)
- [ ] Run benchmarks — Small dataset (10K)
- [ ] Run benchmarks — Medium dataset (100K)
- [ ] ทดสอบ operational tasks (backup, restore, scaling)
- [ ] ประเมิน managed service options และ pricing
- [ ] เขียนสรุปผลเปรียบเทียบ
- [ ] ทำ recommendation พร้อมเหตุผล

### 5.5 Key Questions to Answer

1. ถ้า data ไม่เกิน 1M vectors — pgvector พอหรือไม่? (simple architecture advantage)
2. ถ้าต้องการ hybrid search (keyword + semantic) — OpenSearch มี advantage มากแค่ไหน?
3. Milvus vs Qdrant — ที่ scale เดียวกัน performance ต่างกันมากไหม?
4. Operational complexity — ทีมเราพร้อมดูแล dedicated vector DB หรือควรใช้ managed service?

---

## 6. Phase 2: RAG Framework Comparison

**ระยะเวลา:** 5-7 วัน
**เป้าหมาย:** ตัดสินใจระหว่าง build from scratch vs ใช้ framework — และถ้าใช้ framework จะเลือกตัวไหน

### 6.1 Approaches to Compare

#### Approach A: ใช้ Framework

| Framework       | Language | License    | หมายเหตุ                                       |
|-----------------|----------|------------|------------------------------------------------|
| **LlamaIndex**  | Python   | MIT        | Data framework, strong indexing/retrieval       |
| **LangChain**   | Python   | MIT        | General-purpose, largest ecosystem              |
| **Haystack**    | Python   | Apache 2.0 | Deepset, production-focused, pipeline-based     |

#### Approach B: Build from Scratch (Bare Metal)

Custom implementation โดยใช้ libraries เฉพาะส่วน:
- Vector DB client library ตรง
- OpenAI/Anthropic SDK ตรง
- Custom chunking & retrieval logic
- Custom prompt engineering

### 6.2 Comparison Matrix — Framework vs Bare Metal

| Criteria                          | Weight | LlamaIndex | LangChain | Haystack | Bare Metal |
|-----------------------------------|--------|------------|-----------|----------|------------|
| **Flexibility / Customization**   | 20%    |            |           |          |            |
| **Production Readiness**          | 15%    |            |           |          |            |
| **Debugging & Observability**     | 15%    |            |           |          |            |
| **Learning Curve**                | 10%    |            |           |          |            |
| **Vendor Lock-in Risk**           | 15%    |            |           |          |            |
| **Community & Support**           | 5%     |            |           |          |            |
| **Upgrade & Breaking Changes**    | 10%    |            |           |          |            |
| **Performance Overhead**          | 5%     |            |           |          |            |
| **Thai Language Pipeline**        | 5%     |            |           |          |            |
| **Total**                         | 100%   |            |           |          |            |

### 6.3 Build vs Buy Analysis

| Factor                     | Build from Scratch                              | Use Framework                                    |
|----------------------------|------------------------------------------------|--------------------------------------------------|
| **Time to PoC**            | 2-4 สัปดาห์                                    | 2-5 วัน                                          |
| **Time to Production**     | 2-3 เดือน                                      | 2-4 สัปดาห์                                      |
| **Maintenance Burden**     | สูง — ต้องดูแลเอง 100%                        | ต่ำ-กลาง — แต่ต้องตาม upgrade framework           |
| **Control**                | สูงสุด — ปรับได้ทุกอย่าง                       | จำกัดตาม abstraction ที่ framework ให้มา           |
| **Breaking Changes Risk**  | ต่ำ — เราควบคุม dependencies เอง                | สูง — framework update อาจ break code             |
| **Team Knowledge**         | ต้องเข้าใจ RAG deeply                          | สามารถเริ่มได้เร็วกว่า                            |
| **Debugging**              | ง่าย — เข้าใจทุก line                          | ยากกว่า — abstraction ซ่อน complexity               |
| **Vendor Lock-in**         | ไม่มี                                          | ขึ้นกับ framework (medium risk)                   |

### 6.4 PoC Implementation Plan

สำหรับแต่ละ approach, implement RAG pipeline เดียวกัน:

**PoC Scenario:** ระบบถาม-ตอบจาก internal documents (Thai + English)

**Pipeline Steps:**
1. Document loading (PDF, Markdown, HTML)
2. Text chunking (ทดสอบ chunk strategies ต่างๆ)
3. Embedding generation
4. Vector storage & retrieval
5. Prompt construction with context
6. LLM generation
7. Response formatting

**วัดผล:**
- Lines of code required
- Time to implement
- Answer quality (manual evaluation)
- Latency (end-to-end)
- Ease of adding new document types
- Ease of swapping components (LLM, Vector DB, Embedder)

### 6.5 Task Checklist

- [ ] PoC: LlamaIndex implementation
- [ ] PoC: LangChain implementation
- [ ] PoC: Haystack implementation
- [ ] PoC: Bare metal implementation
- [ ] Evaluate abstraction depth ของแต่ละ framework (อ่าน source code)
- [ ] ทดสอบ component swapping ในแต่ละ framework (เปลี่ยน LLM, เปลี่ยน Vector DB)
- [ ] ประเมิน upgrade path และ breaking change history
- [ ] ประเมิน observability / tracing support
- [ ] เขียนสรุปผล Build vs Buy recommendation

### 6.6 Key Questions to Answer

1. Framework ไหนมี abstraction ที่ดีพอให้ swap component ได้จริง? (ไม่ใช่แค่ claim)
2. LangChain เปลี่ยน API บ่อยแค่ไหน? ความเสี่ยงของ breaking changes?
3. ถ้า build from scratch — effort ที่มากขึ้นคุ้มกับ flexibility ที่ได้หรือไม่?
4. Haystack pipeline approach เหมาะกับ production use case ของเรามากแค่ไหน?
5. ถ้าเลือก framework — จะ wrap ด้วย abstraction layer อีกชั้นเพื่อป้องกัน lock-in หรือไม่?

---

## 7. Phase 3: Embedding Model Comparison

**ระยะเวลา:** 3-5 วัน
**เป้าหมาย:** เลือก Embedding Model ที่เหมาะกับ use case (โดยเฉพาะภาษาไทย)

### 7.1 Candidates

| Model                          | Type        | Dimensions | หมายเหตุ                                    |
|--------------------------------|-------------|------------|---------------------------------------------|
| **OpenAI text-embedding-3-large** | Commercial | 3072       | Benchmark leader, per-token pricing          |
| **OpenAI text-embedding-3-small** | Commercial | 1536       | ถูกกว่า, ดีพอสำหรับหลาย use case             |
| **Cohere embed-v3**            | Commercial  | 1024       | Good multilingual, input type support        |
| **BGE-M3**                     | Open-source | 1024       | BAAI, strong multilingual, self-hosted       |
| **multilingual-e5-large**      | Open-source | 1024       | Microsoft, solid multilingual performance    |
| **mxbai-embed-large**          | Open-source | 1024       | mixedbread.ai, open-weight                   |
| **Thai-specific models**       | Open-source | Varies     | ต้อง research เพิ่ม — WangchanBERTa etc.     |

### 7.2 Comparison Matrix

| Criteria                        | Weight | OAI-3-large | OAI-3-small | Cohere v3 | BGE-M3 | e5-large | Thai-specific |
|---------------------------------|--------|-------------|-------------|-----------|--------|----------|---------------|
| **Thai Retrieval Quality**      | 25%    |             |             |           |        |          |               |
| **English Retrieval Quality**   | 15%    |             |             |           |        |          |               |
| **Latency**                     | 15%    |             |             |           |        |          |               |
| **Cost (per 1M tokens)**        | 15%    |             |             |           |        |          |               |
| **Self-hosting Feasibility**    | 10%    |             |             |           |        |          |               |
| **Dimension / Storage Cost**    | 5%     |             |             |           |        |          |               |
| **Max Token Length**            | 5%     |             |             |           |        |          |               |
| **Vendor Lock-in Risk**         | 10%    |             |             |           |        |          |               |
| **Total**                       | 100%   |             |             |           |        |          |               |

### 7.3 Thai Language Evaluation

**Critical:** ภาษาไทยเป็น first-class citizen ของระบบ ต้องทดสอบ:

- [ ] Tokenization quality (คำไทยถูก tokenize ถูกต้องหรือไม่)
- [ ] Semantic similarity accuracy (ค้นหาภาษาไทยแล้วได้ผลลัพธ์ relevant)
- [ ] Cross-language retrieval (query ไทย → retrieve English documents & vice versa)
- [ ] Thai technical terminology handling (ศัพท์เทคนิค, ศัพท์เฉพาะทาง)
- [ ] Thai colloquial/informal text handling (ภาษาพูด, slang)

**Test Dataset สำหรับภาษาไทย:**
- เอกสารราชการ / formal documents
- เอกสาร technical (IT, engineering)
- คำถาม-คำตอบ FAQ ภาษาไทย
- Mixed Thai-English content

### 7.4 Task Checklist

- [ ] เตรียม evaluation dataset (Thai + English + Mixed)
- [ ] Benchmark แต่ละ model ด้วย dataset เดียวกัน
- [ ] วัด retrieval quality (NDCG, MRR, Recall@k)
- [ ] วัด latency (local vs API)
- [ ] คำนวณ cost projection ที่ production scale
- [ ] ทดสอบ self-hosted deployment (สำหรับ open-source models)
- [ ] เขียนสรุปผลพร้อม recommendation

### 7.5 Hybrid Strategy Consideration

พิจารณา strategy ที่ใช้มากกว่า 1 model:
- **Primary:** Commercial model (quality) สำหรับ query-time embedding
- **Fallback:** Open-source model (cost) สำหรับ batch indexing หรือ fallback
- **Design:** abstraction layer ที่ swap model ได้ผ่าน config

---

## 8. Phase 3.5: LLM Provider Comparison

**ระยะเวลา:** 2-3 วัน (ทำ parallel กับ Phase 3 ได้)
**เป้าหมาย:** เลือก LLM Provider strategy ที่ balance ระหว่าง quality, cost, และ anti-lock-in

### 8.0 Candidates

| Provider          | Type              | API Compatibility  | หมายเหตุ                                                        |
|-------------------|-------------------|--------------------|------------------------------------------------------------------|
| **OpenRouter**    | Aggregator/Proxy  | OpenAI-compatible  | **Key candidate** — single API เข้าถึงหลาย model, swap ได้ทันที |
| **OpenAI direct**| Commercial        | Native             | GPT-4o, o1 — quality leader, แต่ lock-in สูง                    |
| **Anthropic direct** | Commercial     | Native             | Claude 3.x — strong reasoning, แต่ lock-in สูง                   |
| **Google Vertex AI** | Commercial     | OpenAI-compatible  | Gemini models, managed, enterprise support                        |
| **Ollama**        | Self-hosted       | OpenAI-compatible  | Local inference, no API cost, privacy-friendly                    |
| **vLLM**          | Self-hosted       | OpenAI-compatible  | High-throughput serving, GPU required                             |

### 8.0.1 OpenRouter — Deep Dive

OpenRouter เป็น **unified LLM API gateway** ที่เหมาะกับ anti-vendor-lock-in strategy โดยตรง:

**สิ่งที่ OpenRouter ให้:**
- Single OpenAI-compatible endpoint (`https://openrouter.ai/api/v1`)
- เข้าถึงได้ทั้ง GPT-4o, Claude 3.x, Gemini, Llama 3, Mistral, DeepSeek ฯลฯ ผ่าน API เดียว
- เปลี่ยน model ผ่าน `model` parameter โดยไม่ต้องแก้โค้ด
- Automatic fallback เมื่อ provider down
- Cost comparison / model routing ตาม budget หรือ latency

**ตัวอย่าง code:**
```python
# เปลี่ยนแค่ model string — ไม่ต้องแก้ code อื่นเลย
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",   # หรือ "openai/gpt-4o" หรือ "meta-llama/llama-3.1-70b-instruct"
    messages=[{"role": "user", "content": prompt}],
)
```

**Models ที่น่าสนใจบน OpenRouter สำหรับ RAG:**

| Model                              | ข้อดี                                         | ราคา (approx)           |
|------------------------------------|-----------------------------------------------|-------------------------|
| `anthropic/claude-3.5-sonnet`      | Strong reasoning, long context                | $$                      |
| `openai/gpt-4o`                    | Balanced, fast, multimodal                    | $$                      |
| `openai/gpt-4o-mini`               | ถูก, เร็ว, ดีพอสำหรับ RAG                     | $                       |
| `google/gemini-flash-1.5`          | ราคาถูก, context ยาวมาก (1M tokens)           | $                       |
| `meta-llama/llama-3.1-70b-instruct`| Open-weight, strong, free tier available      | $ (หรือ free)           |
| `deepseek/deepseek-chat`           | ราคาถูกมาก, reasoning ดี                      | $                       |

### 8.0.2 Comparison Matrix — LLM Provider Strategy

| Criteria                        | Weight | OpenRouter | OpenAI Direct | Anthropic Direct | Ollama (self-host) |
|---------------------------------|--------|------------|---------------|------------------|--------------------|
| **Response Quality (RAG)**      | 20%    |            |               |                  |                    |
| **Anti-Vendor-Lock-in**         | 20%    |            |               |                  |                    |
| **Cost Flexibility**            | 15%    |            |               |                  |                    |
| **Latency**                     | 15%    |            |               |                  |                    |
| **Thai Language Quality**       | 10%    |            |               |                  |                    |
| **Fallback / Reliability**      | 10%    |            |               |                  |                    |
| **Privacy / Data Control**      | 5%     |            |               |                  |                    |
| **Ease of Model Switching**     | 5%     |            |               |                  |                    |
| **Total**                       | 100%   |            |               |                  |                    |

### 8.0.3 Recommended Architecture — LLM Routing Strategy

```
┌────────────────────────────────────────────────┐
│              RAG Service                         │
│                                                  │
│   LLMClient Interface                            │
│       │                                          │
│       ▼                                          │
│   ┌──────────────────────────────────────┐       │
│   │         OpenRouter Adapter            │       │
│   │  (OpenAI-compatible, single API key) │       │
│   └──────────┬───────────────────────────┘       │
│              │                                   │
│   ┌──────────▼───────────────────────────┐       │
│   │         OpenRouter Gateway            │       │
│   │  ┌──────────┐ ┌──────────┐ ┌───────┐ │       │
│   │  │ Claude   │ │  GPT-4o  │ │Llama3 │ │       │
│   │  └──────────┘ └──────────┘ └───────┘ │       │
│   │  ┌──────────┐ ┌──────────┐           │       │
│   │  │ Gemini   │ │DeepSeek  │  ...      │       │
│   │  └──────────┘ └──────────┘           │       │
│   └──────────────────────────────────────┘       │
└────────────────────────────────────────────────┘
```

> **ข้อดีเชิง Anti-Lock-in:** ถ้า OpenAI ขึ้นราคา, ถูก acquire, หรือ service down — เปลี่ยน model string บรรทัดเดียว ไม่ต้องแก้ integration

### 8.0.4 Task Checklist

- [ ] สมัคร OpenRouter account + ทดสอบ API
- [ ] PoC: RAG pipeline ใช้ OpenRouter — ทดลอง switch model หลายตัว
- [ ] Benchmark quality: Claude 3.5 Sonnet vs GPT-4o vs Llama 3.1 70B บน task ภาษาไทย
- [ ] ประเมิน cost: direct API vs OpenRouter (มี overhead pricing หรือไม่?)
- [ ] ทดสอบ automatic fallback (simulate provider down)
- [ ] ประเมิน OpenRouter reliability & SLA
- [ ] เขียน recommendation: ใช้ OpenRouter เป็น primary vs direct API

### 8.0.5 Key Questions to Answer

1. OpenRouter มี latency overhead เทียบกับ call ตรงมากแค่ไหน?
2. Pricing บน OpenRouter vs direct API — cost เพิ่มหรือเท่ากัน?
3. OpenRouter reliable พอสำหรับ production? (SLA, downtime history)
4. ถ้าเลือก OpenRouter — fallback plan ถ้า OpenRouter เองมีปัญหาคืออะไร?

---

## 9. Phase 4: API Layer & Authentication Design

**ระยะเวลา:** 5-7 วัน
**เป้าหมาย:** ออกแบบ Omnichannel API และระบบ Auth ที่รองรับ Employee + Customer

### 8.1 API Framework Selection

| Framework       | Language | หมายเหตุ                                                |
|-----------------|----------|---------------------------------------------------------|
| **FastAPI**     | Python   | Recommended — async, auto docs, type hints, ecosystem    |
| **Flask**       | Python   | Simpler, but less modern async support                   |
| **Express/Nest**| Node.js  | ถ้าทีมถนัด JS — but mismatch กับ ML ecosystem           |

> **Working assumption:** FastAPI เป็น strong candidate เนื่องจาก Python ecosystem alignment กับ ML/RAG libraries

### 8.2 Omnichannel API Design

**Core Principle:** Client-agnostic API — ทุก platform ใช้ API เดียวกัน

```
POST /api/v1/chat/completions        # Main RAG query endpoint
POST /api/v1/documents/upload         # Upload documents
GET  /api/v1/documents/search         # Search documents (non-RAG)
POST /api/v1/documents/index          # Trigger indexing
GET  /api/v1/collections              # List document collections
POST /api/v1/feedback                 # User feedback on answers

# Platform-specific webhooks (adapter layer)
POST /api/v1/webhooks/line            # LINE webhook receiver
POST /api/v1/webhooks/discord         # Discord webhook receiver
```

**Channel Adapter Pattern:**

```
┌─────────┐    ┌─────────┐    ┌─────────────┐
│ LINE    │───▶│ LINE    │───▶│             │
│ Webhook │    │ Adapter │    │             │
└─────────┘    └─────────┘    │   Core RAG  │
                               │   Service   │
┌─────────┐    ┌─────────┐    │   (Unified) │
│ Discord │───▶│ Discord │───▶│             │
│ Bot     │    │ Adapter │    │             │
└─────────┘    └─────────┘    │             │
                               │             │
┌─────────┐    Direct API     │             │
│ Web App │──────────────────▶│             │
└─────────┘                    └─────────────┘
```

### 8.3 Authentication & Authorization Design

#### 8.3.1 User Types

| User Type     | Description                          | Access Level                              |
|---------------|--------------------------------------|-------------------------------------------|
| **Employee**  | Internal staff                       | Access to internal knowledge base, admin   |
| **Customer**  | External users                       | Access to customer-facing knowledge only   |
| **Admin**     | System administrators                | Full access, user management               |
| **Service**   | API keys for platform integrations   | Scoped access per integration              |

#### 8.3.2 Auth Strategy Options

| Strategy                  | Pros                                        | Cons                                          |
|---------------------------|---------------------------------------------|-----------------------------------------------|
| **JWT + RBAC**            | Simple, well-understood, stateless          | Role explosion ถ้า permission ซับซ้อน          |
| **JWT + ABAC**            | Flexible, fine-grained, policy-based        | ซับซ้อนกว่า, ต้อง design policy engine          |
| **OAuth 2.0 + OIDC**     | Standard, SSO support, third-party login    | Complexity ของ flow management                 |
| **API Key + Scoped Perms**| Simple for service-to-service               | ไม่เหมาะกับ end-user auth                      |

**Recommended Hybrid Approach:**

```
Authentication:  OAuth 2.0 / OIDC  →  JWT tokens
Authorization:   RBAC (roles) + ABAC (attribute-based policies) hybrid

Employee login:  SSO via corporate IdP (e.g., Google Workspace, Azure AD)
Customer login:  Email/password + social login (LINE Login, Google)
Service auth:    API keys with scoped permissions
```

#### 8.3.3 Permission Model — Data Access Control

```
┌─────────────────────────────────────────────────────┐
│                Permission Matrix                      │
├──────────────────┬──────────┬──────────┬─────────────┤
│ Resource         │ Employee │ Customer │ Admin       │
├──────────────────┼──────────┼──────────┼─────────────┤
│ Internal KB      │ ✅ Read  │ ❌       │ ✅ CRUD     │
│ Customer KB      │ ✅ Read  │ ✅ Read  │ ✅ CRUD     │
│ Confidential KB  │ ❌       │ ❌       │ ✅ Read     │
│ Upload Docs      │ ✅       │ ❌       │ ✅          │
│ User Management  │ ❌       │ ❌       │ ✅          │
│ System Config    │ ❌       │ ❌       │ ✅          │
│ Query History    │ Own only │ Own only │ ✅ All      │
│ Analytics        │ ✅ Read  │ ❌       │ ✅ Read     │
└──────────────────┴──────────┴──────────┴─────────────┘
```

**Critical Design Point — Retrieval Filtering:**
- Vector search ต้อง filter ตาม user permissions ด้วย
- ทุก document ต้องมี `access_level` metadata
- Retrieval query ต้อง include permission filter:
  ```
  vector_search(query, filter={"access_level": user.allowed_levels})
  ```

#### 8.3.4 Auth Libraries to Evaluate

| Library/Service   | Type            | หมายเหตุ                              |
|-------------------|-----------------|---------------------------------------|
| **Keycloak**      | Self-hosted IdP | Full-featured, OIDC, complex setup     |
| **Auth0**         | Managed         | Easy, but vendor lock-in risk          |
| **Supabase Auth** | Managed/OSS     | Simple, PostgreSQL-based               |
| **Custom JWT**    | Custom          | Full control, more work                |
| **Authlib**       | Python library  | OAuth 2.0 toolkit for FastAPI          |

### 8.4 Task Checklist

- [ ] Design API schema (OpenAPI spec)
- [ ] Design auth flow diagrams (Employee, Customer, Service)
- [ ] Evaluate auth libraries/services (Keycloak vs Auth0 vs custom)
- [ ] Design permission model (RBAC/ABAC schema)
- [ ] Design document-level access control for vector search filtering
- [ ] PoC: FastAPI + JWT auth implementation
- [ ] PoC: LINE channel adapter
- [ ] PoC: Permission-filtered vector search
- [ ] Document API design decisions

### 8.5 Key Questions to Answer

1. Keycloak self-hosted vs Auth0 managed — trade-off ของ control vs operational cost?
2. RBAC เพียงพอหรือต้อง ABAC? (depends on permission granularity needed)
3. Document-level access control ทำที่ application layer หรือ vector DB layer?
4. Rate limiting strategy สำหรับ customer vs employee ต่างกันอย่างไร?
5. Multi-tenancy design — แยก data ระดับ collection หรือ metadata filter?

---

## 9. Phase 5: Integration Testing

**ระยะเวลา:** 5-7 วัน
**เป้าหมาย:** ทดสอบ selected components ทำงานร่วมกันได้ดีใน end-to-end flow

### 9.1 Integration Test Scenarios

| #  | Scenario                                    | Components Tested                              |
|----|---------------------------------------------|------------------------------------------------|
| 1  | Employee uploads document & queries it      | API → Auth → Ingest → Embed → VectorDB → LLM  |
| 2  | Customer queries — sees only allowed docs   | API → Auth → Permission Filter → VectorDB      |
| 3  | LINE user sends question & gets answer      | LINE Adapter → API → RAG Pipeline → Response   |
| 4  | Concurrent queries under load               | API → VectorDB → LLM (load testing)            |
| 5  | Component swap test                         | Swap VectorDB / Embedder / LLM — verify works  |
| 6  | Error handling — LLM timeout               | API → RAG Pipeline → Fallback behavior          |
| 7  | Thai language end-to-end                    | Thai query → Embed → Retrieve → Thai response   |

### 9.2 Performance Targets (Draft)

| Metric                       | Target                | หมายเหตุ                          |
|------------------------------|-----------------------|-----------------------------------|
| End-to-end latency (p50)     | < 3 seconds           | Including LLM generation          |
| End-to-end latency (p95)     | < 8 seconds           | Including LLM generation          |
| Retrieval latency (p95)      | < 200ms               | Vector search only                |
| Throughput                   | > 50 req/sec          | Concurrent users                  |
| Retrieval relevance          | > 80% Recall@5        | Manual evaluation on test set     |
| Uptime target                | 99.5%                 | Production SLO                    |

> หมายเหตุ: targets เหล่านี้เป็น draft — จะ finalize หลังจากรู้ production requirements ชัดเจนขึ้น

### 9.3 Task Checklist

- [ ] Setup end-to-end test environment (Docker Compose)
- [ ] Implement integration test suite
- [ ] Run Scenario 1-7 tests
- [ ] Load test with locust/k6
- [ ] Component swap verification test
- [ ] Document integration test results
- [ ] Identify integration issues & mitigations

---

## 10. Phase 6: RFC Document & Knowledge Sharing

**ระยะเวลา:** 3-5 วัน
**เป้าหมาย:** รวบรวมผลทั้งหมดเป็น RFC document และเตรียม Knowledge Sharing session

### 10.1 RFC Document Structure

```
RFC: RAG System Tech Stack Selection
├── 1. Executive Summary
├── 2. Problem Statement
├── 3. Requirements (Functional & Non-Functional)
├── 4. Options Evaluated
│   ├── 4.1 Vector Database — comparison & recommendation
│   ├── 4.2 RAG Framework — comparison & recommendation
│   ├── 4.3 Embedding Model — comparison & recommendation
│   ├── 4.4 API & Auth — design & recommendation
│   └── 4.5 Anti-Vendor-Lock-in — architecture patterns
├── 5. Recommended Architecture
│   ├── 5.1 System diagram
│   ├── 5.2 Component selection rationale
│   ├── 5.3 Trade-offs acknowledged
│   └── 5.4 Migration path (if needs change later)
├── 6. Proof-of-Concept Results
│   ├── 6.1 Benchmark data
│   ├── 6.2 Integration test results
│   └── 6.3 Demo
├── 7. Cost Analysis
├── 8. Risks & Mitigations
├── 9. Implementation Roadmap
├── 10. Decision Log (ADRs)
└── Appendices
    ├── A. Raw benchmark data
    ├── B. PoC source code links
    └── C. Reference materials
```

### 10.2 Knowledge Sharing Presentation

**Audience:** Engineering team + พี่ตั๊ก (Senior)
**Format:** 45-60 min presentation + 15-30 min Q&A
**Goal:** Team consensus on Tech Stack

**Slide Outline:**
1. Why RAG? (2 min) — context setting
2. Architecture Overview (5 min) — target system design
3. Vector DB Comparison (10 min) — results + recommendation
4. RAG Framework: Build vs Buy (10 min) — results + recommendation
5. Embedding Models (5 min) — results + recommendation
6. API & Auth Design (10 min) — omnichannel + permission model
7. Anti-Vendor-Lock-in Strategy (5 min) — architecture principles
8. Live Demo of PoC (5 min)
9. Recommended Tech Stack & Roadmap (5 min)
10. Q&A / Discussion (15-30 min)

### 10.3 Task Checklist

- [ ] รวบรวม benchmark data จากทุก phase
- [ ] เขียน RFC document (full version)
- [ ] สร้าง Architecture Decision Records (ADRs)
- [ ] เตรียม presentation slides
- [ ] เตรียม PoC demo
- [ ] Review RFC กับ 1-2 คนก่อน present
- [ ] Schedule Knowledge Sharing session
- [ ] Present & facilitate discussion
- [ ] บันทึก feedback และ decisions
- [ ] Finalize RFC with team consensus

---

## 11. Decision Criteria & Weighting

### 11.1 Overall Tech Stack Decision Factors

| Factor                         | Weight | Description                                                      |
|--------------------------------|--------|------------------------------------------------------------------|
| **Production Readiness**       | 20%    | Proven in production? Stable API? Good documentation?             |
| **Thai Language Support**      | 15%    | รองรับภาษาไทยได้ดีแค่ไหน (critical for our use case)             |
| **Operational Complexity**     | 15%    | ทีมเราดูแลได้ไหม? ต้องการ DevOps effort มากแค่ไหน?                |
| **Anti-Vendor-Lock-in**        | 15%    | Swap component ได้ง่ายแค่ไหน? Open standards?                     |
| **Performance**                | 10%    | Latency, throughput ตรงตาม targets หรือไม่                       |
| **Cost (TCO)**                 | 10%    | Total Cost of Ownership ทั้ง license, infra, operational          |
| **Developer Experience**       | 10%    | ใช้งานง่ายไหม? ทีมเรียนรู้เร็วแค่ไหน? Debugging ง่ายไหม?         |
| **Community & Ecosystem**      | 5%     | Community ใหญ่ไหม? มี plugins/integrations เยอะไหม?               |

### 11.2 Decision Making Process

1. **Individual scoring** — แต่ละคนให้คะแนนแยก
2. **Group discussion** — discuss ความแตกต่างของ scores
3. **Weighted calculation** — คำนวณ weighted score
4. **Consensus check** — ทุกคน (รวมพี่ตั๊ก) ต้อง agree หรืออย่างน้อย "can live with it"
5. **Document decision** — บันทึกเหตุผลใน ADR

### 11.3 Scoring Scale

| Score | Meaning                                    |
|-------|---------------------------------------------|
| 5     | Excellent — ตอบโจทย์ได้ดีมาก ไม่มีข้อเสียสำคัญ |
| 4     | Good — ดี มีข้อเสียเล็กน้อย                   |
| 3     | Adequate — พอใช้ได้ มี trade-off ที่ยอมรับได้   |
| 2     | Poor — มีปัญหาสำคัญ ต้องมี workaround         |
| 1     | Unacceptable — ไม่เหมาะกับ use case เรา       |

---

## 12. Risks & Blockers

### 12.1 Risk Register

| #  | Risk                                          | Probability | Impact | Mitigation                                                        |
|----|-----------------------------------------------|-------------|--------|-------------------------------------------------------------------|
| R1 | Thai language support ไม่ดีพอในทุก model       | Medium      | High   | ทดสอบ Thai-specific models, เตรียม custom tokenization pipeline    |
| R2 | Framework เปลี่ยน API / ถูก acquire            | Medium      | High   | Abstraction layer + multi-provider testing (Anti-lock-in)         |
| R3 | Vector DB performance ไม่ scale ตาม expected   | Low         | High   | Benchmark ที่ realistic scale, มี fallback option                  |
| R4 | LLM API cost สูงกว่า budget                    | Medium      | Medium | เตรียม self-hosted LLM option, caching strategy                    |
| R5 | Spike ใช้เวลานานเกินไป scope creep             | Medium      | Medium | Strict timeboxing, cut scope ถ้าจำเป็น, focus on decisions         |
| R6 | ทีมไม่ consensus — ตัดสินใจไม่ได้               | Low         | High   | Decision criteria ชัดเจนตั้งแต่ต้น, weighted scoring objective       |
| R7 | Security concerns กับ external LLM APIs        | Medium      | High   | Data classification, PII filtering before sending to LLM           |
| R8 | Permission-filtered search ทำให้ performance แย่| Medium      | Medium | Benchmark filtered vs unfiltered, pre-filtering design              |

### 12.2 Blockers

| #  | Blocker                                        | Status   | Owner    | Resolution                                    |
|----|------------------------------------------------|----------|----------|-----------------------------------------------|
| B1 | API keys สำหรับ LLM providers                  | Pending  | TBD      | ขอ budget — พิจารณา OpenRouter key เดียวแทนหลาย keys (OpenAI, Anthropic, etc.) |
| B2 | Test dataset — sensitive data ใช้ไม่ได้          | Pending  | TBD      | สร้าง synthetic dataset หรือ anonymize           |
| B3 | Infrastructure สำหรับ benchmark (GPU, etc.)     | Pending  | TBD      | Cloud instance หรือ on-prem GPU?                |
| B4 | Clear production requirements (scale, SLO)     | Pending  | TBD      | Confirm กับ product owner / stakeholders        |

---

## 13. Timeline & Milestones

### 13.1 Estimated Timeline

```
Week 1-2  ──▶  Phase 1: Vector DB Comparison
Week 2-3  ──▶  Phase 2: RAG Framework Comparison
Week 3    ──▶  Phase 3: Embedding Model Comparison
Week 3-4  ──▶  Phase 4: API & Auth Design
Week 4-5  ──▶  Phase 5: Integration Testing
Week 5-6  ──▶  Phase 6: RFC & Knowledge Sharing
```

> Total: approximately 5-6 weeks (flexible based on findings and team availability)

### 13.2 Milestones

| Milestone                           | Target          | Deliverable                              |
|-------------------------------------|-----------------|------------------------------------------|
| M1: Vector DB shortlisted           | End of Week 2   | Comparison table + top 2 candidates       |
| M2: Framework decision (Build/Buy)  | End of Week 3   | Build vs Buy recommendation + rationale   |
| M3: Embedding model selected        | End of Week 3   | Thai evaluation results + selection        |
| M4: API & Auth design complete      | End of Week 4   | OpenAPI spec + Auth flow diagrams          |
| M5: Integration tests pass          | End of Week 5   | E2E demo working + benchmark results      |
| M6: RFC published & presented       | End of Week 6   | RFC document + team consensus              |

### 13.3 Phase Dependencies

```
Phase 1 (Vector DB) ─────────────────────┐
                                          ├──▶ Phase 5 (Integration)
Phase 2 (Framework) ──┐                  │
                       ├──▶ Phase 4 ─────┘
Phase 3 (Embedding) ──┘     (API/Auth)
                                          └──▶ Phase 6 (RFC/KS)
```

- Phase 1, 2, 3 สามารถทำ parallel ได้บางส่วน
- Phase 4 ต้องรอ direction จาก Phase 2 (framework choice affects API design)
- Phase 5 ต้องรอ Phase 1-4 เสร็จ (needs all components)
- Phase 6 ต้องรอ Phase 5 เสร็จ (needs integration results)

---

## 14. Appendices

### 14.1 Repository Structure (Proposed)

```
spike-rak/
├── plan.md                          # This document
├── README.md                        # Project overview & getting started
├── docs/
│   ├── rfc/                         # Final RFC document
│   │   └── rfc-rag-tech-stack.md
│   ├── adr/                         # Architecture Decision Records
│   │   ├── 001-vector-db.md
│   │   ├── 002-rag-framework.md
│   │   ├── 003-embedding-model.md
│   │   └── 004-auth-strategy.md
│   └── presentation/               # Knowledge sharing slides
├── benchmarks/
│   ├── vector-db/                   # Vector DB benchmark scripts & results
│   ├── embedding/                   # Embedding model evaluation
│   └── results/                     # Consolidated benchmark data
├── poc/
│   ├── llamaindex/                  # LlamaIndex PoC
│   ├── langchain/                   # LangChain PoC
│   ├── haystack/                    # Haystack PoC
│   ├── bare-metal/                  # Custom build PoC
│   └── shared/                      # Shared test data & utilities
├── api-design/
│   ├── openapi.yaml                 # API specification
│   └── auth-flows/                  # Auth flow diagrams
├── docker/
│   ├── docker-compose.vector-db.yml # Vector DB instances
│   ├── docker-compose.rag.yml       # RAG service stack
│   └── docker-compose.full.yml      # Full integration stack
├── datasets/
│   ├── thai/                        # Thai test documents
│   ├── english/                     # English test documents
│   └── mixed/                       # Mixed language documents
└── scripts/
    ├── setup.sh                     # Environment setup
    ├── benchmark.py                 # Benchmark runner
    └── evaluate.py                  # Evaluation metrics
```

### 14.2 Reference Materials

| Resource                                    | URL / Location                                  |
|---------------------------------------------|------------------------------------------------|
| Milvus Documentation                        | https://milvus.io/docs                          |
| OpenSearch Vector Search                    | https://opensearch.org/docs/latest/search-plugins/knn/ |
| pgvector                                    | https://github.com/pgvector/pgvector            |
| Qdrant                                      | https://qdrant.tech/documentation/              |
| Weaviate                                    | https://weaviate.io/developers/weaviate          |
| LlamaIndex                                 | https://docs.llamaindex.ai/                      |
| LangChain                                  | https://docs.langchain.com/                      |
| Haystack                                   | https://docs.haystack.deepset.ai/                |
| MTEB Benchmark (Embedding)                 | https://huggingface.co/spaces/mteb/leaderboard   |
| ANN Benchmarks                              | https://ann-benchmarks.com/                      |
| FastAPI                                     | https://fastapi.tiangolo.com/                    |

### 14.3 Glossary

| Term          | Definition                                                                                 |
|---------------|--------------------------------------------------------------------------------------------|
| **RAG**       | Retrieval-Augmented Generation — เทคนิคที่ดึงข้อมูลจาก knowledge base มาเป็น context ให้ LLM |
| **Vector DB** | ฐานข้อมูลที่ออกแบบมาเพื่อเก็บและค้นหา vector embeddings                                     |
| **Embedding** | การแปลงข้อความเป็น numerical vector ที่เก็บ semantic meaning                                 |
| **ANN**       | Approximate Nearest Neighbor — อัลกอริทึมค้นหา vector ที่ใกล้เคียงที่สุด                      |
| **RBAC**      | Role-Based Access Control — ควบคุมสิทธิ์ตาม role ของ user                                    |
| **ABAC**      | Attribute-Based Access Control — ควบคุมสิทธิ์ตาม attribute/policy                            |
| **OIDC**      | OpenID Connect — authentication protocol บน OAuth 2.0                                       |
| **TCO**       | Total Cost of Ownership — ต้นทุนรวมทั้งหมดของการใช้งาน                                       |
| **ADR**       | Architecture Decision Record — บันทึกเหตุผลของการตัดสินใจด้าน architecture                   |
| **RFC**       | Request for Comments — เอกสารข้อเสนอทางเทคนิคให้ทีม review                                   |

---

## Changelog

| Date       | Author | Change                        |
|------------|--------|-------------------------------|
| 2026-03-31 | Team   | Initial plan creation          |

---

> **Next Action:** Review this plan with the team, resolve blockers (B1-B4), and begin Phase 1.
