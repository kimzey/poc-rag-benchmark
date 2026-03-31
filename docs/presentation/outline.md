# Knowledge Sharing Presentation
## RAG System Tech Stack Selection

| ฟิลด์ | ค่า |
|------|-----|
| **Audience** | Engineering Team + พี่ตั๊ก (Senior) |
| **Duration** | 45-60 นาที presentation + 15-30 นาที Q&A |
| **Goal** | Team consensus on Tech Stack |
| **Format** | Slide presentation + Live Demo |
| **วันที่** | [TODO: กำหนดวัน] |

---

## โครงสร้าง Presentation

### Slide 1-2: Opening

**"ทำไมเราถึงอยู่ที่นี่วันนี้"**

- ปัญหาที่ต้องการแก้: ผู้ใช้ต้องค้นหาข้อมูลเองจากเอกสารหลายที่
- Vision: ระบบที่ตอบคำถามจาก knowledge base ได้ทันที — ทั้ง Web, LINE, Discord
- Spike นี้ใช้เวลา ~6 สัปดาห์ ทดสอบจริงกับ 15+ components

**Speaker notes:**  
อธิบาย scope ของ spike ว่าครอบคลุมอะไรบ้าง และทำไมต้องทำก่อน build จริง

---

### Slide 3: RAG คืออะไร? (สำหรับคนที่ยังไม่คุ้น)

```
ถามคำถาม
    │
    ▼
[ระบบค้นหาใน Knowledge Base]  ←── เอกสาร + ข้อมูลภายใน
    │
    ▼
[AI สร้างคำตอบจากข้อมูลที่ค้นเจอ]
    │
    ▼
คำตอบที่อิงจากข้อมูลจริงของเรา
```

**ต่างจาก ChatGPT ทั่วไปยังไง:**
- ChatGPT ตอบจากความรู้ที่ train มา (อาจ outdated, ไม่รู้ข้อมูลภายใน)
- RAG ตอบจากเอกสารที่เราใส่เข้าไป (accurate, up-to-date, ควบคุมได้)

---

### Slide 4-5: System Architecture (Target)

**แสดง architecture diagram จาก plan.md Section 1.3**

Component หลัก 4 ส่วน:
1. **Vector Database** — คลังเก็บ + ค้นหาเอกสาร
2. **Embedding Model** — แปลงข้อความเป็นตัวเลข
3. **LLM Provider** — สร้างคำตอบ
4. **API Layer + Auth** — เชื่อมทุก platform + ควบคุม access

**Slide 5: Omnichannel Architecture**

```
LINE ──┐
Web ───┤── API Gateway ── RAG Service ── Knowledge Base
Discord┘
```

---

### Slide 6: Anti-Vendor-Lock-in Strategy

**"เราออกแบบให้เปลี่ยน component ได้ใน 1-2 วัน"**

แสดง Port & Adapter diagram:
```
Application → Interface → Adapter A
                       → Adapter B  (swap ได้โดยแก้ config)
                       → Adapter C
```

**ทำไมสำคัญ:**
- vendor ราคาขึ้น 5x → เราเปลี่ยนได้ทันที
- provider ล่ม → fallback ได้อัตโนมัติ
- technology ใหม่ดีกว่า → migrate ได้โดยไม่ rewrite

---

### Slide 7-9: Phase 1 — Vector Database Results

**Slide 7: ทดสอบอะไร?**
- 4 Vector DBs: Qdrant, pgvector, Milvus, OpenSearch
- ทดสอบที่ 10K และ 100K vectors
- วัด: latency, recall, operational complexity, cost

**Slide 8: Benchmark Results**
> [TODO: ใส่ตัวเลขจริงหลัง Phase 1]

| DB | p95 latency | Recall@10 | Ops complexity | TCO estimate |
|----|-------------|-----------|----------------|-------------|
| Qdrant | — | — | — | — |
| pgvector | — | — | — | — |
| Milvus | — | — | — | — |
| OpenSearch | — | — | — | — |

**Slide 9: Recommendation**
> [TODO] เลือก _____ เพราะ _____

**Key insight:**
> [TODO: เช่น "pgvector พอสำหรับ scale ของเรา ไม่จำเป็นต้องใช้ dedicated vector DB"]

---

### Slide 10-12: Phase 2 — RAG Framework Results

**Slide 10: Build vs Buy?**

| | Build from Scratch | Use Framework |
|-|-------------------|---------------|
| Time to production | 2-3 เดือน | 2-4 สัปดาห์ |
| Control | สูงสุด | จำกัด |
| Maintenance | สูง | ต่ำ-กลาง |
| Lock-in risk | ไม่มี | Medium |

**Slide 11: Framework Comparison Results**
> [TODO: ใส่ข้อมูลจริงหลัง Phase 2]

**Slide 12: Recommendation**
> [TODO] เลือก _____ เพราะ _____

---

### Slide 13-14: Phase 3 — Embedding Model Results

**Slide 13: Thai Language is Critical**

แสดงความสำคัญของ Thai support:
- Recall@5 (Thai) ต่างกันระหว่าง models
- open-source vs commercial: quality gap เท่าไหร่?
- cost: $0 local vs $X per 1M tokens

**Slide 14: Results + Recommendation**
> [TODO: ใส่ Recall@K, latency, cost comparison จริง]

---

### Slide 15-16: Phase 3.5 — LLM Provider Strategy

**Slide 15: OpenRouter — Anti-Lock-in ในทางปฏิบัติ**

