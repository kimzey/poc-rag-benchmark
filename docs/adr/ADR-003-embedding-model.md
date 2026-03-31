# ADR-003: Embedding Model Selection

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-003 |
| **สถานะ** | 🟡 Draft |
| **วันที่** | 2026-03-31 |
| **Deciders** | Engineering Team, พี่ตั๊ก |
| **Phase** | Phase 3 |

---

## บริบท (Context)

Embedding model เป็น component ที่ **มีผลต่อคุณภาพ retrieval โดยตรง** โดยเฉพาะภาษาไทยซึ่งเป็น first-class requirement ของระบบเรา

การตัดสินใจนี้มี trade-off หลักคือ:
- **Commercial models** (OpenAI) — คุณภาพสูง แต่มี cost ต่อ token + data ออกนอก
- **Open-source models** (BGE-M3, multilingual-E5) — ฟรี, data อยู่ใน org, แต่ต้องจัดการ infrastructure เอง

เราทดสอบ: **BGE-M3**, **multilingual-E5-large**, **mxbai-embed-large**, **text-embedding-3-large**, **text-embedding-3-small**

---

## Decision

> **[TODO หลัง Phase 3 เสร็จ — กรอกตรงนี้]**
>
> Primary model: _______________  
> Fallback model (ถ้ามี hybrid strategy): _______________

---

## เหตุผล (Rationale)

> **[TODO]**

**Thai language benchmark:**

| Model | Recall@3 (Thai) | Recall@5 (Thai) | Latency (ms) | Cost/1M tokens |
|-------|-----------------|-----------------|--------------|----------------|
| BGE-M3 | — | — | — | $0 |
| multilingual-E5 | — | — | — | $0 |
| mxbai | — | — | — | $0 |
| OAI-3-large | — | — | — | $0.13 |
| OAI-3-small | — | — | — | $0.02 |

**Key question ที่ต้องตอบ:**
- Open-source vs Commercial quality gap สำหรับภาษาไทย: [TODO]
- Self-hosted latency ยอมรับได้ไหมสำหรับ production: [TODO]

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- [TODO]

**ข้อเสีย / Trade-offs:**
- [TODO]

**ข้อควรระวัง:**
- ถ้าเปลี่ยน embedding model ในอนาคต — ต้อง **re-index เอกสารทั้งหมด** เพราะ vector dimensions อาจต่างกัน
- ควรออกแบบ indexing pipeline ให้ re-run ได้ง่าย

---

## Migration Path

> **[TODO]** ถ้าต้องเปลี่ยน model ในอนาคต:
> - Re-index ใช้เวลาประมาณ [X] ชั่วโมง/วัน สำหรับ [Y] เอกสาร
> - Abstraction layer ใน `EmbeddingModel` interface ทำให้เปลี่ยนได้โดยแก้ config

---

## ข้อมูลที่ใช้ตัดสินใจ

- Evaluation results: `benchmarks/embedding-model/`
- Phase 3 notes: `docs/phases/phase-3-embedding.md`
- Thai evaluation criteria: `plan.md` Section 7.3
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
