# ADR-003: Embedding Model Selection

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-003 |
| **สถานะ** | 🟢 Accepted |
| **วันที่** | 2026-04-01 |
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

**Primary model: multilingual-e5-large**  
**Fallback model: mxbai-embed-large-v1** (ถ้าต้องการ latency ต่ำกว่า บน hardware จำกัด)

multilingual-e5-large เป็นตัวเลือกที่ชัดเจนที่สุด — recall สมบูรณ์แบบทั้งภาษาไทยและอังกฤษ, ไม่มีค่าใช้จ่าย, self-hostable

---

## เหตุผล (Rationale)

**Benchmark ครบ 5 models — Phase 3 (10 queries: Thai HR, English API, Thai Mixed, English Security):**

| Model | Thai Recall@3 | Eng Recall@3 | Overall | Avg Latency (ms) | Index (ms) | Cost/1M | Lock-in | **Weighted Score** |
|-------|--------------|-------------|---------|-----------------|-----------|---------|---------|-----------------|
| **multilingual-e5-large** | **1.000** | **1.000** | **1.000** | **29.9** | 1,061 | $0 | 0 | **0.9472** |
| BGE-M3 | 0.833 | 1.000 | 0.900 | 53.4 | 4,001 | $0 | 0 | 0.7349 |
| mxbai-embed-large-v1 | 0.833 | 1.000 | 0.900 | **24.5** | **761** | $0 | 0 | 0.7000 |
| OpenAI text-embedding-3-small | 1.000 | 1.000 | 1.000 | 312.2 | 819 | $0.02 | 9 | 0.6144 |
| OpenAI text-embedding-3-large | 1.000 | 1.000 | 1.000 | 301.7 | 939 | $0.13 | 9 | 0.4555 |

> Weights: Thai recall 25%, Eng recall 15%, Latency 15%, Cost 15%, Self-host 10%, Dimension 5%, Max tokens 5%, Lock-in 10%

**Key findings:**
- Open-source vs Commercial quality gap สำหรับภาษาไทย: **ไม่มี** — multilingual-e5 ทำได้ Thai recall = 1.0 เท่ากับ OpenAI
- Self-hosted latency ยอมรับได้: 29.9ms ต่อ query เหมาะสำหรับ production บน CPU (ต่ำกว่า OpenAI API ถึง 10x)
- BGE-M3 index เวลานานมาก (4,000ms) เทียบกับ mE5 (1,061ms) — ไม่คุ้มกับ recall ที่ต่ำกว่า
- OpenAI models มี latency 300ms+ เพราะเป็น API call ออกนอก — ไม่เหมาะสำหรับ target p50 < 3s

**เหตุผลที่ไม่เลือกตัวอื่น:**

| ตัวเลือก | เหตุผลที่ไม่เลือก |
|---------|-----------------|
| BGE-M3 | Thai recall 0.833 ต่ำกว่า mE5, index time ช้ามาก (4,001ms), latency สูงสุดในกลุ่ม open-source |
| mxbai-embed-large-v1 | Thai recall 0.833 ไม่ครบ 100% แม้ latency จะดีที่สุด — เลือกเป็น fallback แทน |
| OpenAI text-embedding-3-small | Vendor lock-in = 9, latency 312ms (API call), data ออกนอก org ทุกครั้ง |
| OpenAI text-embedding-3-large | เช่นเดียวกับ small + cost สูงกว่า 6.5x, weighted score ต่ำสุด (0.4555) |

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- Thai recall = 1.0 เกิน requirement (Recall@5 > 80%) อย่างมีนัยสำคัญ
- ไม่มี data ออกนอก org — เหมาะสำหรับ sensitive documents
- ต้นทุน embedding = $0 ต่อ token ตลอดอายุระบบ
- Latency 29.9ms ต่ำกว่า API-based models 10 เท่า

**ข้อเสีย / Trade-offs:**
- ต้องจัดการ model hosting เอง (RAM ~1.5GB สำหรับ e5-large)
- ไม่มี GPU → ใช้ CPU inference เท่านั้นใน PoC ปัจจุบัน
- Max tokens = 512 — เอกสารยาวต้องแบ่ง chunk และไม่สามารถ embed ทั้งหน้าในครั้งเดียว

**ข้อควรระวัง:**
- ถ้าเปลี่ยน embedding model ในอนาคต — ต้อง **re-index เอกสารทั้งหมด** เพราะ dimensions อาจต่างกัน
- ควรออกแบบ indexing pipeline ให้ re-run ได้ง่าย และ version-track model name

---

## Migration Path

ถ้าต้องเปลี่ยน model ในอนาคต:
- Abstraction layer ใน `BaseEmbeddingModel` ทำให้เปลี่ยนได้โดยแก้ config เดียว
- ต้อง re-index เอกสารทั้งหมด — เวลาขึ้นกับขนาด corpus (benchmark: 5 chunks ใช้ 1,061ms)
- ตัวเลือก upgrade ที่แนะนำ: multilingual-e5-large → BGE-M3 (ถ้าต้องการ max tokens 8192)

---

## ข้อมูลที่ใช้ตัดสินใจ

- Evaluation results: `benchmarks/embedding-model/`
- Phase 3 notes: `docs/phases/phase-3-embedding.md`
- Thai evaluation criteria: `plan.md` Section 7.3
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