```python
# เปลี่ยน LLM แค่แก้บรรทัดเดียว
model="anthropic/claude-3.5-sonnet"   # หรือ
model="openai/gpt-4o"                  # หรือ
model="meta-llama/llama-3.1-70b"      # ไม่ต้องแก้ code อื่น
```

**Slide 16: Cost + Quality Trade-off**
> [TODO: ใส่ comparison table จริง]

**Key question for team:** เราต้องการ quality ระดับไหน vs ยอมรับ cost เท่าไหร่?

---

### Slide 17-19: Phase 4 — API & Auth Design

**Slide 17: Omnichannel API Design**

Endpoint หลัก:
- `POST /api/v1/chat/completions` — RAG query
- `POST /api/v1/documents/upload` — Upload docs
- `POST /api/v1/webhooks/line` — LINE adapter

**Slide 18: Permission-Filtered Retrieval**

```
Employee query → เห็น internal + customer docs
Customer query → เห็นเฉพาะ customer docs
                 (filter ที่ Vector DB — ไม่ใช่แค่ API)
```

แสดง demo ความแตกต่าง Employee vs Customer response

**Slide 19: Auth Recommendation**
> [TODO] Short-term vs Long-term auth strategy

---

### Slide 20-21: Phase 5 — Integration Test Results

**Slide 20: 7 Scenarios ที่ทดสอบ**

| # | Scenario | Result |
|---|---------|--------|
| 1 | Employee upload & query | [TODO] |
| 2 | Customer permission filter | [TODO] |
| 3 | LINE webhook E2E | [TODO] |
| 4 | Concurrent queries | [TODO] |
| 5 | Component swap ✓ | [TODO] |
| 6 | LLM error handling | [TODO] |
| 7 | Thai language E2E | [TODO] |

**Slide 21: Performance vs Targets**

| Metric | Target | Actual | ✓/✗ |
|--------|--------|--------|-----|
| E2E p50 | < 3s | [TODO] | — |
| E2E p95 | < 8s | [TODO] | — |
| Throughput | > 50 rps | [TODO] | — |
| Thai Recall@5 | > 80% | [TODO] | — |

---

### Slide 22-23: Live Demo

**Slide 22: Demo Setup**

สิ่งที่จะ demo:
1. Login เป็น Employee → Query เรื่อง internal policy → เห็นผลลัพธ์
2. Login เป็น Customer → Query เหมือนกัน → ไม่เห็น internal docs
3. LINE message → ระบบตอบกลับ (ถ้ามี LINE integration)
4. Swap LLM model → response เปลี่ยนแค่แก้ config

**Slide 23: [Demo Slide — แสดง live]**

> **หมายเหตุสำหรับ presenter:**  
> เตรียม screen recording เป็น backup ในกรณี environment มีปัญหา  
> Demo URL: http://localhost:8000/docs

---

### Slide 24-25: Recommended Tech Stack

**Slide 24: สรุป — สิ่งที่เราแนะนำ**

> [TODO: กรอกหลัง Phase 1-5 เสร็จ]

| Component | ที่เลือก | เหตุผลหลัก |
|-----------|---------|-----------|
| Vector DB | [TODO] | [TODO] |
| RAG Approach | [TODO] | [TODO] |
| Embedding | [TODO] | [TODO] |
| LLM Provider | [TODO] | [TODO] |
| API | FastAPI | ecosystem, async, auto docs |
| Auth (v1) | [TODO] | [TODO] |

**Slide 25: Implementation Roadmap**

```
[TODO: Timeline ถ้า RFC ได้ approved]

Sprint 1: Core RAG pipeline
Sprint 2: API + Auth
Sprint 3: Channel adapters
Sprint 4: Production hardening
```

---

### Slide 26: Risks & Mitigations

Top 3 risks ที่ต้อง aware:

1. **Thai language quality** — Mitigation: ทดสอบ evaluation set ภาษาไทยก่อน launch
2. **LLM cost scaling** — Mitigation: self-hosted fallback + caching strategy
3. **Vendor reliability** — Mitigation: OpenRouter + circuit breaker pattern

---

### Slide 27: Q&A / Decision Time

**คำถามที่ต้องตัดสินใจร่วมกัน:**

1. เห็นด้วยกับ Tech Stack ที่แนะนำไหม?
2. มี requirements หรือ constraints อะไรที่เรายังไม่รู้?
3. Trade-offs ที่เสนอมา — ยอมรับได้ไหม?
4. Timeline สำหรับ implementation — ทีมพร้อมไหม?
5. Next steps คืออะไร?

**Goal:** ออกจากห้องนี้พร้อม **decision ที่ทุกคน agree** (หรืออย่างน้อย "can live with it")

---

## Notes สำหรับ Presenter

### ก่อน Present
- [ ] ทดสอบ demo environment (make api-run)
- [ ] เตรียม screen recording เป็น backup
- [ ] ส่ง RFC draft ให้ team อ่านล่วงหน้า ≥ 2 วัน
- [ ] Rehearse timing — ควรจบ slides ภายใน 50 นาที

### ระหว่าง Present
- Data-driven เสมอ — อ้างอิง benchmark results
- เน้น trade-offs ชัดเจน — ไม่มีตัวเลือกใดดีทุกด้าน
- เปิดรับ feedback — session นี้คือ discussion ไม่ใช่ announcement

### หลัง Present
- [ ] บันทึก feedback และ decisions ทันที
- [ ] Update RFC ตาม feedback
- [ ] ได้รับ sign-off จาก stakeholders
- [ ] Archive decisions ใน ADRs
