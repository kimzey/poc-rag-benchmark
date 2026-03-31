# คำศัพท์ RAG (Glossary)

คำศัพท์ที่ใช้ในโปรเจคนี้ จัดเรียงตามหมวดหมู่

---

## RAG Core Concepts

| คำศัพท์ | ความหมาย |
|--------|---------|
| **RAG** (Retrieval-Augmented Generation) | สถาปัตยกรรมที่ให้ AI ตอบคำถามโดยค้นหาเอกสารที่เกี่ยวข้องก่อน แล้วนำมาเป็น context ให้ LLM สร้างคำตอบ — ต่างจาก LLM ธรรมดาที่ตอบจากความรู้ที่ train มาเท่านั้น |
| **Knowledge Base (KB)** | คลังเอกสารที่ระบบ RAG ใช้ค้นหาข้อมูล เช่น HR policy, product FAQ, tech docs |
| **Retrieval** | ขั้นตอนค้นหาเอกสารที่เกี่ยวข้องกับคำถามของผู้ใช้ |
| **Generation** | ขั้นตอนที่ LLM สร้างคำตอบจาก context ที่ retrieve มา |
| **Context Window** | จำนวน tokens สูงสุดที่ LLM รับได้ในครั้งเดียว (prompt + response) |
| **Hallucination** | เมื่อ LLM สร้างข้อมูลที่ไม่ตรงกับ context หรือเป็นเรื่องแต่ง — RAG ช่วยลดปัญหานี้โดยให้ข้อมูลจริงเป็น context |
| **Grounding** | การทำให้คำตอบของ LLM อิงจากข้อมูลจริง (context) ไม่ใช่จากความรู้ทั่วไปของ model |

---

## Vector & Embedding

| คำศัพท์ | ความหมาย |
|--------|---------|
| **Vector** | อาร์เรย์ของตัวเลขที่แทนความหมายของข้อความ เช่น `[0.12, -0.87, 0.34, ...]` — ข้อความที่มีความหมายคล้ายกันจะมี vector ใกล้กัน |
| **Embedding** | กระบวนการแปลงข้อความเป็น vector |
| **Embedding Model** | โมเดลที่ทำ embedding เช่น BGE-M3, OpenAI text-embedding-3 |
| **Dimensions** | จำนวนมิติของ vector เช่น 768, 1024, 1536 — มากกว่า = ละเอียดกว่า แต่ใช้ storage มากกว่า |
| **Cosine Similarity** | วิธีวัดความคล้ายกันของ 2 vectors (0 = ไม่เกี่ยวกัน, 1 = เหมือนกัน) |
| **ANN** (Approximate Nearest Neighbor) | อัลกอริทึมค้นหา vectors ที่ใกล้เคียงที่สุด — ไม่ 100% แม่นยำ แต่เร็วกว่า exact search หลายเท่า |
| **Vector Database** | ฐานข้อมูลที่ออกแบบมาเพื่อเก็บ + ค้นหา vectors ได้เร็ว เช่น Qdrant, pgvector, Milvus |
| **L2-normalization** | ปรับขนาด vector ให้มี length = 1 เพื่อให้ cosine similarity ทำงานถูกต้อง |

---

## Document Processing

| คำศัพท์ | ความหมาย |
|--------|---------|
| **Chunking** | ตัดเอกสารยาวเป็นท่อนเล็กๆ (chunks) เพื่อ embed แยกกัน |
| **Chunk Size** | ขนาดของแต่ละ chunk (วัดเป็นตัวอักษรหรือ tokens) — ค่าปกติ 200-1000 |
| **Chunk Overlap** | ส่วนที่ซ้อนกันระหว่าง chunk ติดกัน — ช่วยไม่ให้ข้อมูลหายที่รอยต่อ |
| **Indexing** | กระบวนการ chunk → embed → store เอกสารลง Vector DB |
| **Re-indexing** | ทำ indexing ใหม่ทั้งหมด (จำเป็นเมื่อเปลี่ยน embedding model หรือ chunk strategy) |
| **Collection** | กลุ่มของ vectors ใน Vector DB (คล้าย table ใน SQL) |
| **Metadata** | ข้อมูลเพิ่มเติมที่แนบกับแต่ละ vector เช่น `access_level`, `source`, `category` |
| **Metadata Filter** | กรอง search results ด้วย metadata — เช่น แสดงเฉพาะ `access_level=customer_kb` |

---

## LLM & Generation

