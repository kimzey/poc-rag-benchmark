# ADR-004: LLM Provider Strategy

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-004 |
| **สถานะ** | 🟡 Draft |
| **วันที่** | 2026-03-31 |
| **Deciders** | Engineering Team, พี่ตั๊ก |
| **Phase** | Phase 3.5 |

---

## บริบท (Context)

เราต้องเลือก strategy สำหรับ LLM — ทั้ง **provider** (OpenAI, Anthropic, etc.) และ **access pattern** (direct vs gateway)

**คำถามหลัก:**  
ควรเชื่อมต่อ LLM providers โดยตรง หรือผ่าน **OpenRouter** ซึ่งเป็น unified API gateway?

OpenRouter ให้ประโยชน์ด้าน Anti-Vendor-Lock-in โดยตรง — เปลี่ยน model ได้แค่เปลี่ยน string โดยไม่แก้ code แต่มี trade-off ด้าน latency overhead และ dependency เพิ่มขึ้น

เราทดสอบ: **OpenRouter**, **OpenAI Direct**, **Anthropic Direct**, **Ollama (local)**

---

## Decision

> **[TODO หลัง Phase 3.5 เสร็จ — กรอกตรงนี้]**
>
> Primary strategy: _______________  
> Primary model: _______________  
> Fallback plan: _______________

---

## เหตุผล (Rationale)

> **[TODO]**

**Benchmark summary:**

| Provider | Latency p50 (ms) | Quality score | Cost/1K queries | Thai quality |
|---------|-----------------|---------------|-----------------|-------------|
| OpenRouter (gpt-4o-mini) | — | — | — | — |
| OpenAI Direct | — | — | — | — |
| Anthropic Direct | — | — | — | — |
| Ollama (local) | — | — | $0 | — |

**OpenRouter latency overhead vs direct:**
> [TODO] — วัดจาก Phase 3.5

**เหตุผลสำคัญ:**
- [TODO]

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- [TODO]

**ข้อเสีย / Trade-offs:**
- [TODO]

**ถ้าเลือก OpenRouter:**
- ต้องมี fallback plan ถ้า OpenRouter เองมีปัญหา
- ควรมี circuit breaker pattern
- Monitor OpenRouter SLA / uptime

**ถ้าเลือก Direct API:**
- Lock-in สูงกว่า — migration cost มากขึ้นถ้าเปลี่ยน
- แต่ latency ดีกว่าและ dependency น้อยกว่า

---

## Migration Path

> เนื่องจากใช้ `LLMClient` interface — เปลี่ยน provider ได้โดยแก้ adapter + config  
> ถ้าใช้ OpenRouter: เปลี่ยน model แค่เปลี่ยน `OPENROUTER_MODEL` env var

---

## ข้อมูลที่ใช้ตัดสินใจ

- Evaluation results: `benchmarks/llm-provider/`
- Phase 3.5 notes: `docs/phases/phase-3.5-llm-provider.md`
- OpenRouter pricing: https://openrouter.ai/models
