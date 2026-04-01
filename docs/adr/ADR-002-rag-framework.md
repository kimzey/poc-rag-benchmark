# ADR-002: RAG Framework Approach (Build vs Buy)

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-002 |
| **สถานะ** | 🟢 Accepted |
| **วันที่** | 2026-04-01 |
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

**เลือก: LlamaIndex** (พร้อม Bare Metal เป็น reference implementation)

LlamaIndex ให้ abstraction ที่ดีที่สุดโดยใช้ LOC น้อยที่สุด (84 lines) ในขณะที่ยังให้ความยืดหยุ่นในการ swap components ตาม ADR-006

---

## เหตุผล (Rationale)

**Evaluation summary — Phase 2 benchmark (10 คำถาม, embedding=text-embedding-3-small, LLM=gpt-4o-mini):**

| Framework | Chunks สร้าง | Index time (ms) | Lines of Code | คุณภาพคำตอบ |
|-----------|------------|----------------|--------------|------------|
| bare_metal | 5 | 963.5 | 103 | ✅ ตอบถูกทุกข้อ |
| **llamaindex** | **17** | **1,596.4** | **84** | **✅ ตอบถูกทุกข้อ** |
| langchain | 33 | 1,690.9 | 97 | ✅ ตอบถูกทุกข้อ |
| haystack | 5 | 863.3 | 142 | ✅ ตอบถูกทุกข้อ |

> หมายเหตุ: ทุก framework ตอบคำถามได้ถูกต้องทั้ง 10 ข้อ — ความต่างอยู่ที่ maintainability และ feature set

**Key findings จาก Phase 2:**
- ทุก framework ผ่าน functional test — ไม่มีตัวใด fail ในการตอบคำถาม
- LlamaIndex ใช้ LOC น้อยสุด (84) สะท้อน abstraction ที่ดี ไม่ต้องเขียน boilerplate
- Haystack ใช้ LOC มากสุด (142) แต่ indexing เร็วสุด — trade-off เรื่อง verbosity vs speed
- Bare metal ดีสำหรับ reference/learning แต่ต้องเขียน chunking, retrieval, และ prompt engineering เองทุกอย่าง
- LangChain สร้าง chunks มากที่สุด (33) — chunking strategy ต่างออกไปจาก default

**เหตุผลหลักที่เลือก LlamaIndex:**
- LOC น้อยสุดในกลุ่ม framework (84 lines) — less code = less maintenance burden
- Native support สำหรับ component swap (Vector DB, LLM, Embedding) ผ่าน abstraction
- Community และ documentation แข็งแรง, active development
- ง่ายต่อการ extend สำหรับ agentic use cases ในอนาคต

**เหตุผลที่ไม่เลือกตัวอื่น:**

| ตัวเลือก | เหตุผลที่ไม่เลือก |
|---------|-----------------|
| Bare Metal | ต้องเขียน infrastructure code เองทั้งหมด — เหมาะสำหรับ reference/learning แต่ maintenance cost สูงกว่าในระยะยาว |
| LangChain | LOC สูงกว่า LlamaIndex, chunking behavior ต่างจากที่คาด, API เปลี่ยนบ่อยระหว่าง major versions |
| Haystack | LOC สูงสุด (142), API verbose, community เล็กกว่า แม้จะ production-grade |

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- ลด boilerplate code ได้มาก เทียบกับ bare metal
- รองรับ advanced features (reranking, hybrid search, agents) ได้ง่าย
- Abstraction layer ทำให้ swap Vector DB หรือ LLM ได้โดยแก้ config

**ข้อเสีย / Trade-offs:**
- มี framework dependency — breaking changes ระหว่าง major versions เป็นไปได้
- Abstraction บางชั้น debug ยากกว่า bare metal
- Version pinning สำคัญ — ต้อง test ก่อน upgrade

**สิ่งที่ต้องทำ:**
- [ ] Wrap LlamaIndex ด้วย `BaseRAGPipeline` abstraction layer (ตาม ADR-006)
- [ ] กำหนด policy สำหรับ LlamaIndex version upgrades
- [ ] Document ส่วนที่ใช้ LlamaIndex API ตรงๆ (ไม่ผ่าน abstraction)
- [ ] Maintain bare_metal implementation เป็น reference ไว้เสมอ

---

## Migration Path

ถ้าต้องเปลี่ยนในอนาคต:
- เนื่องจาก pipeline อยู่หลัง `BaseRAGPipeline` interface — เปลี่ยนได้โดยแก้ adapter implementation เดียว
- Bare metal implementation ใน spike สามารถใช้เป็น migration target ได้ทันทีถ้า framework มีปัญหา

---

## ข้อมูลที่ใช้ตัดสินใจ

- Evaluation results: `benchmarks/rag-framework/results/`
- Phase 2 notes: `docs/phases/phase-2-rag-framework.md`
- Build vs Buy analysis: `plan.md` Section 6.3