| คำศัพท์ | ความหมาย |
|--------|---------|
| **LLM** (Large Language Model) | โมเดล AI ขนาดใหญ่ที่เข้าใจและสร้างภาษาได้ เช่น GPT-4o, Claude, Llama |
| **Token** | หน่วยย่อยที่ LLM ใช้ประมวลผล — ภาษาอังกฤษ ~1 word = 1.3 tokens, ภาษาไทย ~1 คำ = 2-4 tokens |
| **Prompt** | ข้อความที่ส่งให้ LLM เพื่อสั่งให้ทำงาน — ใน RAG ประกอบด้วย system prompt + context + คำถาม |
| **System Prompt** | คำสั่งตั้งต้นที่กำหนดพฤติกรรมของ LLM เช่น "ตอบจาก context เท่านั้น ถ้าไม่รู้ให้บอกว่าไม่รู้" |
| **Completion** | คำตอบที่ LLM สร้างขึ้น |
| **Temperature** | ค่าควบคุมความ "สร้างสรรค์" ของ LLM (0 = deterministic, 1 = creative) — RAG มักใช้ 0-0.3 |
| **OpenAI-compatible API** | API format มาตรฐานที่ providers หลายเจ้ารองรับ — ช่วยให้ swap provider ได้ง่าย |
| **OpenRouter** | API gateway ที่รวม LLM หลาย providers ไว้ที่เดียว — switch model แค่เปลี่ยน string |

---

## Search & Retrieval

| คำศัพท์ | ความหมาย |
|--------|---------|
| **Semantic Search** | ค้นหาด้วย "ความหมาย" ไม่ใช่ keyword — "นโยบายลาพักร้อน" จะเจอเอกสารที่เขียนว่า "สิทธิ์วันหยุดประจำปี" |
| **Keyword Search** | ค้นหาด้วยคำตรงๆ — "ลาพักร้อน" จะเจอเฉพาะเอกสารที่มีคำนี้ |
| **Hybrid Search** | ผสม semantic + keyword search เพื่อ recall ที่ดีกว่า |
| **Top-K** | จำนวนผลลัพธ์ที่ดึงมา เช่น top-3 = 3 chunks ที่คล้ายที่สุด |
| **Recall@K** | % ของเอกสารที่ถูกต้องที่อยู่ใน top-K results — Recall@5 = 80% หมายความว่าใน 5 อันดับแรก ค้นเจอ 80% ของคำตอบที่ถูก |
| **Precision** | สัดส่วนของผลลัพธ์ที่เกี่ยวข้อง vs ทั้งหมดที่ดึงมา |
| **Score** | ค่าความคล้ายกันระหว่าง query กับ document (0-1) |

---

## Auth & Security

| คำศัพท์ | ความหมาย |
|--------|---------|
| **JWT** (JSON Web Token) | Token ที่เข้ารหัสข้อมูล user + expiry — ใช้ยืนยันตัวตนโดยไม่ต้อง query DB ทุกครั้ง |
| **RBAC** (Role-Based Access Control) | ระบบ permission ตาม role เช่น admin, employee, customer |
| **Permission** | สิ่งที่ user ได้รับอนุญาตให้ทำ เช่น `doc:read`, `doc:upload`, `chat:query` |
| **Access Level** | ระดับความลับของเอกสาร เช่น `customer_kb` (ทุกคนเห็น), `internal_kb` (พนักงาน), `confidential_kb` (admin) |
| **Permission-Filtered Retrieval** | กรองผลค้นหาที่ Vector DB ตาม access level ของ user — **ไม่ใช่กรองหลัง retrieve** แต่กรองตอน query เลย |

---

## Performance & Benchmarking

| คำศัพท์ | ความหมาย |
|--------|---------|
| **Latency** | เวลาตั้งแต่ส่ง request ถึงได้ response |
| **p50 / p95 / p99** | Percentile — p50 = median, p95 = 95% ของ requests เร็วกว่านี้, p99 = worst 1% |
| **Throughput** | จำนวน requests ที่รับได้ต่อวินาที (req/s หรือ QPS) |
| **QPS** (Queries Per Second) | = Throughput สำหรับ search/query operations |
| **Spike** | การทดลองระยะสั้นเพื่อตอบคำถามทางเทคนิค ก่อนตัดสินใจ build จริง |
| **PoC** (Proof of Concept) | ต้นแบบเพื่อพิสูจน์ว่าแนวคิดใช้งานได้จริง |

---

## Architecture & Design

| คำศัพท์ | ความหมาย |
|--------|---------|
| **ABC** (Abstract Base Class) | Class ที่กำหนด interface — adapter ต้อง implement method ทั้งหมด |
| **Adapter Pattern** | Design pattern ที่ wrap implementation ต่างกันให้มี interface เดียวกัน |
| **Anti-Vendor-Lock-in** | ออกแบบให้ไม่ผูกติดกับ vendor เดียว — swap component ได้โดยแก้ config |
| **RFC** (Request for Comments) | เอกสารเสนอ technical decision ให้ทีม review และตัดสินใจร่วมกัน |
| **ADR** (Architecture Decision Record) | บันทึกการตัดสินใจด้าน architecture + เหตุผล + alternatives ที่พิจารณา |
| **Omnichannel** | รองรับหลาย platform (Web, LINE, Discord) ผ่าน API เดียว |
