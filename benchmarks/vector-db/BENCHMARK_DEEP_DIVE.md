# Vector DB Benchmark — Deep Dive

เอกสารนี้อธิบายการทำงานของ benchmark ทีละขั้นตอน พร้อมตัวอย่างข้อมูลจริง
และวิเคราะห์ว่าสิ่งที่วัดนั้น **วัดได้จริง, mock, หรือสุ่ม**

---

## สารบัญ

1. [ภาพรวม Pipeline](#1-ภาพรวม-pipeline)
2. [ขั้นที่ 1 — สร้าง Dataset](#2-ขั้นที่-1--สร้าง-dataset)
3. [ขั้นที่ 2 — สร้าง Ground Truth](#3-ขั้นที่-2--สร้าง-ground-truth)
4. [ขั้นที่ 3 — Index + วัด Throughput](#4-ขั้นที่-3--index--วัด-throughput)
5. [ขั้นที่ 4 — ANN Search + วัด Latency](#5-ขั้นที่-4--ann-search--วัด-latency)
6. [ขั้นที่ 5 — Filtered Search](#6-ขั้นที่-5--filtered-search)
7. [ขั้นที่ 6 — คำนวณ Recall@10](#7-ขั้นที่-6--คำนวณ-recall10)
8. [ผลจริงที่รันได้](#8-ผลจริงที่รันได้)
9. [วิเคราะห์: วัดได้จริง vs Mock vs สุ่ม](#9-วิเคราะห์-วัดได้จริง-vs-mock-vs-สุ่ม)
10. [ข้อจำกัดและสิ่งที่ควรแก้](#10-ข้อจำกัดและสิ่งที่ควรแก้)

---

## 1. ภาพรวม Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    run_benchmark.py                             │
│                                                                 │
│  [1] generate_dataset(10,000)  ←── random unit vectors (fake)  │
│  [2] compute_ground_truth()    ←── brute-force numpy (exact)   │
│                                                                 │
│  สำหรับแต่ละ DB (Qdrant / pgvector / Milvus / OpenSearch):     │
│  [3] insert() → วัด index_time                                  │
│  [4] search() × 100 → วัด latency p50/p95/p99/QPS              │
│  [5] search(filter) × 50 → วัด filter latency                  │
│  [6] compute_recall() เทียบ ground_truth                        │
│  [7] drop_collection() → cleanup                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. ขั้นที่ 1 — สร้าง Dataset

**ไฟล์:** `utils/dataset.py` → `generate_dataset(n=10000)`

```python
rng = np.random.default_rng(seed=42)
raw = rng.standard_normal((10000, 1536))  # สุ่ม Gaussian
vectors = raw / np.linalg.norm(raw, axis=1, keepdims=True)  # unit normalize
```

### ตัวอย่าง Record จริงๆ ที่ได้

```python
BenchmarkRecord(
    id="0",
    vector=[-0.0231, 0.0891, -0.0145, ..., 0.0372],  # 1536 ค่า, norm=1.0
    metadata={
        "access_level": "public",       # 50% โอกาส
        "category":     "tech",         # 40% โอกาส
        "source":       "doc_000000"
    }
)

BenchmarkRecord(id="1", ..., metadata={"access_level": "internal", "category": "hr", ...})
BenchmarkRecord(id="2", ..., metadata={"access_level": "confidential", "category": "finance", ...})
# ... ×10,000
```

### การกระจาย Metadata (ออกแบบให้สมจริง)

| access_level  | สัดส่วน | จำนวน (10K) |
|--------------|---------|------------|
| public       | 50%     | ~5,000     |
| internal     | 35%     | ~3,500     |
| confidential | 15%     | ~1,500     |

| category | สัดส่วน | จำนวน (10K) |
|----------|---------|------------|
| tech     | 40%     | ~4,000     |
| hr       | 20%     | ~2,000     |
| finance  | 20%     | ~2,000     |
| ops      | 20%     | ~2,000     |

> **seed=42** → ทุกครั้งที่รันได้ชุดข้อมูลเดิม ทุก DB ได้ข้อมูลชุดเดียวกัน = fair comparison

---

## 3. ขั้นที่ 2 — สร้าง Ground Truth

**ไฟล์:** `utils/dataset.py` → `compute_ground_truth(dataset, queries, top_k=10)`

Brute-force คำนวณ cosine similarity ระหว่าง **100 query vectors** กับ **10,000 vectors** ทั้งหมด
โดยใช้ numpy dot product (เร็ว, ไม่มี approximation)

```python
corpus  = np.array([r.vector for r in dataset])  # shape: (10000, 1536)
q_mat   = np.array(queries)                       # shape: (100, 1536)
scores  = q_mat @ corpus.T                        # shape: (100, 10000)
# ← คำนวณ 100 × 10,000 = 1,000,000 similarity scores
```

### ตัวอย่าง Ground Truth ของ query[0]

```
scores[0] = [0.043, 0.891, 0.012, 0.334, ..., 0.723]
                     ^^^                        ^^^
            index=1 ใกล้สุด           index=9999 ใกล้อันดับ 2?

top-10 index = {1, 9999, 4821, 237, 512, 3344, 8801, 99, 7766, 4500}

ground_truth[0] = {"1", "9999", "4821", "237", "512", "3344", "8801", "99", "7766", "4500"}
                   ↑ set ของ ID ที่ใกล้จริงๆ — นี่คือ "คำตอบถูก"
```

> คำนวณแค่ dataset ≤50K vectors เพราะ O(N×Q) หนัก — 100K vectors จะใช้เวลา ~10 นาที

---

## 4. ขั้นที่ 3 — Index + วัด Throughput

```python
t0 = time.perf_counter()
client.insert(dataset)           # ส่ง batch vectors เข้า DB
index_time = time.perf_counter() - t0

throughput = 10_000 / index_time  # vectors/second
```

### ตัวอย่างผลจริงที่รันได้

| DB         | Index Time | Throughput |
|------------|-----------|------------|
| Qdrant     | 10.1 s    | 989 v/s    |
| pgvector   | 105.6 s   | 95 v/s     |
| Milvus     | 10.5 s    | 956 v/s    |
| OpenSearch | 43.1 s    | 232 v/s    |

**สิ่งที่วัดจริง:** เวลา wall-clock ของการ insert + build index ใน Docker บนเครื่องเดียวกัน

---

## 5. ขั้นที่ 4 — ANN Search + วัด Latency

```python
search_times = []
result_ids   = []

for q in queries[:100]:              # 100 queries ทีละอัน (sequential)
    t0    = time.perf_counter()
    hits  = client.search(q, top_k=10)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    search_times.append(elapsed_ms)
    result_ids.append([h.id for h in hits])
```

### ตัวอย่าง search times list (ms)

```
[4.1, 3.8, 12.2, 4.0, 4.2, 11.8, 3.9, 4.1, 4.3, 3.7, ...]
 ↑                ↑               ↑
 ปกติ          spike (cache miss?)   spike
```

### วิธีคำนวณ Percentile

```python
arr = np.array(search_times)

p50  = np.percentile(arr, 50)   # 4.09 ms  — ครึ่งนึงเร็วกว่านี้
p95  = np.percentile(arr, 95)   # 11.5 ms  — 95% ของ query จบภายในเวลานี้
p99  = np.percentile(arr, 99)   # 12.8 ms  — worst case เกือบๆ
QPS  = 100 / (sum(arr) / 1000)  # 192 req/s
```

### ตัวอย่างผลจริงที่รันได้

| DB         | p50 (ms) | p95 (ms) | p99 (ms) | QPS   |
|------------|---------|---------|---------|-------|
| Qdrant     | 4.1     | 11.5    | 12.8    | 192   |
| pgvector   | 7.2     | 8.5     | 12.7    | 135   |
| Milvus     | 2.3     | 4.8     | 7.5     | 378   |
| OpenSearch | 18.9    | 22.1    | 26.0    | 51    |

**สิ่งที่วัดจริง:** latency รวม network round-trip ไป Docker + DB processing + กลับมา

---

## 6. ขั้นที่ 5 — Filtered Search

เหมือนขั้นที่ 4 แต่เพิ่ม metadata filter

```python
client.search(q, top_k=10, filter={"access_level": "internal"})
# DB ค้นเฉพาะ vector ที่มี access_level="internal" (~3,500 จาก 10,000)
```

### ตัวอย่างผลจริง

| DB         | Filter p95 (ms) | vs ANN p95 | ผลต่าง |
|------------|----------------|-----------|--------|
| Qdrant     | 4.9 ms         | 11.5 ms   | **เร็วขึ้น** (Qdrant optimize filter ได้ดี) |
| pgvector   | 21.3 ms        | 8.5 ms    | ช้าลง 2.5× |
| Milvus     | 2.6 ms         | 4.8 ms    | เร็วขึ้น |
| OpenSearch | 23.4 ms        | 22.1 ms   | ใกล้เคียงเดิม |

---

## 7. ขั้นที่ 6 — คำนวณ Recall@10

```python
def compute_recall(results, ground_truth):
    hits  = sum(len(set(r) & gt) for r, gt in zip(results, ground_truth))
    total = sum(len(gt) for gt in ground_truth)
    return hits / total
```

### ตัวอย่างการคำนวณ query เดียว

```
ground_truth[0] = {"1","9999","4821","237","512","3344","8801","99","7766","4500"}
                   ↑ 10 IDs จริงๆ ที่ใกล้ที่สุด (จาก brute-force)

DB ตอบมา       = {"1","9999","4821","237","512","3344","8801","99","7766","XXXX"}
                                                                           ^^^^
                                                                     พลาด! ได้ XXXX แทน 4500

hits ของ query นี้ = |intersection| = 9
```

```
ทำแบบนี้กับ 100 queries:
total_hits    = 888   (query 1: 9, query 2: 10, query 3: 8, ...)
total_possible = 1000  (100 queries × 10 ต่อ query)

Recall@10 = 888/1000 = 0.888
```

### ตัวอย่างผลจริง

| DB         | Recall@10 | ความหมาย |
|------------|-----------|---------|
| Qdrant     | 88.8%     | ใน 10 ผล → 8.88 ถูก |
| pgvector   | 41.4%     | ใน 10 ผล → 4.14 ถูก (น้อยมาก) |
| Milvus     | 27.7%     | ใน 10 ผล → 2.77 ถูก (แย่ที่สุด) |
| OpenSearch | 88.1%     | ใน 10 ผล → 8.81 ถูก |

---

## 8. ผลจริงที่รันได้

ผลนี้มาจาก run จริงบนเครื่อง local (Docker, 10,000 vectors, 1536 dims)

```
DB         Vectors  Index(s)  v/s    p50    p95    p99    QPS   Filter p95  Recall@10
─────────────────────────────────────────────────────────────────────────────────────
Qdrant     10,000   10.1 s    989    4.1ms  11.5ms 12.8ms  192  4.9ms       88.8%
pgvector   10,000   105.6 s   95     7.2ms  8.5ms  12.7ms  135  21.3ms      41.4%  ⚠
Milvus     10,000   10.5 s    956    2.3ms  4.8ms  7.5ms   378  2.6ms       27.7%  ⚠
OpenSearch 10,000   43.1 s    232    18.9ms 22.1ms 26.0ms   51  23.4ms      88.1%
```

> ค่า Recall@10 ต่ำของ pgvector และ Milvus อธิบายในหัวข้อถัดไป

---

## 9. วิเคราะห์: วัดได้จริง vs Mock vs สุ่ม

### สรุปแบบตาราง

| Metric            | สถานะ       | เหตุผล |
|-------------------|-------------|--------|
| Index time        | ✅ วัดจริง   | `time.perf_counter()` จับเวลาจริง ครอบคลุม network + DB |
| Search p50/p95/p99| ✅ วัดจริง   | วัด round-trip latency จริงๆ 100 ครั้ง |
| Filter p95        | ✅ วัดจริง   | วัดจริง แต่ filter condition เดียว ("internal") |
| QPS               | ⚠️ ประมาณ  | Sequential query ไม่ใช่ concurrent → ตัวเลขสูงเกินจริง |
| Recall@10         | ⚠️ บิดเบือน | วัดถูกวิธี แต่ input data สุ่ม → ตัวเลขไม่ตรงกับ production |

---

### ปัญหาหลัก: Vector ปลอม (Random)

นี่คือข้อจำกัดที่สำคัญที่สุด

**Vector จริง (text embedding) มีลักษณะนี้:**
```
ข้อความ "นโยบาย HR" → [0.001, 0.003, 0.892, -0.002, ...]
ข้อความ "วันลาพักร้อน" → [0.002, 0.001, 0.871, -0.003, ...]
                                          ^^^^^^^^^^^
                         สองข้อความนี้ใกล้กัน → มี "cluster"
```

**Random vector ที่ใช้ตอนนี้:**
```
vector[0] = [-0.023,  0.891, -0.445,  0.112, ...]  ← สุ่มทุกทิศ
vector[1] = [ 0.334, -0.221,  0.091, -0.781, ...]  ← ไม่มี pattern
```

ใน 1536 มิติ random vectors เกือบทั้งหมด **orthogonal ต่อกัน** (angle ≈ 90°)
ไม่มี cluster → ANN index (HNSW/IVF) ทำงานผิดจากสภาพที่ออกแบบมา

**ผลที่เกิด:**

| DB         | Recall@10 (random) | คาดการณ์ด้วย real text |
|------------|-------------------|----------------------|
| Qdrant     | 88.8%             | ~95-99%              |
| pgvector   | 41.4% ← ต่ำมาก    | ~85-95%              |
| Milvus     | 27.7% ← ต่ำมาก    | ~90-98%              |
| OpenSearch | 88.1%             | ~90-95%              |

pgvector และ Milvus ได้ recall ต่ำมาก **ไม่ใช่เพราะ DB แย่** แต่เพราะ:
- index parameter default ไม่ได้ tune สำหรับ random data
- HNSW/IVF ออกแบบมาสำหรับ clustered embedding space

---

### QPS: Sequential ≠ Concurrent

```python
# วิธีปัจจุบัน (sequential)
for q in queries:
    result = client.search(q)   # รอเสร็จก่อนค่อยส่งอันต่อไป

# QPS = 192 req/s (Qdrant)
```

Production จริง: users ส่ง request พร้อมกัน 10–100 connections

```
Sequential QPS ≠ Concurrent throughput
Sequential QPS สูงเกินจริงเมื่อ load สูง
```

---

### Ground Truth: วิธีนี้ถูกต้อง

`compute_ground_truth` ใช้ numpy brute-force → คำตอบ exact 100%

```python
scores = q_mat @ corpus.T  # dot product = cosine sim (unit vectors)
```

วิธีนี้ถูกต้องสมบูรณ์ ปัญหาคือ **input vectors** ไม่สมจริง ไม่ใช่วิธีคำนวณ

---

### No Warm-up

Query แรกๆ มักช้าเพราะ OS page cache ยังไม่อุ่น

```
times = [4.1, 12.2, 4.0, 4.2, 4.1, ...]
              ^^^
         query ที่ 2 ช้าเป็นพิเศษ
```

p99 อาจสูงเพราะ outlier ช่วงแรก ไม่ใช่ steady-state จริง

---

## 10. ข้อจำกัดและสิ่งที่ควรแก้

### ระดับ "ต้องแก้" (กระทบ correctness)

| ข้อจำกัด | วิธีแก้ |
|---------|---------|
| Vector ปลอม → Recall บิดเบือน | Embed ข้อความจริงจาก `datasets/` ด้วย `openai/text-embedding-3-small` |
| Milvus/pgvector recall ต่ำผิดปกติ | ต้อง tune index params: HNSW ef_construction, pgvector lists |

### ระดับ "ควรแก้" (กระทบ reliability ของตัวเลข)

| ข้อจำกัด | วิธีแก้ |
|---------|---------|
| ไม่ warm-up | รัน 10 queries ทิ้งก่อนวัด |
| Sequential QPS | เพิ่ม concurrent load test แยกต่างหาก |
| Filtered recall ไม่วัด | คำนวณ recall สำหรับ filtered query ด้วย |

### ระดับ "รับได้สำหรับ spike" (ไม่ใช่ production benchmark)

| ข้อจำกัด | เหตุผลที่รับได้ |
|---------|---------------|
| 10,000 vectors (เล็ก) | spike/PoC เพื่อเปรียบเทียบ relative behavior |
| Filter condition เดียว | เพียงพอสำหรับเห็น pattern |
| ไม่วัด memory usage | ไม่ใช่ constraint หลักของ spike |

---

## สรุป: ควรเชื่อผลแค่ไหน?

```
✅ เชื่อได้ (Relative comparison)
   Qdrant index เร็วกว่า pgvector ~10x  → จริง
   Milvus search เร็วที่สุด             → น่าเชื่อ
   OpenSearch QPS ต่ำสุด               → น่าเชื่อ

⚠️ เชื่อไม่ได้เต็มๆ (Absolute numbers)
   pgvector Recall@10 = 41.4%           → ต่ำเกินจริงเพราะ random vectors
   Milvus Recall@10 = 27.7%             → ต่ำเกินจริงเพราะ random vectors
   QPS ตัวเลขสูง                        → วัด sequential ไม่ใช่ concurrent

❌ ไม่ควรเอาไปใช้วาง production capacity plan โดยตรง
```
