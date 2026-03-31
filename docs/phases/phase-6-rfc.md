# Phase 6: RFC Document & Knowledge Sharing

## คืออะไร?

Phase 6 คือขั้นตอนสุดท้าย — รวบรวมผลการวิจัยจาก Phase 1-5 ทั้งหมดมาเขียนเป็น **RFC Document** และนำเสนอใน **Knowledge Sharing Session** เพื่อให้ทีมตัดสินใจร่วมกันเรื่อง Tech Stack

**RFC (Request for Comments)** คือเอกสาร formal ที่อธิบาย:
- ปัญหาที่ต้องการแก้
- ตัวเลือกที่ประเมินแล้ว
- ข้อมูล/หลักฐานสนับสนุน
- คำแนะนำ + เหตุผล
- เปิดรับ feedback ก่อนตัดสินใจ

---

## Definition of Done (สิ่งที่ต้องทำให้เสร็จ)

- [ ] RFC Document ฉบับสมบูรณ์
- [ ] Architecture Decision Records (ADRs) ทุก decision สำคัญ
- [ ] Presentation slides (45-60 นาที)
- [ ] PoC Demo พร้อม
- [ ] Review กับ 1-2 คนก่อน present
- [ ] Knowledge Sharing session scheduled + presented
- [ ] Team consensus บันทึกแล้ว
- [ ] RFC finalized พร้อม sign-off

---

## โครงสร้าง RFC Document

```
RFC: RAG System Tech Stack Selection
│
├── 1. Executive Summary (1 หน้า)
│      ← สรุปสั้น สำหรับคนที่อ่านแค่หน้าเดียว
│
├── 2. Problem Statement
│      ← ทำไมต้องมีระบบ RAG? ปัญหาที่ต้องแก้คืออะไร?
│
├── 3. Requirements
│      ├── Functional requirements
│      └── Non-functional requirements (latency, scale, cost)
│
├── 4. Options Evaluated
│      ├── 4.1 Vector Database — comparison table + recommendation
│      ├── 4.2 RAG Framework — comparison table + recommendation
│      ├── 4.3 Embedding Model — comparison table + recommendation
│      ├── 4.4 API & Auth — design decisions + recommendation
│      └── 4.5 Anti-Vendor-Lock-in — architecture patterns
│
├── 5. Recommended Architecture
│      ├── 5.1 System diagram (final recommended stack)
│      ├── 5.2 Component selection rationale (ทำไมเลือกตัวนี้)
│      ├── 5.3 Trade-offs acknowledged (ยอมรับว่ามี trade-off อะไร)
│      └── 5.4 Migration path (ถ้าต้องเปลี่ยนในอนาคต)
│
├── 6. Proof-of-Concept Results
│      ├── 6.1 Benchmark data (Phase 1-3.5)
│      ├── 6.2 Integration test results (Phase 5)
│      └── 6.3 Demo
│
├── 7. Cost Analysis
│      └── TCO comparison — options ต่างๆ ที่ scale ต่างๆ
│
├── 8. Risks & Mitigations
│
├── 9. Implementation Roadmap
│      └── ถ้า approve — step ถัดไปคืออะไร?
│
├── 10. Decision Log (ADRs)
│      └── บันทึก decision แต่ละข้อพร้อมเหตุผล
│
└── Appendices
       ├── A. Raw benchmark data
       ├── B. PoC source code links
       └── C. Reference materials
```

---

## Architecture Decision Records (ADRs)

ADR คือเอกสารสั้นๆ บันทึก decision สำคัญแต่ละข้อ:

```markdown
## ADR-001: เลือก [ชื่อ Component] สำหรับ Vector DB

**สถานะ:** Accepted / Proposed / Deprecated

**บริบท (Context):**
[อธิบายสถานการณ์และปัญหา]

**Decision:**
[เลือกอะไร]

**เหตุผล:**
[ทำไมถึงเลือก]

**ผลที่ตามมา (Consequences):**
[ข้อดี / ข้อเสีย / สิ่งที่ต้องทำตามมา]
```

ตัวอย่าง ADRs ที่ต้องเขียน:
- ADR-001: Vector DB selection
- ADR-002: RAG Framework approach (build vs buy)
- ADR-003: Embedding Model selection
- ADR-004: LLM Provider strategy
- ADR-005: Auth approach (JWT+RBAC vs OAuth+ABAC)
- ADR-006: Anti-vendor-lock-in architecture pattern

---

## Knowledge Sharing Presentation

**ผู้ฟัง:** Engineering team + พี่ตั๊ก (Senior)
**รูปแบบ:** 45-60 นาที presentation + 15-30 นาที Q&A
**เป้าหมาย:** Team consensus บน Tech Stack ที่เลือก

### Slide Outline

| Slide | หัวข้อ | เวลา |
|-------|--------|------|
| 1-3 | Why RAG? — context setting | 2 นาที |
| 4-7 | Architecture Overview — target system design | 5 นาที |
| 8-12 | Vector DB Comparison — results + recommendation | 10 นาที |
| 13-17 | RAG Framework: Build vs Buy — results | 10 นาที |
| 18-20 | Embedding Models — results + recommendation | 5 นาที |
| 21-25 | API & Auth Design — omnichannel + permission model | 10 นาที |
| 26-28 | Anti-Vendor-Lock-in Strategy | 5 นาที |
| 29 | Live Demo of PoC | 5 นาที |
| 30-32 | Recommended Tech Stack & Roadmap | 5 นาที |
| — | Q&A / Discussion | 15-30 นาที |

---

## Checklist การเตรียมงาน

### เอกสาร
- [ ] รวบรวม benchmark results ทุก phase
- [ ] เขียน RFC draft
- [ ] สร้าง ADRs (อย่างน้อย 6 ตัว)
- [ ] Review RFC กับ 1-2 คน → แก้ไข
- [ ] RFC ฉบับสมบูรณ์

### Presentation
- [ ] สร้าง slides
- [ ] เตรียม live demo environment
- [ ] ซักซ้อม presentation (< 60 นาที)
- [ ] เตรียม backup demo (screen recording ในกรณี env มีปัญหา)

### Knowledge Sharing Session
- [ ] Schedule session กับ team
- [ ] ส่ง RFC draft ล่วงหน้า (≥ 2 วัน)
- [ ] Present + facilitate discussion
- [ ] บันทึก feedback และ decisions
- [ ] Finalize RFC พร้อม sign-off

---

## วิธีจัดเก็บ RFC และ ADRs

แนะนำให้สร้างไว้ใน repo นี้:

```
docs/
├── rfc/
│   └── RFC-001-rag-tech-stack.md    ← RFC document
└── adr/
    ├── ADR-001-vector-db.md
    ├── ADR-002-rag-framework.md
    ├── ADR-003-embedding-model.md
    ├── ADR-004-llm-provider.md
    ├── ADR-005-auth-approach.md
    └── ADR-006-anti-lock-in.md
```

---

## ผลลัพธ์ที่ได้ (Output)

1. **RFC Document** — เอกสาร formal สำหรับ decision making
2. **ADRs** — บันทึก 6+ decisions พร้อมเหตุผล
3. **Presentation slides** — สำหรับ Knowledge Sharing
4. **Team consensus** — agreement บน Tech Stack ที่จะใช้ใน production
5. **Implementation roadmap** — plan ขั้นถัดไปหลังจาก spike เสร็จ
