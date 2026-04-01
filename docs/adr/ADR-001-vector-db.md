# ADR-001: Vector Database Selection

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-001 |
| **สถานะ** | 🟢 Accepted |
| **วันที่** | 2026-04-01 |
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

**เลือก: Qdrant**

Qdrant ให้ balance ที่ดีที่สุดระหว่าง recall accuracy, filtering performance, และ operational simplicity จากผลทดสอบทั้ง 10K และ 100K vectors

---

## เหตุผล (Rationale)

**Benchmark summary — 10K vectors (1536 dim):**

| Metric | Qdrant | OpenSearch | pgvector | Milvus |
|--------|--------|------------|---------|--------|
| Index throughput (docs/s) | 595.2 | 185.8 | 73.3 | **907.9** |
| Query latency p50 (ms) | 10.87 | 19.72 | **7.92** | 2.37 |
| Query latency p95 (ms) | 38.27 | 36.87 | **12.37** | 10.17 |
| Filtered latency p50 (ms) | **6.28** | 19.10 | 23.32 | 1.18 |
| Filtered latency p95 (ms) | **15.00** | 25.57 | 30.92 | 1.85 |
| **Recall@10** | **0.896** | 0.793 | 0.429 | 0.277 |

**Benchmark summary — 100K vectors (scale test):**

| Metric | Qdrant | OpenSearch | pgvector | Milvus |
|--------|--------|------------|---------|--------|
| Query latency p50 (ms) | **25.71** | 52.51 | 26.71 | 19.43 |
| Query latency p95 (ms) | **100.58** | 253.79 | 77.58 | 505.26 |
| Filtered latency p50 (ms) | **26.36** | 61.31 | 256.03 | 21.45 |
| Filtered latency p95 (ms) | **46.55** | 97.41 | 1609.63 | 45.18 |

**เหตุผลหลักที่เลือก Qdrant:**
- Recall@10 = 0.896 สูงสุดในกลุ่ม — ตรงโดยตรงกับ requirement ด้านคุณภาพ retrieval
- Filtered latency p50 = 6.28ms (10K) และ 26.36ms (100K) — permission filtering เป็น core feature ของระบบเรา
- Scale behavior คาดเดาได้ — p95 เพิ่มขึ้นตามสัดส่วนสมเหตุสมผล (38ms → 100ms)
- Operational complexity ต่ำ — ไม่ต้องการ JVM, cluster mode ไม่ยุ่งยาก, Docker-first

**เหตุผลที่ไม่เลือกตัวอื่น:**

| ตัวเลือก | เหตุผลที่ไม่เลือก |
|---------|-----------------|
| pgvector | Recall@10 ต่ำมาก (0.429) และ filtered latency พัง 100K — p95 = 1,609ms ซึ่งทำให้ permission filtering ใช้ใน production ไม่ได้ |
| Milvus | Recall@10 ต่ำที่สุด (0.277) และ p99 = 2,352ms ที่ 100K scale — variance สูงเกินรับได้ แม้ p50 จะดี |
| OpenSearch | Recall และ filtering ดีพอ แต่ latency p95 = 253ms ที่ 100K scale และ operational overhead สูง (JVM, cluster config) |

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- Recall@10 = 0.896 เกิน target ที่ Recall@5 > 80%
- Filtered search รองรับ permission-based retrieval ได้ดีตั้งแต่ระดับ DB
- Scale behavior คาดเดาได้สำหรับ production planning
- Native REST + gRPC API, Python SDK ครบ

**ข้อเสีย / Trade-offs:**
- ไม่ใช่ managed service บน major cloud providers (ต่างจาก pgvector ที่มี AWS RDS)
- ต้องจัดการ infrastructure เอง หรือใช้ Qdrant Cloud (managed option)
- Recall@10 = 0.896 ยังไม่ 100% — อาจต้อง tune `hnsw_config` (ef, m) สำหรับ production

**สิ่งที่ต้องทำตามมา:**
- [ ] Setup production infrastructure (Docker self-host หรือ Qdrant Cloud)
- [ ] เขียน production VectorDBClient adapter สำหรับ Qdrant
- [ ] Tune HNSW parameters สำหรับ production dataset จริง
- [ ] วางแผน backup/snapshot strategy
- [ ] Document operational runbook + monitoring metrics

---

## Migration Path

ถ้าต้องเปลี่ยนในอนาคต:
- เนื่องจาก code ใช้ `VectorDBClient` interface — แก้เฉพาะ adapter implementation + `.env` config
- ไม่ต้องแก้ business logic หรือ RAG pipeline
- ต้อง re-index เอกสารทั้งหมดไปยัง DB ใหม่ (export vectors → import)
- ตัวเลือกสำรองที่แนะนำ: **OpenSearch** (recall 0.793, scale behavior stable กว่า Milvus)

---

## ข้อมูลที่ใช้ตัดสินใจ

- Benchmark results: `benchmarks/vector-db/results/`
- Phase 1 notes: `docs/phases/phase-1-vector-db.md`
- Comparison criteria: `plan.md` Section 5.2
