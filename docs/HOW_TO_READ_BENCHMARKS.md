# คู่มืออ่านผล Benchmark — RAG Tech Stack Spike

> เอกสารนี้อธิบายว่าแต่ละ metric ใน benchmark คืออะไร อ่านยังไง และตัวเลขแบบไหนถือว่า "ดี"

---

## สารบัญ

1. [Phase 1 — Vector DB Metrics](#phase-1--vector-db-metrics)
2. [Phase 2 — RAG Framework Metrics](#phase-2--rag-framework-metrics)
3. [Phase 3 — Embedding Model Metrics](#phase-3--embedding-model-metrics)
4. [Phase 3.5 — LLM Provider Metrics](#phase-35--llm-provider-metrics)
5. [Weighted Score — อ่านยังไง](#weighted-score--อ่านยังไง)
6. [สรุปภาพรวม: อ่านตารางเปรียบเทียบ](#สรุปภาพรวม-อ่านตารางเปรียบเทียบ)

---

## Phase 1 — Vector DB Metrics

### 1.1 Index Throughput (docs/sec)

**คืออะไร:** ความเร็วในการ insert vectors เข้า DB — วัดว่า 1 วินาที DB รับ vector ได้กี่ตัว

**อ่านยังไง:**
```
Milvus:     907.9 docs/sec  ← เร็วมาก
Qdrant:     595.2 docs/sec  ← เร็วดี
OpenSearch: 185.8 docs/sec  ← ช้าพอรับได้
pgvector:    73.3 docs/sec  ← ช้า
```

**สำคัญแค่ไหน:** สำคัญมากถ้า corpus ใหญ่มากหรือต้อง re-index บ่อย แต่ถ้า index ครั้งเดียวแล้วใช้ไปเรื่อยๆ (typical RAG) ตัวเลขนี้สำคัญน้อยกว่า search latency

---

### 1.2 Latency Percentiles — p50, p95, p99, mean

นี่คือ metric ที่สำคัญที่สุดในการประเมิน DB ต้องเข้าใจให้ดี

**Percentile คืออะไร:**

สมมติรัน query 100 ครั้ง เรียงผลลัพธ์จากเร็วสุดไปช้าสุด:
```
query ที่ 1 (เร็วสุด):  2ms
query ที่ 2:            3ms
...
query ที่ 50 (p50):    10ms  ← "ปกติ" ผู้ใช้ครึ่งหนึ่งเจอน้อยกว่านี้
...
query ที่ 95 (p95):    38ms  ← ผู้ใช้ 95% เจอเร็วกว่านี้
...
query ที่ 99 (p99):    53ms  ← "worst case" ที่น่าเป็นห่วง
query ที่ 100 (ช้าสุด): 80ms
```

**แต่ละตัวบอกอะไร:**

| Metric | อ่านว่า | บอกอะไร | ใช้ดูอะไร |
|--------|---------|---------|---------|
| **p50** | "มัธยฐาน" | ผู้ใช้ปกติเจออะไร | ประสบการณ์ "ทั่วไป" |
| **p95** | "95th percentile" | ผู้ใช้ส่วนใหญ่เจออะไร | ประสบการณ์ "แย่ที่สุดที่พบบ่อย" |
| **p99** | "99th percentile" | outlier / worst case | ระบบ stable ไหม |
| **mean** | "ค่าเฉลี่ย" | average ทั้งหมด | บิดเบือนได้จาก outlier |

**ทำไม p50 สำคัญกว่า mean:**

```
สมมติมี 10 queries: 5, 5, 5, 5, 5, 5, 5, 5, 5, 500 ms

mean = (5×9 + 500) / 10 = 54.5ms  ← ดูสูงเกินจริง
p50  = 5ms                          ← สะท้อนความเป็นจริงดีกว่า
p99  = 500ms                        ← บอกว่ามี spike
```

**ตัวอย่างจากผล benchmark:**

```
Qdrant (10K vectors):
  p50 = 10.87ms  "query ปกติใช้เวลาแค่นี้"
  p95 = 38.27ms  "query ที่ช้ากว่าปกติ 1 ใน 20 ใช้เวลาเท่านี้"
  p99 = 53.16ms  "query ที่ช้าสุดๆ 1 ใน 100 ใช้เวลาเท่านี้"

pgvector (10K vectors):
  p50 =  7.92ms  ← ดูดีกว่า Qdrant ที่ p50!
  p95 = 12.37ms  ← ดูดีกว่า Qdrant ที่ p95!
  ...แต่...
  Recall@10 = 0.429  ← หาของผิด 57% ของเวลา
```

> **บทเรียน:** latency ต่ำแต่ recall แย่ = เร็วแต่ตอบผิด — ไม่มีประโยชน์

---

### 1.3 Filtered Latency

**คืออะไร:** latency เดียวกับด้านบน แต่เพิ่มเงื่อนไข filter เข้าไปด้วย

**ตัวอย่าง filter ในระบบเรา:**
```python
# ไม่ filter: ค้นหาใน vectors ทั้งหมด
results = db.search(query_vector, top_k=3)

# มี filter: ค้นหาเฉพาะ docs ที่ user มีสิทธิ์เข้าถึง
results = db.search(
    query_vector,
    top_k=3,
    filter={"access_level": {"$in": ["public", "internal"]}}
)
```

**ทำไมต้องวัดแยก:** บาง DB handle filter แบบ pre-filter (กรองก่อนค้นหา → เร็ว) บางตัวทำ post-filter (ค้นหาก่อน กรองทีหลัง → ช้า ยิ่งถ้า filter เข้มงวด)

**ผลที่น่าตกใจ:**
```
pgvector (100K vectors):
  ไม่ filter:   p50 =  26.71ms  ← พอรับได้
  มี filter:    p50 = 256.03ms  ← ช้าขึ้น 9.6 เท่า!
                p95 = 1,609ms   ← 1.6 วินาทีแค่ retrieval
```

**ทำไม pgvector แย่:** ทำ sequential scan ผ่าน WHERE clause แทนที่จะ integrate filter เข้ากับ ANN index

---

### 1.4 QPS (Queries Per Second)

**คืออะไร:** จำนวน query ที่ระบบตอบได้ต่อวินาที — inverse ของ mean latency

```
QPS = 1000 / mean_latency_ms

Qdrant:  QPS = 1000 / 14.56 = 68.7 queries/sec
Milvus:  QPS = 1000 /  3.72 = 268.9 queries/sec
```

**บอกอะไร:** throughput capacity ของระบบ — ถ้าต้องการรองรับ concurrent users จำนวนมากต้องดู metric นี้

**requirement ของเรา:** > 50 req/sec — Qdrant (68.7 QPS) ผ่านเพียงพอ

---

### 1.5 Recall@K

**คืออะไร:** สัดส่วนของ "คำตอบที่ถูกต้อง" ที่ DB หาเจอ ใน top-K results

**อธิบายด้วยตัวอย่าง:**

สมมติเราถามว่า "นโยบาย WFH" และรู้ว่า chunk ที่ถูกต้องคือ chunk #3

```
ค้นหา top-10:
  Qdrant คืนมา: [chunk#3, chunk#7, chunk#1, ...]  ← พบ chunk#3 ใน top-10 ✓
  Milvus คืนมา: [chunk#7, chunk#2, chunk#9, ...]  ← ไม่พบ chunk#3 ใน top-10 ✗
```

ทำซ้ำ 100 ครั้ง นับว่ากี่ครั้งที่หาเจอ:

```
Recall@10 = จำนวนครั้งที่หาเจอ / 100

Qdrant:    89.6/100 = 0.896
pgvector:  42.9/100 = 0.429
Milvus:    27.7/100 = 0.277
OpenSearch: 79.3/100 = 0.793
```

**ทำไม Recall สำคัญมาก:** ถ้า retrieval หาข้อมูลไม่เจอ LLM จะไม่มีข้อมูลที่ถูกต้องมาตอบ → คำตอบผิดหรือ hallucinate

**เป้าหมาย requirement:** Recall@5 > 0.80 — Qdrant (0.896) ผ่านสบาย, Milvus (0.277) ไม่ผ่านเลย

---

## Phase 2 — RAG Framework Metrics

### 2.1 Number of Chunks

**คืออะไร:** จำนวน text chunks ที่ framework สร้างจาก corpus เดียวกัน (3 เอกสาร)

```
bare_metal:  5 chunks   ← chunk ใหญ่ๆ (ตรงกับ config size=500)
llamaindex: 17 chunks   ← แบ่งละเอียดกว่า (overlapping strategy ต่างกัน)
langchain:  33 chunks   ← แบ่งละเอียดมาก (splitter logic ต่าง)
haystack:    5 chunks   ← เหมือน bare_metal
```

**ส่งผลต่ออะไร:**
- Chunks มาก → precision ดีกว่า (แต่ละ chunk เน้นเรื่องเดียว) แต่ noise มากขึ้น
- Chunks น้อย → context ครบกว่า แต่ precision ต่ำกว่า

> ตัวเลขนี้ไม่มี "ถูก/ผิด" — ขึ้นกับ chunking strategy และ use case

---

### 2.2 Indexing Time (ms)

**คืออะไร:** เวลาที่ใช้ตั้งแต่อ่านเอกสารจนถึง index พร้อมค้นหา (รวม embed + insert)

```
haystack:   863ms   ← เร็วสุด
bare_metal: 964ms
llamaindex: 1,596ms
langchain:  1,691ms ← ช้าสุด (chunks มากที่สุดด้วย)
```

**สำคัญไหม:** สำหรับ production ตัวนี้สำคัญน้อยกว่า query latency เพราะ index ทำครั้งเดียว แต่ถ้าต้อง re-index บ่อย (เพิ่ม/แก้เอกสาร) ก็ต้องดู

---

### 2.3 Lines of Code (LOC)

**คืออะไร:** จำนวนบรรทัด code ที่ต้องเขียนเพื่อ implement RAG pipeline พื้นฐาน

```
llamaindex:  84 LOC  ← น้อยสุด
langchain:   97 LOC
bare_metal: 103 LOC
haystack:   142 LOC  ← มากสุด
```

**บอกอะไร:** proxy ของ complexity และ maintenance burden — code น้อย = อ่านง่าย, แก้ง่าย, test ง่าย

**ข้อควรระวัง:** LOC น้อยไม่ได้แปลว่าดีเสมอไป ถ้า abstraction ซ่อนของมากเกินไปจะ debug ยาก

---

## Phase 3 — Embedding Model Metrics

### 3.1 Recall@K (Thai / English)

ใช้หลักการเดียวกับ Recall@10 ใน Phase 1 แต่:
- วัดที่ K=3 (top-3 chunks)
- แยกวัดตามภาษาของ query

```
multilingual_e5:
  Thai recall@3 = 1.000  ← หาถูกทุกข้อที่ถามเป็นภาษาไทย
  Eng  recall@3 = 1.000  ← หาถูกทุกข้อที่ถามเป็นภาษาอังกฤษ

bge_m3:
  Thai recall@3 = 0.833  ← หาถูก 5/6 คำถามไทย (พลาด 1)
  Eng  recall@3 = 1.000  ← หาถูกทุกข้อภาษาอังกฤษ
```

**ทำไม Thai recall สำคัญพิเศษ:** ภาษาไทยเป็น first-class requirement — model ที่ train บน English-heavy data มักมีปัญหากับภาษาไทย

---

### 3.2 MRR — Mean Reciprocal Rank

**คืออะไร:** วัดว่า "คำตอบที่ถูกต้อง" อยู่ที่ตำแหน่งไหนใน results (ไม่ใช่แค่ว่าอยู่ใน top-K หรือเปล่า)

**สูตร:** `MRR = (1/n) × Σ (1 / rank_i)`

**ตัวอย่าง:**

```
query 1: chunk ที่ถูกต้องอยู่อันดับ 1  → reciprocal rank = 1/1 = 1.000
query 2: chunk ที่ถูกต้องอยู่อันดับ 2  → reciprocal rank = 1/2 = 0.500
query 3: chunk ที่ถูกต้องอยู่อันดับ 3  → reciprocal rank = 1/3 = 0.333
query 4: ไม่พบใน top-K               → reciprocal rank = 0

MRR = (1.000 + 0.500 + 0.333 + 0) / 4 = 0.458
```

**อ่านค่า MRR:**

| MRR | ความหมาย |
|-----|---------|
| 1.0 | ตำแหน่ง 1 ทุกครั้ง — สมบูรณ์แบบ |
| 0.7–0.9 | ส่วนใหญ่อยู่ top-2 |
| 0.5–0.7 | มักอยู่ top-3 |
| < 0.5 | หาเจอบ้าง แต่มักไม่ได้อันดับต้น |

**ผลลัพธ์:**
```
multilingual_e5: MRR = 0.767  ← ส่วนใหญ่อยู่ top-2
bge_m3:          MRR = 0.700
mxbai:           MRR = 0.683
```

**ความต่างระหว่าง Recall กับ MRR:**
- Recall บอกว่า "พบหรือไม่พบ" (binary)
- MRR บอกว่า "พบที่อันดับไหน" (positional) — สำคัญกว่าเพราะ RAG ใช้แค่ top-K และ LLM ให้ความสำคัญกับ context อันดับต้น

---

### 3.3 Avg Query Latency (ms)

**คืออะไร:** เวลาเฉลี่ยที่ใช้ embed query 1 ครั้ง (แปลง text → vector)

```
mxbai:            24.5ms   ← เร็วสุด (self-hosted)
multilingual_e5:  29.9ms   ← เร็วมาก
bge_m3:           53.4ms   ← ช้าพอรับได้
OpenAI small:    312.2ms   ← ช้ามาก (network round-trip ไป API)
OpenAI large:    301.7ms   ← ช้าเช่นกัน
```

**ทำไม OpenAI ช้ากว่า local มาก:** ต้องส่ง request ออก internet → process → รับ response กลับ แม้ OpenAI จะมี infrastructure ดีแค่ไหนก็ยังช้ากว่า local inference

**ผลต่อ E2E latency:** ถ้า target p50 < 3 วินาที และ LLM ใช้ ~1 วินาที เหลือ 2 วินาทีสำหรับ retrieval ทั้งหมด (embed + vector search) — 312ms ต่อ embed เริ่มกินเวลามากเกินไป

---

## Phase 3.5 — LLM Provider Metrics

### 4.1 F1 Score (Overall / Thai)

**คืออะไร:** วัดคุณภาพคำตอบโดยเปรียบเทียบ token ระหว่าง "คำตอบที่ generate ได้" กับ "คำตอบที่คาดหวัง"

**F1 = harmonic mean ของ Precision และ Recall:**
```
Precision = ส่วนที่ model ตอบมาแล้วถูก / ทั้งหมดที่ตอบ
Recall    = ส่วนที่ model ตอบมาแล้วถูก / ทั้งหมดที่ควรตอบ
F1        = 2 × (Precision × Recall) / (Precision + Recall)
```

**ตัวอย่างจาก benchmark:**
```
คำถาม:   "OT วันหยุดได้รับค่าตอบแทนกี่เท่า?"
Expected: "OT วันหยุดได้รับ 3 เท่า พนักงาน Senior Grade 4+ ได้วันหยุดชดเชย"
Generated: "OT วันหยุดได้รับค่า OT 3 เท่าของอัตราค่าจ้างรายชั่วโมง สำหรับพนักงาน Senior (Grade 4+)"

F1 = 0.571  ← บางส่วนถูก บางส่วนพูดเกิน บางส่วนขาด
```

**อ่านค่า F1:**

| F1 | ความหมาย |
|----|---------|
| > 0.8 | ตอบได้ดีมาก — ใกล้เคียง expected |
| 0.5–0.8 | ตอบได้พอใช้ — ถูกบางส่วน |
| 0.3–0.5 | ตอบได้บางส่วน — มี noise |
| < 0.3 | ตอบผิดหรือ off-topic |

**ข้อจำกัดของ F1:** วัด token overlap เท่านั้น ไม่ได้วัด "ความหมาย" — คำตอบที่ถูกต้องแต่ใช้คำต่างออกไปจะได้ F1 ต่ำกว่าความเป็นจริง ควรใช้ร่วมกับ human evaluation

**ทำไม F1 ในผลลัพธ์ค่อนข้างต่ำ (0.43–0.47):**
- เป็นเพราะ expected answer เขียนสั้น model ตอบยาวกว่า → precision ต่ำ
- ไม่ได้แปลว่าคำตอบ "ผิด" — แต่ token overlap ต่ำ

---

### 4.2 Avg Latency (ms) — LLM

**คืออะไร:** เวลาเฉลี่ยตั้งแต่ส่ง prompt ถึงได้ response ครบ (Time to Last Token)

```
gemini-2.0-flash:    1,066ms  ← เร็วสุด
gpt-4o (direct):     1,192ms
gpt-4o (OpenRouter): 1,503ms
llama-3.1-70b:       2,195ms
gpt-4o-mini (OR):    2,377ms
deepseek-r1:         2,993ms  ← ช้าสุด
```

**ทำไม gpt-4o-mini ผ่าน OpenRouter ช้ากว่า direct (2,377ms vs 1,440ms):**

```
Direct:    App → OpenAI API → Response
             └── 1 hop

OpenRouter: App → OpenRouter → OpenAI API → Response → OpenRouter → App
               └── 3 hops ── routing + overhead ~937ms
```

> OpenRouter overhead ที่ gpt-4o-mini = 937ms ซึ่งมากพอดู แต่ gemini-flash ผ่าน OpenRouter ใช้ 1,066ms ซึ่งไม่มี direct reference ให้เปรียบ

---

### 4.3 Total Cost (USD) ต่อ 10 queries

**คืออะไร:** ค่าใช้จ่ายจริงที่เกิดขึ้นในการรัน 10 queries (input tokens + output tokens × rate)

```
gemini-2.0-flash:  $0.003146  ← ถูกสุด (~$0.000315/query)
gpt-4o-mini (OR):  $0.004890  ← ถูกพอรับได้ (~$0.000489/query)
llama-3.1-70b:     $0.011860  ← แพงกว่า gemini 3.8x
gpt-4o (OR):       $0.080885  ← แพงมาก (~$0.00809/query) = 26x ของ gemini
```

**คำนวณ cost ที่ scale จริง:**
```
1,000 queries/วัน × $0.000315 = $0.315/วัน = ~$9.45/เดือน  (gemini-flash)
1,000 queries/วัน × $0.00809  = $8.09/วัน  = ~$242/เดือน   (gpt-4o)
```

---

### 4.4 Vendor Lock-in Score

**คืออะไร:** คะแนน 0–10 ที่วัดว่า "ผูกพัน" กับ provider นี้มากแค่ไหน

| Score | ความหมาย | ตัวอย่าง |
|-------|---------|---------|
| 0 | ไม่ผูกพันเลย | model open-source, self-hostable |
| 1–3 | ผูกพันน้อย | OpenRouter (เปลี่ยน model ด้วย string) |
| 4–6 | ผูกพันปานกลาง | OpenRouter + proprietary model |
| 7–9 | ผูกพันสูง | Direct API (ต้องแก้ integration code) |
| 10 | ผูกพันสูงมาก | Proprietary format + data migration ยาก |

**ผลลัพธ์:**
```
llama-3.1-70b (via OpenRouter): lock-in = 0  ← open-source, self-host ได้
gemini-flash  (via OpenRouter): lock-in = 2  ← ผ่าน OpenRouter เปลี่ยนง่าย
gpt-4o-mini   (via OpenRouter): lock-in = 3
gpt-4o-mini   (OpenAI Direct):  lock-in = 9  ← เปลี่ยนต้องแก้ integration ทั้งหมด
```

> **ทำไม lock-in ต่างกันระหว่าง OpenRouter vs Direct แม้ใช้ model เดียวกัน:**
> OpenRouter ใช้ OpenAI-compatible API → เปลี่ยน model ด้วย string เดียว
> Direct API → ถ้าเปลี่ยนเป็น Anthropic หรือ Google ต้องแก้ SDK และ API format

---

## Weighted Score — อ่านยังไง

### คืออะไร

Weighted Score คือการรวม metrics หลายตัวเป็นตัวเลขเดียว โดยให้ "น้ำหนัก" กับแต่ละ metric ตามความสำคัญต่อ use case ของเรา

### Phase 3 — Embedding Model Weights

```
thai_recall:   25%  ← สำคัญสุด (first-class requirement)
eng_recall:    15%
latency:       15%
cost:          15%
self_host:     10%  ← สำคัญมาก (data privacy)
lock_in:       10%
dimension:      5%  ← storage cost
max_tokens:     5%
```

### Phase 3.5 — LLM Provider Weights

```
overall_quality: 20%  ← คุณภาพคำตอบ
lock_in:         20%  ← ให้น้ำหนักเท่ากับคุณภาพ! (anti-lock-in policy)
cost:            15%
latency:         15%
thai_quality:    10%
reliability:     10%
privacy:          5%
ease_switching:   5%
```

### วิธีอ่าน Weighted Score

```
Score = 0.9472  ← ดีมาก (~95% ของ max)
Score = 0.70    ← ดีพอใช้ (~70% ของ max)
Score = 0.45    ← ต่ำ (~45% ของ max)
```

**ข้อควรระวัง:** Weighted Score ขึ้นกับ weights ที่กำหนด — ถ้า project อื่นมี priority ต่างกัน (เช่น ไม่สนใจ self-host) ลำดับอาจเปลี่ยน

### ตัวอย่าง: ทำไม OpenAI large ได้ score ต่ำแม้ recall สูง

```
OpenAI text-embedding-3-large:
  thai_recall (25%): 1.0  × 0.25 = 0.250  ✓
  eng_recall  (15%): 1.0  × 0.15 = 0.150  ✓
  latency     (15%): แย่  × 0.15 = ~0.025 ✗ (301ms vs 29ms)
  cost        (15%): $0.13× 0.15 = ~0.010 ✗ (แพงสุด)
  self_host   (10%): 0    × 0.10 = 0.000  ✗ (host ไม่ได้)
  lock_in     (10%): 9/10 × 0.10 = ~0.010 ✗ (lock-in สูง)

Weighted score ≈ 0.455  ← แม้ recall ดีแต่ penalty อื่นดึงลง
```

---

## สรุปภาพรวม: อ่านตารางเปรียบเทียบ

### Framework สำหรับการตัดสินใจ

เมื่อดูตารางเปรียบเทียบ ให้ถามตัวเองตามลำดับนี้:

```
1. มี disqualifier ไหม?
   → Recall ต่ำกว่า threshold? (e.g., Milvus recall=0.277)
   → Latency เกิน budget? (e.g., pgvector filtered=1,609ms)
   ถ้ามี → ตัดออกก่อนเลย ไม่ต้องดูต่อ

2. ดู p95 ไม่ใช่แค่ p50
   → p50 ดีแต่ p95 แย่ = ระบบ unstable (e.g., Milvus 100K: p95=505ms)
   → p95 สม่ำเสมอ = predictable (e.g., Qdrant: p50=10ms, p95=38ms)

3. ดู Recall ก่อน Latency เสมอ
   → เร็วแต่หาของผิด ไม่มีประโยชน์
   → ช้ากว่าหน่อยแต่หาถูก ยังแก้ได้ด้วย caching/optimization

4. ดู scale behavior
   → ตัวเลขที่ 10K ไม่การันตี 100K
   → ระวัง p99 spike ที่ scale ใหญ่ขึ้น

5. ดู Weighted Score เป็น tiebreaker
   → ถ้า 2 ตัวสูสีกัน ดู weighted score ที่รวม dimension อื่นด้วย
```

### Red Flags ที่ต้องระวัง

| สัญญาณ | ความหมาย | ตัวอย่าง |
|--------|---------|---------|
| p99 > 10× p50 | มี spike รุนแรง | Milvus 100K: p50=19ms, p99=2,352ms |
| Filtered >> Unfiltered | DB ไม่ support filter ดี | pgvector 100K: unfiltered=26ms, filtered=256ms |
| Recall < 0.5 | หาข้อมูลผิดเกินครึ่ง | Milvus: 0.277, pgvector: 0.429 |
| Lock-in = 9 + ราคาแพง | ทั้งแพงทั้งเปลี่ยนยาก | OpenAI Direct gpt-4o |

---

## Quick Reference

| Metric | ยิ่งสูง/ต่ำยิ่งดี | range ทั่วไป | เกณฑ์ของเรา |
|--------|----------------|------------|-----------|
| Recall@K | สูง ↑ | 0–1.0 | > 0.80 |
| MRR | สูง ↑ | 0–1.0 | > 0.60 |
| F1 score | สูง ↑ | 0–1.0 | > 0.40 |
| Weighted score | สูง ↑ | 0–1.0 | > 0.70 |
| Query latency p50 | ต่ำ ↓ | 1–500ms | < 200ms |
| Query latency p95 | ต่ำ ↓ | 5–2000ms | < 500ms |
| Cost/query | ต่ำ ↓ | $0–$0.01 | < $0.001 |
| Lock-in score | ต่ำ ↓ | 0–10 | < 4 |
| LOC | ต่ำ ↓ | 50–500 | — |
