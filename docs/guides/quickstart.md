# คู่มือเริ่มต้นใช้งาน (Quickstart Guide)

## ข้อกำหนดเบื้องต้น

ก่อนเริ่ม ต้องมีสิ่งเหล่านี้:

```bash
# ตรวจสอบ
python3 --version   # ต้องเป็น 3.11 ขึ้นไป
uv --version        # ต้องเป็น 0.5 ขึ้นไป
docker --version    # จำเป็นเฉพาะ Phase 1
```

### ติดตั้ง uv (ถ้ายังไม่มี)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env   # หรือ restart terminal

# macOS (Homebrew)
brew install uv
```

### ติดตั้ง Python (ถ้าต้องการ)

```bash
# macOS (Homebrew)
brew install python@3.13

# หรือปล่อยให้ uv จัดการ
uv python install 3.13
```

---

## Setup ครั้งแรก

```bash
# 1. Clone repo
git clone <repo-url>
cd spike-rak

# 2. สร้าง .env จาก template
cp .env.example .env

# 3. ตรวจสอบ setup
make setup
```

### กรอก API Keys ใน .env

เปิดไฟล์ `.env` และกรอกค่าที่ต้องการ:

```bash
# Phase 2, 3.5, 4: LLM
OPENROUTER_API_KEY=sk-or-...          # https://openrouter.ai (สมัครฟรี)
RAG_LLM_MODEL=openai/gpt-4o-mini

# Phase 3: Embedding (OpenAI models เท่านั้น)
OPENAI_API_KEY=sk-...                 # ไม่จำเป็น ถ้าใช้แค่ open-source models

# Phase 3.5: Anthropic (optional)
ANTHROPIC_API_KEY=sk-ant-...

# Phase 4-5: API Server
JWT_SECRET_KEY=my-secret-key-change-in-production
```

> หมายเหตุ: หลาย phase ทำงานได้โดยไม่ต้องการ API key — ดูรายละเอียดในแต่ละ phase

---

## เส้นทางด่วน — เลือกตามสิ่งที่ต้องการ

### ต้องการ: ทดสอบ API Server (Phase 4)

```bash
make install-api && make api-run
# เปิด http://localhost:8000/docs
```

### ต้องการ: รัน Integration Tests (Phase 5)

```bash
make install-test && make test-integration
```

### ต้องการ: เปรียบเทียบ Vector DB (Phase 1)

```bash
make up-db && make install && make benchmark-quick
```

### ต้องการ: เปรียบเทียบ Embedding Models (Phase 3)

```bash
make install-embed && make embed-eval     # ไม่ต้องการ API key
```

### ต้องการ: ทดสอบ LLM Providers (Phase 3.5)

```bash
# ต้องกรอก OPENROUTER_API_KEY ก่อน
make install-llm && make llm-eval
```

---

## Phase-by-Phase Guide

### Phase 1 — Vector DB Benchmark

**ต้องการ:** Docker
**ไม่ต้องการ:** API keys

```bash
# เริ่ม Vector DBs
make up-db

# ติดตั้ง deps
make install

# รัน benchmark (10K vectors)
make benchmark-quick

# หยุดเมื่อเสร็จ
make down-db
```

ดูรายละเอียด: [phases/phase-1-vector-db.md](../phases/phase-1-vector-db.md)

---

### Phase 2 — RAG Framework Comparison

**ต้องการ:** ~2GB disk
**API Key:** `OPENROUTER_API_KEY` (optional — รัน `--no-llm` ได้ถ้าไม่มี)

```bash
make install-rag

# ถ้ามี API key
make rag-eval

# ถ้าไม่มี API key
make rag-eval-no-llm
```

ดูรายละเอียด: [phases/phase-2-rag-framework.md](../phases/phase-2-rag-framework.md)

---

### Phase 3 — Embedding Model Comparison

**ต้องการ:** ~1.5GB disk, ~4GB RAM (สำหรับ local models)
**API Key:** `OPENAI_API_KEY` (optional — open-source models ไม่ต้องการ)

```bash
make install-embed

# Open-source models (ไม่ต้องการ API key)
make embed-eval

# ทุก models รวม OpenAI (ต้องการ OPENAI_API_KEY)
make embed-eval-all
```

ดูรายละเอียด: [phases/phase-3-embedding.md](../phases/phase-3-embedding.md)

---

### Phase 3.5 — LLM Provider Comparison

**API Key:** `OPENROUTER_API_KEY` (อย่างน้อย 1 provider)

```bash
make install-llm

