# ADR-002: RAG Framework Approach (Build vs Buy)

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-002 |
| **สถานะ** | 🟡 Draft |
| **วันที่** | 2026-03-31 |
| **Deciders** | Engineering Team, พี่ตั๊ก |
| **Phase** | Phase 2 |

---

## บริบท (Context)

เราต้องตัดสินใจว่าจะ:
- **Build from Scratch (Bare Metal)** — เขียน RAG pipeline เอง ใช้แค่ libraries ที่จำเป็น
- **ใช้ Framework สำเร็จรูป** — LlamaIndex, LangChain, หรือ Haystack

นี่เป็น decision ที่มีผลระยะยาวมาก เพราะส่งผลต่อ:
- ความยาก/ง่ายในการ maintain code
- ความเสี่ยง vendor lock-in ต่อ framework
- Speed ในการพัฒนา features ใหม่
- Debugging และ observability

เราทดสอบ: **LlamaIndex**, **LangChain**, **Haystack**, **Bare Metal**

---

## Decision

> **[TODO หลัง Phase 2 เสร็จ — กรอกตรงนี้]**
>
> เลือก: _______________

---

## เหตุผล (Rationale)

> **[TODO]** อธิบายเหตุผลที่เลือก

**Evaluation summary:**

| Criteria | ตัวที่เลือก | หมายเหตุ |
|----------|-----------|---------|
| Lines of code (PoC) | — | — |
| Time to implement PoC | — | — |
| Query latency | — | — |
| Component swap ease | — | — |
| Debugging experience | — | — |

**Key findings จาก Phase 2:**
- [ ] TODO
- [ ] TODO

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- [TODO]

**ข้อเสีย / Trade-offs:**
- [TODO]

**ถ้าเลือก Framework — สิ่งที่ต้องทำเพิ่ม:**
- [ ] Wrap ด้วย abstraction layer เพื่อป้องกัน lock-in
- [ ] กำหนด policy สำหรับ framework version upgrades
- [ ] Document ส่วนที่ใช้ framework API ตรง (ไม่ผ่าน abstraction)

**ถ้าเลือก Bare Metal — สิ่งที่ต้องทำเพิ่ม:**
- [ ] Design และ document RAG pipeline architecture
- [ ] เตรียม chunking strategies
- [ ] เตรียม prompt engineering guidelines

---

## Migration Path

ถ้าต้องเปลี่ยนในอนาคต:
> [TODO] เนื่องจาก pipeline อยู่หลัง `RAGPipeline` interface — เปลี่ยนได้โดยแก้ adapter

---

## ข้อมูลที่ใช้ตัดสินใจ

- Evaluation results: `benchmarks/rag-framework/results/`
- Phase 2 notes: `docs/phases/phase-2-rag-framework.md`
- Build vs Buy analysis: `plan.md` Section 6.3
