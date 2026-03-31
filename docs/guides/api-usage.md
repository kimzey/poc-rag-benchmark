# คู่มือการใช้งาน API Server (Phase 4)

## ภาพรวม

API Server เป็น FastAPI application ที่รวม RAG pipeline + Auth + Permission control ไว้ด้วยกัน

**Base URL:** `http://localhost:8000`  
**API Docs:** `http://localhost:8000/docs` (Swagger UI — ทดสอบ interactive ได้เลย)  
**ReDoc:** `http://localhost:8000/redoc`

---

## เริ่มต้น Server

```bash
make install-api    # ติดตั้ง deps (ครั้งแรก)
make api-run        # เริ่ม server
```

---

## Authentication Flow

ระบบใช้ **JWT (JSON Web Token)** — ต้อง login ก่อน แล้วนำ token ไปใช้กับทุก endpoint

### Step 1: Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "bob_employee", "password": "emp123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Step 2: ใช้ Token กับ Requests

```bash
# เก็บ token ใน variable
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"bob_employee","password":"emp123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# ใช้ token ใน header
curl http://localhost:8000/api/v1/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## Test Users

| Username | Password | Role | สิทธิ์ |
|----------|----------|------|------|
| `alice_admin` | `admin123` | admin | ทุกอย่าง |
| `bob_employee` | `emp123` | employee | อ่าน + upload + index + query |
| `carol_customer` | `cust123` | customer | อ่าน customer docs + query |
| `svc_line_bot` | `svc123` | service | อ่าน + query (สำหรับ bot integrations) |

---

## Endpoints

### GET /api/v1/me — ดู User Info

ดูข้อมูล user ปัจจุบัน + permissions ทั้งหมด

```bash
curl http://localhost:8000/api/v1/me \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "user_id": "u-002",
  "username": "bob_employee",
  "user_type": "employee",
  "permissions": ["chat:query", "doc:index", "doc:read", "doc:upload"],
  "allowed_access_levels": ["customer", "internal"]
}
```

---

### POST /api/v1/chat/completions — RAG Query

**หัวใจหลักของระบบ** — รับคำถาม แล้วค้นหาเอกสารที่เกี่ยวข้อง + ตอบด้วย LLM

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "นโยบายการลาพักร้อนเป็นอย่างไร?"}
    ],
    "top_k": 3
  }'
```

Request body:
```json
{
  "messages": [
    {"role": "user", "content": "คำถามของผู้ใช้"}
  ],
  "top_k": 3,
  "collection": null
}
```

| Parameter | ประเภท | Default | คำอธิบาย |
|-----------|--------|---------|---------|
| `messages` | array | — | ประวัติการสนทนา (format เหมือน OpenAI) |
| `top_k` | int | 3 | จำนวนเอกสารที่ดึงมาใช้เป็น context |
| `collection` | string | null | ระบุ collection เฉพาะ (null = ค้นทุก collection) |

Response:
```json
{
  "message": {
    "role": "assistant",
    "content": "นโยบายการลาพักร้อนของบริษัท..."
  },
  "sources": [
    {
      "doc_id": "doc-001",
      "title": "HR Policy 2024",
      "access_level": "internal",
      "score": 0.92
    }
  ],
  "model": "openai/gpt-4o-mini",
  "usage": {
    "prompt_tokens": 450,
    "completion_tokens": 120,
    "total_tokens": 570
  }
}
```

> **Permission note:** sources จะแสดงเฉพาะเอกสารที่ user มีสิทธิ์เข้าถึง — Customer จะไม่เห็น internal docs แม้อยู่ใน context

---

### POST /api/v1/documents/upload — Upload เอกสาร

**ต้องการสิทธิ์:** employee หรือสูงกว่า

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "HR Policy 2024",
    "content": "นโยบายการลาพักร้อน: พนักงานมีสิทธิ์ลา 10 วันต่อปี...",
    "access_level": "internal",
    "collection": "hr-policies"
  }'
