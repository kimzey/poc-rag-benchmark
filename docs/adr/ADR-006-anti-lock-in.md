# ADR-006: Anti-Vendor-Lock-in Architecture Pattern

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-006 |
| **สถานะ** | 🟢 Accepted |
| **วันที่** | 2026-03-31 |
| **Deciders** | Engineering Team, พี่ตั๊ก |
| **Phase** | All Phases |

---

## บริบท (Context)

ระบบ RAG ใช้ components จากหลาย vendors (Vector DB, Embedding Model, LLM Provider, RAG Framework) ทุกตัวมีความเสี่ยงที่:
- ราคาขึ้นอย่างกะทันหัน
- API เปลี่ยน / deprecate
- บริษัทถูก acquire
- Service ล่มในช่วง critical

**เป้าหมาย:** ออกแบบให้ swap component ได้ภายใน 1-2 วัน โดยไม่ต้อง rewrite business logic

---

## Decision ✅

**ใช้ Port & Adapter Pattern (Hexagonal Architecture)** สำหรับทุก external dependency

### Architecture

```
┌─────────────────────────────────────────┐
│           Application Layer              │
│  (Business Logic — ไม่รู้จัก infra)      │
├─────────────────────────────────────────┤
│           Port Interfaces                │
│  ┌────────────┐ ┌──────────┐ ┌────────┐ │
│  │VectorStore │ │Embedder  │ │LLMClient│ │
│  │ Interface  │ │Interface │ │Interface│ │
│  └─────┬──────┘ └────┬─────┘ └────┬───┘ │
├────────┼─────────────┼────────────┼─────┤
│        │    Adapter Layer         │      │
│  ┌─────▼────┐  ┌─────▼────┐ ┌────▼────┐ │
│  │Qdrant    │  │BGE-M3    │ │OpenRouter│ │
│  │Adapter   │  │Adapter   │ │Adapter  │ │
│  ├──────────┤  ├──────────┤ ├─────────┤ │
│  │pgvector  │  │OAI Embed │ │Direct   │ │
│  │Adapter   │  │Adapter   │ │Adapter  │ │
│  └──────────┘  └──────────┘ └─────────┘ │
└─────────────────────────────────────────┘
```

### 6 Iron Rules

| # | หลักการ | Implementation |
|---|--------|---------------|
| 1 | **Abstraction over Implementation** | ทุก external dependency อยู่หลัง abstract class/interface |
| 2 | **Port & Adapter Pattern** | Business logic ไม่ import vendor library ตรง |
| 3 | **Configuration over Code** | เปลี่ยน provider ผ่าน `.env` / config — ไม่แก้ code |
| 4 | **Standard Protocols** | ใช้ OpenAI-compatible API เมื่อเป็นไปได้ |
| 5 | **Data Portability** | Data export/import ในรูปแบบ standard |
| 6 | **Multi-Provider Testing** | PoC ทดสอบกับ ≥ 2 providers เสมอ |

---

## เหตุผล (Rationale)

Decision นี้ **ตัดสินใจไว้ตั้งแต่ต้น** และ Spike ทั้งหมดออกแบบให้พิสูจน์หลักการนี้

**PoC พิสูจน์แล้วว่า:**

| ลำดับ | สิ่งที่พิสูจน์ | ที่ไหน |
|-------|-------------|-------|
| ✅ | Vector DB swap ได้โดยแก้แค่ config | `benchmarks/vector-db/clients/` |
| ✅ | RAG Framework swap ได้โดยแก้แค่ adapter | `benchmarks/rag-framework/frameworks/` |
| ✅ | LLM swap ได้โดยเปลี่ยน model string เดียว | `benchmarks/llm-provider/providers/` |
| ✅ | Embedding model swap ได้ผ่าน config | `benchmarks/embedding-model/models/` |
| ⬜ | Integration test Scenario 5: Component swap | `tests/integration/test_scenarios.py` |

---

## Checklist สำหรับทุก Component ที่เลือก

ก่อน finalize decision บน component ใดก็ตาม ต้องตอบคำถามเหล่านี้ได้:

- [ ] ถ้า vendor นี้ถูก acquire หรือ deprecate — เราเปลี่ยนได้ภายในกี่วัน?
- [ ] มี open-source alternative ที่ใช้แทนได้ไหม?
- [ ] Data ของเรา export ออกมาในรูปแบบ standard ได้ไหม?
- [ ] API ที่ใช้เป็น proprietary หรือ standard protocol?
- [ ] มี abstraction layer กั้นระหว่าง business logic กับ vendor-specific code ไหม?

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- เปลี่ยน component ได้เร็ว — ลด business risk จาก vendor dependency
- ทดสอบ A/B ระหว่าง providers ได้ง่าย
- Migration path ชัดเจนสำหรับทุก component

**ข้อเสีย / Trade-offs:**
- Code เพิ่มขึ้น — ต้องเขียน adapter สำหรับทุก provider
- Abstraction อาจ obscure vendor-specific features ที่มีประโยชน์
- Developer ต้อง understand interface layer ก่อนเพิ่ม provider ใหม่

**ข้อกำหนดสำหรับ Production Codebase:**
- ทุก PR ที่เพิ่ม external dependency ใหม่ → ต้องมี adapter + interface
- ห้าม import vendor library ตรงใน service/business logic layer
- Config-driven provider selection ผ่าน env vars เสมอ
