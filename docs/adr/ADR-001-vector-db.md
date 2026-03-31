# ADR-001: Vector Database Selection

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-001 |
| **สถานะ** | 🟡 Draft |
| **วันที่** | 2026-03-31 |
| **Deciders** | Engineering Team, พี่ตั๊ก |
| **Phase** | Phase 1 |

---

## บริบท (Context)

ระบบ RAG ต้องการ Vector Database สำหรับจัดเก็บและค้นหา vector embeddings ของเอกสาร เราต้องการ DB ที่:
- รองรับ semantic search (ANN — Approximate Nearest Neighbor)
- รองรับ metadata filtering (สำหรับ permission-based access control)
- ทำงานได้ใน production ที่ scale ของเรา
- Operational complexity ไม่สูงเกินที่ทีมจะ maintain ได้

เราทดสอบ: **Qdrant**, **pgvector**, **Milvus**, **OpenSearch**

---

## Decision

> **[TODO หลัง Phase 1 เสร็จ — กรอกตรงนี้]**
>
> เลือก: _______________

---

## เหตุผล (Rationale)

> **[TODO]** อธิบายเหตุผลที่เลือก โดยอิงจากผลลัพธ์จริง

**Benchmark summary:**

| Metric | ตัวที่เลือก | อันดับ 2 | ต่างกัน |
|--------|-----------|---------|--------|
| Query latency p50 | — | — | — |
| Query latency p95 | — | — | — |
| Recall@10 | — | — | — |
| Operational complexity | — | — | — |

**เหตุผลหลักที่เลือก:**
- [ ] TODO: เหตุผล 1
- [ ] TODO: เหตุผล 2
- [ ] TODO: เหตุผล 3

**เหตุผลที่ไม่เลือกตัวอื่น:**

| ตัวเลือก | เหตุผลที่ไม่เลือก |
|---------|-----------------|
| Qdrant | [TODO] |
| pgvector | [TODO] |
| Milvus | [TODO] |
| OpenSearch | [TODO] |

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- [TODO]

**ข้อเสีย / Trade-offs:**
- [TODO]

**สิ่งที่ต้องทำตามมา:**
- [ ] Setup production infrastructure
- [ ] เขียน adapter ใน production codebase
- [ ] วางแผน backup/restore strategy
- [ ] Document operational runbook

---

## Migration Path

ถ้าต้องเปลี่ยนในอนาคต:
> [TODO] อธิบาย migration path ไป DB อื่น — ใช้เวลานานแค่ไหน, ต้องทำอะไรบ้าง

เนื่องจาก code ใช้ `VectorDBClient` interface — แก้เฉพาะ adapter + config, ไม่ต้องแก้ business logic

---

## ข้อมูลที่ใช้ตัดสินใจ

- Benchmark results: `benchmarks/vector-db/results/`
- Phase 1 notes: `docs/phases/phase-1-vector-db.md`
- Comparison criteria: `plan.md` Section 5.2
