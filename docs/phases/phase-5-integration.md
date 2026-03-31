# Phase 5: Integration Testing

## คืออะไร?

Phase 5 เป็นการทดสอบว่า **components ทั้งหมดทำงานร่วมกันได้จริง** ในรูปแบบ end-to-end — ไม่ใช่แค่ทดสอบแยกทีละส่วน

มี 2 ส่วนหลัก:
1. **Integration Tests** — pytest scenarios ทดสอบ 7 สถานการณ์จริง
2. **Load Tests** — Locust ทดสอบว่าระบบรับ concurrent users ได้ไหม

---

## ทำไมต้อง Integration Test?

Unit tests ทดสอบแต่ละส่วน แต่ integration test ทดสอบว่า:
- Auth flow → Vector DB → LLM ทำงานต่อกันได้จริงหรือไม่
- Permission filter ทำงานถูกต้องใน end-to-end flow หรือไม่
- Component swap ทำงานได้จริงหรือเป็นแค่ทฤษฎี
- ระบบรับ load ได้ตาม performance targets ที่กำหนด

---

## 7 Test Scenarios

| # | Scenario | สิ่งที่ทดสอบ |
|---|---------|-----------|
| 1 | Employee upload & query | Upload doc → index → query → ได้คำตอบจาก doc นั้น |
| 2 | Customer permission filter | Customer ค้นหา → ได้เฉพาะ customer docs, ไม่เห็น internal |
| 3 | LINE webhook E2E | LINE message → adapter → RAG pipeline → reply |
| 4 | Concurrent queries | 30 concurrent requests ไม่มี errors |
| 5 | Component swap | Swap retrieval strategy → ผลลัพธ์ยังถูกต้อง |
| 6 | LLM error handling | LLM timeout/error → ระบบตอบ 503 อย่างสง่างาม |
| 7 | Thai language E2E | Query ภาษาไทย → retrieve ภาษาไทย → ตอบภาษาไทย |

---

## โครงสร้างโค้ด

```
tests/
├── integration/
│   ├── conftest.py           ← Test fixtures (FastAPI test client, test docs)
│   └── test_scenarios.py     ← 7 scenario classes
│       ├── TestScenario1EmployeeUploadAndQuery
│       ├── TestScenario2CustomerPermissionFilter
│       ├── TestScenario3LineWebhookE2E
│       ├── TestScenario4ConcurrentQueries
│       ├── TestScenario5ComponentSwap
│       ├── TestScenario6LLMErrorHandling
│       └── TestScenario7ThaiLanguageE2E
└── load/
    └── locustfile.py         ← Locust load test (login + chat + search)
```

---

## Performance Targets

| Metric | Target | หมายเหตุ |
|--------|--------|---------|
| E2E latency p50 | < 3 วินาที | รวม LLM generation |
| E2E latency p95 | < 8 วินาที | รวม LLM generation |
| Retrieval latency p95 | < 200ms | Vector search เท่านั้น |
| Throughput | > 50 req/sec | Concurrent users |
| Integration test pass rate | 100% | ทุก 7 scenarios |

---

## วิธีใช้งาน

### ข้อกำหนดเบื้องต้น
- ไม่ต้องการ API key (tests ใช้ mock LLM)
- ไม่ต้องการ Docker

### Step 1: ติดตั้ง dependencies

```bash
make install-test
# หรือ: uv sync --group test
# (รวม api group อัตโนมัติ)
```

### Step 2: รัน Integration Tests

```bash
# รันทุก 7 scenarios (~27 tests)
make test-integration

# ดู output แบบ verbose (full tracebacks)
make test-integration-verbose
```

### รัน Scenario เดียว

```bash
# เลือก scenario ที่ต้องการ
uv run pytest tests/integration/ -v -k "TestScenario1"
uv run pytest tests/integration/ -v -k "TestScenario2"
uv run pytest tests/integration/ -v -k "TestScenario3"
uv run pytest tests/integration/ -v -k "TestScenario4"
uv run pytest tests/integration/ -v -k "TestScenario5"
uv run pytest tests/integration/ -v -k "TestScenario6"
uv run pytest tests/integration/ -v -k "TestScenario7"

# เรียกชื่อ class เต็ม
uv run pytest tests/integration/test_scenarios.py::TestScenario7ThaiLanguageE2E -v
```

### รัน Load Test (Locust)

```bash
# Terminal 1: เริ่ม API server
make api-run

# Terminal 2: รัน load test
make load-test                   # 50 users, ramp 5/s, 30 วินาที

# ปรับ parameters
make load-test U=100 R=10 T=60s  # 100 users, ramp 10/s, 60 วินาที
```

### Locust Interactive UI

```bash
# Terminal 1: เริ่ม API server
make api-run

# Terminal 2: เริ่ม Locust UI
uv run locust -f tests/load/locustfile.py --host=http://localhost:8000

# เปิด browser: http://localhost:8089
# กำหนด users, ramp-up rate แล้วกด Start
```

---

## ตัวอย่าง Test Output

```
tests/integration/test_scenarios.py::TestScenario1EmployeeUploadAndQuery::test_upload_document PASSED
tests/integration/test_scenarios.py::TestScenario1EmployeeUploadAndQuery::test_index_document PASSED
tests/integration/test_scenarios.py::TestScenario1EmployeeUploadAndQuery::test_query_returns_uploaded_content PASSED
tests/integration/test_scenarios.py::TestScenario2CustomerPermissionFilter::test_customer_cannot_see_internal_docs PASSED
...
================================ 27 passed in 3.42s ================================
```

---

## ผลลัพธ์ที่ได้ (Output)

1. **Test pass/fail report** — ทุก 7 scenarios ผ่านหรือเปล่า
2. **Performance metrics** — latency measurements จาก load test
3. **Integration issues** — bugs หรือ design flaws ที่พบระหว่างทดสอบ
4. **Throughput report** — Locust summary (RPS, failure rate, percentiles)

---

## ความสำคัญของ Scenario 5: Component Swap

Scenario 5 พิสูจน์ว่า **Anti-Vendor-Lock-in architecture ทำงานได้จริง** — ไม่ใช่แค่ทฤษฎี

ทดสอบว่า:
- Swap retrieval strategy ได้โดยไม่แก้ API code
- Abstraction layer ทำงานถูกต้องหลัง swap
- ผลลัพธ์ยังสอดคล้องกับ expected behavior

---

## คำถามที่ต้องตอบได้หลัง Phase 5

1. ระบบผ่าน performance targets ทุกตัวหรือไม่? ตัวไหนที่ยังไม่ผ่าน?
2. มี integration issues อะไรที่พบระหว่างทดสอบ?
3. Component swap ทำงานได้จริงตาม architecture ที่ออกแบบไว้?
4. Thai language end-to-end flow ทำงานถูกต้องหรือมี tokenization issues?