make llm-eval         # default: openrouter
make llm-eval-all     # ทุก providers ที่มี key
```

ดูรายละเอียด: [phases/phase-3.5-llm-provider.md](../phases/phase-3.5-llm-provider.md)

---

### Phase 4 — API Server

**API Key:** `OPENROUTER_API_KEY` (optional — mock LLM ถ้าไม่มี)

```bash
make install-api

# เริ่ม server
make api-run
# → http://localhost:8000/docs

# Smoke test
make api-demo
```

ดูรายละเอียด: [phases/phase-4-api-auth.md](../phases/phase-4-api-auth.md)

---

### Phase 5 — Integration Tests

**ไม่ต้องการ:** API keys, Docker

```bash
make install-test

# Integration tests
make test-integration

# Load test (ต้องรัน api-run ก่อน)
make api-run          # Terminal 1
make load-test        # Terminal 2
```

ดูรายละเอียด: [phases/phase-5-integration.md](../phases/phase-5-integration.md)

---

## คำสั่ง make ทั้งหมด

```bash
make help   # แสดงคำสั่งทั้งหมดพร้อมคำอธิบาย
```

| คำสั่ง | ทำอะไร | Phase |
|-------|--------|-------|
| `make setup` | ตรวจสอบ setup + แสดง quick-start | — |
| `make up-db` | เริ่ม Vector DBs ทั้งหมด | 1 |
| `make up-db DB=qdrant` | เริ่ม DB เดียว | 1 |
| `make down-db` | หยุด + ลบ DB volumes | 1 |
| `make install` | ติดตั้ง deps Phase 1 | 1 |
| `make benchmark-quick` | Benchmark 10K vectors | 1 |
| `make benchmark-medium` | Benchmark 100K vectors | 1 |
| `make install-rag` | ติดตั้ง deps Phase 2 | 2 |
| `make rag-eval` | รัน RAG framework evaluation | 2 |
| `make rag-eval-no-llm` | รัน indexing เท่านั้น | 2 |
| `make install-embed` | ติดตั้ง deps Phase 3 | 3 |
| `make embed-eval` | รัน embedding evaluation (open-source) | 3 |
| `make embed-eval-all` | รันทุก models รวม OpenAI | 3 |
| `make install-llm` | ติดตั้ง deps Phase 3.5 | 3.5 |
| `make llm-eval` | รัน LLM evaluation (default) | 3.5 |
| `make install-api` | ติดตั้ง deps Phase 4 | 4 |
| `make api-run` | เริ่ม FastAPI server | 4 |
| `make api-demo` | Smoke test API | 4 |
| `make install-test` | ติดตั้ง deps Phase 5 | 5 |
| `make test-integration` | รัน integration tests | 5 |
| `make load-test` | รัน load test (Locust) | 5 |

---

## Troubleshooting

### `uv: command not found`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
# หรือ restart terminal
```

### `ModuleNotFoundError` หลัง switch phases

```bash
# Re-sync ให้ตรงกับ phase ที่ต้องการ
make install-api    # สำหรับ Phase 4
make install-test   # สำหรับ Phase 5
```

### Port 8000 ถูกใช้งานอยู่

```bash
lsof -ti:8000 | xargs kill -9
make api-run
```

### Docker ไม่ทำงาน (Phase 1)

```bash
open -a Docker   # macOS — เปิด Docker Desktop
# รอให้ Docker start แล้ว
make up-db
```

### Model download ช้า (Phase 2-3)

```bash
# Models เก็บใน .cache/ — download แค่ครั้งแรก
# ครั้งแรกอาจใช้เวลา 5-15 นาที ขึ้นอยู่กับขนาด model
# ครั้งถัดไปจะโหลดจาก cache ทันที
```

### API ตอบช้าหรือ error เมื่อไม่มี API key

```bash
# ถ้าไม่มี OPENROUTER_API_KEY → API จะใช้ mock LLM อัตโนมัติ
# Mock LLM ตอบเร็วมาก (ไม่ต้องเรียก external API)
# ถ้าต้องการ real LLM response ต้องกรอก key ใน .env
```

---

## การจัดการ Dependencies (uv)

```bash
# ดู packages ที่ติดตั้งอยู่
uv pip list

# เพิ่ม package ใหม่
uv add --group api "some-package>=1.0"

# ติดตั้งหลาย group พร้อมกัน
uv sync --group api --group test

# Activate venv แบบ manual (ถ้าต้องการ)
source .venv/bin/activate
```

> **Note:** ปกติไม่ต้อง activate venv เลย — ใช้ `uv run <command>` หรือ `make <target>` แทน