```

| Parameter | ประเภท | คำอธิบาย |
|-----------|--------|---------|
| `title` | string | ชื่อเอกสาร |
| `content` | string | เนื้อหาเอกสาร (text) |
| `access_level` | string | `"internal"` หรือ `"customer"` |
| `collection` | string | ชื่อ collection |

---

### POST /api/v1/documents/index — Trigger Indexing

**ต้องการสิทธิ์:** employee หรือสูงกว่า

```bash
curl -X POST http://localhost:8000/api/v1/documents/index \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"collection": "hr-policies"}'
```

> PoC นี้ auto-index เมื่อ upload แล้ว — endpoint นี้สำหรับ trigger manual re-index

---

### GET /api/v1/documents/search — ค้นหาเอกสาร

ค้นหาเอกสารโดย semantic search (permission-filtered)

```bash
curl "http://localhost:8000/api/v1/documents/search?q=นโยบายลา&top_k=5" \
  -H "Authorization: Bearer $TOKEN"
```

Query parameters:
| Parameter | Default | คำอธิบาย |
|-----------|---------|---------|
| `q` | — | คำค้นหา |
| `top_k` | 5 | จำนวนผลลัพธ์ |
| `collection` | null | ระบุ collection เฉพาะ |

---

### GET /api/v1/documents/collections — List Collections

```bash
curl http://localhost:8000/api/v1/documents/collections \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "collections": [
    {"name": "hr-policies", "count": 12, "access_level": "internal"},
    {"name": "product-faq", "count": 45, "access_level": "customer"}
  ]
}
```

---

### POST /api/v1/webhooks/line — LINE Webhook

Endpoint นี้รับ webhook จาก LINE Messaging API

```bash
# LINE ส่งมาให้อัตโนมัติ — ทดสอบแบบ manual:
curl -X POST http://localhost:8000/api/v1/webhooks/line \
  -H "Content-Type: application/json" \
  -H "X-Line-Signature: <LINE_SIGNATURE>" \
  -d '{
    "destination": "Uxxxxxxxx",
    "events": [
      {
        "type": "message",
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "source": {"userId": "U4af4980629..."},
        "message": {"type": "text", "text": "RAG คืออะไร?"}
      }
    ]
  }'
```

> ต้องกรอก `LINE_CHANNEL_SECRET` และ `LINE_CHANNEL_ACCESS_TOKEN` ใน `.env` ก่อน

---

## ตัวอย่าง: เปรียบเทียบสิทธิ์ Employee vs Customer

```bash
# Login เป็น employee
EMP_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"bob_employee","password":"emp123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Login เป็น customer
CUST_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"carol_customer","password":"cust123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Query เหมือนกัน — แต่ผลต่างกัน
echo "=== Employee query ==="
curl -s -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer $EMP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"นโยบายภายใน?"}]}' | python3 -m json.tool

echo "=== Customer query (ไม่เห็น internal docs) ==="
curl -s -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer $CUST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"นโยบายภายใน?"}]}' | python3 -m json.tool
```

---

## Error Codes

| Status | ความหมาย |
|--------|---------|
| `200` | สำเร็จ |
| `401` | ไม่มี token หรือ token expired |
| `403` | ไม่มีสิทธิ์ทำ action นี้ |
| `404` | ไม่พบ resource |
| `422` | Request body ไม่ถูกต้อง |
| `503` | LLM ไม่ตอบสนอง (timeout หรือ error) |

---

## Environment Variables

| Variable | Default | คำอธิบาย |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | — | API key (ไม่กรอก = ใช้ mock LLM) |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Model ที่ใช้ |
| `JWT_SECRET_KEY` | `change-me` | Secret key สำหรับ sign JWT |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXPIRE_MINUTES` | `60` | Token expire time (นาที) |
| `LINE_CHANNEL_SECRET` | — | LINE webhook signature verification |
| `LINE_CHANNEL_ACCESS_TOKEN` | — | LINE Reply API token |
