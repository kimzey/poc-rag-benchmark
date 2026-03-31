# Phase 4: API Layer & Authentication Design

## คืออะไร?

Phase 4 เป็น PoC ของ **API Server** ที่รวม components จาก Phase 1-3.5 เข้าด้วยกัน พร้อมระบบ Auth สำหรับ Multi-tenant (Employee + Customer) และรองรับ Omnichannel (Web, LINE, Discord ฯลฯ)

```
Client (Web/LINE/Discord)
         │
         ▼
    FastAPI Server
    ├── JWT Authentication
    ├── RBAC Authorization
    ├── Permission-filtered Retrieval
    │
    ├── Vector DB (ค้นหาเอกสาร)
    ├── Embedding Model (แปลงคำถาม)
    └── LLM Provider (สร้างคำตอบ)
```

---

## ทำไมต้องออกแบบ API Layer?

ระบบ RAG ที่ดีต้องรองรับ:
1. **หลาย client platforms** — Web, LINE, Discord ผ่าน API เดียวกัน
2. **หลาย user types** — Employee เห็นข้อมูลภายใน, Customer เห็นแค่ข้อมูลสาธารณะ
3. **Document-level access control** — แค่ filter ที่ API ไม่พอ ต้อง filter ตอน retrieval ด้วย
4. **Anti-lock-in** — เปลี่ยน Vector DB / LLM ได้โดยไม่แก้ API layer

---

## โครงสร้างโค้ด

```
api/
├── main.py               ← FastAPI application entry point
├── config.py             ← Settings จาก .env (JWT secret, LLM config)
├── store.py              ← In-memory document store (PoC — ไม่มี real DB)
├── auth/
│   ├── models.py         ← User, Permission, AccessLevel dataclasses
│   └── dependencies.py   ← FastAPI dependencies (get_current_user)
├── rag/
│   ├── models.py         ← RAGRequest, RAGResponse dataclasses
│   ├── pipeline.py       ← RAG pipeline (embed → retrieve → generate)
│   └── retrieval.py      ← Permission-filtered vector retrieval
└── routes/
    ├── auth_routes.py    ← POST /auth/token
    ├── chat.py           ← POST /chat/completions
    ├── documents.py      ← POST /documents/upload, GET /documents/search
    └── webhooks/
        └── line.py       ← POST /webhooks/line (LINE Messaging API adapter)
```

---

## API Endpoints

| Method | Path | Auth | ทำอะไร |
|--------|------|------|--------|
| `POST` | `/api/v1/auth/token` | — | Login → JWT token |
| `GET` | `/api/v1/me` | ✓ | ดู user info + permissions |
| `POST` | `/api/v1/chat/completions` | ✓ | RAG query (ค้นหา + ตอบคำถาม) |
| `POST` | `/api/v1/documents/upload` | ✓ employee+ | Upload เอกสาร |
| `GET` | `/api/v1/documents/search` | ✓ | ค้นหาเอกสาร (permission-filtered) |
| `POST` | `/api/v1/documents/index` | ✓ employee+ | Trigger indexing |
| `GET` | `/api/v1/documents/collections` | ✓ | List collections |
| `POST` | `/api/v1/webhooks/line` | LINE signature | LINE webhook receiver |

---

## ระบบ Users & Permissions

### User Types

| Type | ตัวอย่าง user | สิ่งที่เข้าถึงได้ |
|------|-------------|----------------|
| **admin** | `alice_admin` | ทุกอย่าง + user management |
| **employee** | `bob_employee` | Internal KB + Customer KB, upload docs |
| **customer** | `carol_customer` | Customer KB เท่านั้น, ห้าม upload |
| **service** | `svc_line_bot` | อ่าน + query (สำหรับ LINE bot) |

### Permission Matrix

| Resource | admin | employee | customer | service |
|---------|-------|----------|---------|---------|
| Internal KB | ✅ CRUD | ✅ Read | ❌ | ✅ Read |
| Customer KB | ✅ CRUD | ✅ Read | ✅ Read | ✅ Read |
| Upload docs | ✅ | ✅ | ❌ | ❌ |
| User management | ✅ | ❌ | ❌ | ❌ |

### Permission-Filtered Retrieval

ข้อมูลสำคัญ: **filter ทำที่ retrieval step** ไม่ใช่แค่ที่ API

```python
# ทุก query จะ filter ตาม user.allowed_access_levels
vector_search(
    query_vector,
    filter={"access_level": {"$in": user.allowed_access_levels}}
)
```

ทำให้แน่ใจว่า Customer ไม่สามารถเห็นเอกสาร Internal แม้ว่าจะพยายาม bypass API

---

## Test Users (Built-in สำหรับ PoC)

| Username | Password | Role |
|----------|----------|------|
| `alice_admin` | `admin123` | admin |
| `bob_employee` | `emp123` | employee |
| `carol_customer` | `cust123` | customer |
| `svc_line_bot` | `svc123` | service |

> หมายเหตุ: PoC ใช้ hardcoded users ใน memory — Production จะใช้ database จริง

---

## LINE Webhook Adapter

```
LINE App  →  POST /api/v1/webhooks/line
              │
              ▼
        ตรวจสอบ LINE signature
              │
              ▼
        แปลง LINE message format
        → RAG Chat Request (standard)
              │
              ▼
        RAG Pipeline (เหมือนกับ Web client)
              │
              ▼
        LINE Reply API
```

Channel Adapter Pattern: LINE adapter แปลง format แล้วส่งให้ core RAG service — core ไม่รู้ว่า request มาจาก LINE หรือ Web

---

## วิธีใช้งาน

### Step 1: ติดตั้ง dependencies

```bash
make install-api
# หรือ: uv sync --group api
```

### Step 2: กรอก API Keys (Optional)

```bash
# .env
# ถ้าไม่กรอก OPENROUTER_API_KEY → ใช้ mock LLM response อัตโนมัติ
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-4o-mini

# JWT settings
JWT_SECRET_KEY=change-me-in-production
JWT_EXPIRE_MINUTES=60

# LINE (optional)
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

### Step 3: รัน API Server

```bash
make api-run
# → http://localhost:8000/docs   (Swagger UI — ทดสอบ API ได้เลย)
# → http://localhost:8000/redoc  (ReDoc)
```

### Step 4: Smoke Test

```bash
# รัน quick demo (login + query + แสดงผล)
make api-demo
```

### ดูเอกสาร API แบบ interactive

เปิด browser ไปที่ `http://localhost:8000/docs` จะเห็น Swagger UI ที่ทดสอบ API ได้เลย

---

## ผลลัพธ์ที่ได้ (Output)

1. **Working PoC API** — FastAPI server ที่ทดสอบได้จริง
2. **Auth design** — JWT + RBAC pattern ที่พิสูจน์แล้วว่าใช้ได้
3. **Permission-filtered retrieval** — แสดงให้เห็นว่า access control ทำงานถูกต้อง
4. **LINE adapter** — ตัวอย่าง channel adapter pattern
5. **API design decisions** — เป็น input สำหรับ RFC document

---

## คำถามที่ต้องตอบได้หลัง Phase 4

1. RBAC เพียงพอหรือต้อง ABAC? (depends on permission granularity)
2. Document-level access control ทำที่ application layer — ดีพอสำหรับ production?
3. Keycloak/Auth0 vs custom JWT — trade-off ของ control vs operational cost?
4. Multi-tenancy — แยก data ระดับ collection หรือ metadata filter ดีกว่า?
