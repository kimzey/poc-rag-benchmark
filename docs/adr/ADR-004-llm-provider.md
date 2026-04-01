# ADR-004: LLM Provider Strategy

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-004 |
| **สถานะ** | 🟢 Accepted |
| **วันที่** | 2026-04-01 |
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

**Primary strategy: OpenRouter (unified gateway)**  
**Primary model: google/gemini-2.0-flash-001**  
**Fallback plan: meta-llama/llama-3.1-70b-instruct** (ผ่าน OpenRouter เช่นกัน — open-source, self-hostable ได้ถ้าจำเป็น)

OpenRouter ให้ anti-vendor-lock-in สูงสุด และ gemini-2.0-flash มี weighted score สูงสุดจาก benchmark ด้วยต้นทุนต่ำ

---

## เหตุผล (Rationale)

**Benchmark ครบ 7 providers — Phase 3.5 (10 queries: Thai HR, English API, Thai Mixed, English Security):**

| Provider | Model | Overall F1 | Thai F1 | Avg Latency (ms) | Cost/10 queries | Lock-in | **Weighted Score** |
|---------|-------|-----------|---------|-----------------|----------------|---------|-----------------|
| **OpenRouter** | **gemini-2.0-flash-001** | **0.4601** | **0.4785** | **1,066** | **$0.003146** | 2 | **0.8686** |
| OpenRouter | llama-3.1-70b-instruct | 0.4586 | 0.4654 | 2,195 | $0.01186 | 0 | 0.8008 |
| OpenRouter | gpt-4o | 0.4689 | 0.4061 | 1,503 | $0.080885 | 3 | 0.6117 |
| OpenRouter | gpt-4o-mini | 0.4334 | 0.4394 | 2,377 | $0.00489 | 3 | 0.5645 |
| OpenAI Direct | gpt-4o-mini | 0.4360 | 0.4438 | 1,440 | $0.004886 | 9 | 0.5002 |
| OpenRouter | deepseek-r1 | 0.4264 | 0.3974 | 2,993 | $0.00454 | 1 | 0.4850 |
| OpenAI Direct | gpt-4o | 0.4651 | 0.3997 | 1,192 | $0.081245 | 9 | 0.4552 |

> Weights: Overall quality 20%, Anti-lock-in 20%, Cost 15%, Latency 15%, Thai quality 10%, Reliability 10%, Privacy 5%, Ease switching 5%

**OpenRouter vs Direct API — key insight:**
- `openai_gpt4o_mini` (direct, lock-in=9) weighted = 0.5002 vs `openrouter_gpt4o_mini` (lock-in=3) weighted = 0.5645
- การใช้ OpenRouter ช่วยลด lock-in penalty อย่างมีนัยสำคัญแม้ quality/latency เหมือนกัน
- Cost ต่อ query ใกล้เคียงกัน ($0.004886 vs $0.00489)

**เหตุผลหลักที่เลือก OpenRouter + Gemini Flash:**
- Weighted score สูงสุด (0.8686) — balance ดีที่สุดระหว่างทุก dimension
- Thai F1 สูงสุด (0.4785) — สำคัญมากสำหรับ requirement ภาษาไทย
- Latency 1,066ms ดีที่สุดในกลุ่มที่ราคาเหมาะสม
- Cost ต่ำสุดใน top 3 ($0.003146 / 10 queries = ~$0.31/1K queries)
- Lock-in score = 2 (ต่ำ) — เปลี่ยน model ได้ด้วย string เดียว

**เหตุผลที่ไม่เลือกตัวอื่น:**

| ตัวเลือก | เหตุผลที่ไม่เลือก |
|---------|-----------------|
| OpenAI Direct (gpt-4o-mini) | Lock-in = 9 สูงมาก, weighted score ต่ำกว่า OpenRouter version แม้ quality เหมือนกัน |
| OpenRouter gpt-4o | ราคาแพงมาก ($0.080885/10q = 25x ของ gemini-flash) แต่ F1 สูงกว่าเล็กน้อยเท่านั้น |
| OpenRouter llama-3.1-70b | Latency 2,195ms สูง, cost $0.01186 แพงกว่า gemini-flash 3.7x |
| OpenAI Direct gpt-4o | Weighted score ต่ำสุด (0.4552) เพราะ lock-in = 9 + ราคาแพงสุด |

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- เปลี่ยน model ได้ด้วยการเปลี่ยน `OPENROUTER_MODEL` env var เพียงอย่างเดียว
- ไม่ต้องแก้ code เมื่อเปลี่ยน provider — OpenAI-compatible API
- Access ถึง 100+ models ผ่าน API เดียว
- ต้นทุนต่ำมาก — gemini-flash $0.1/1M input tokens

**ข้อเสีย / Trade-offs:**
- มี dependency เพิ่มขึ้น 1 ชั้น (OpenRouter service) — ถ้า OpenRouter มีปัญหา ทั้งระบบได้รับผลกระทบ
- ต้องมี circuit breaker / fallback pattern สำหรับ production
- Data ผ่าน OpenRouter ก่อนถึง model provider — ต้องตรวจสอบ privacy policy ถ้ามี PII

**สิ่งที่ต้องทำสำหรับ Production:**
- [ ] Implement circuit breaker pattern สำหรับ OpenRouter calls
- [ ] กำหนด fallback model (ปัจจุบัน: llama-3.1-70b ผ่าน OpenRouter)
- [ ] Monitor OpenRouter latency/uptime แยกจาก model latency
- [ ] Review data privacy policy ของ OpenRouter สำหรับ sensitive data

---

## Migration Path

> เนื่องจากใช้ `LLMClient` interface — เปลี่ยน provider ได้โดยแก้ adapter + config  
> ถ้าใช้ OpenRouter: เปลี่ยน model แค่เปลี่ยน `OPENROUTER_MODEL` env var

---

## ข้อมูลที่ใช้ตัดสินใจ

- Evaluation results: `benchmarks/llm-provider/`
- Phase 3.5 notes: `docs/phases/phase-3.5-llm-provider.md`
- OpenRouter pricing: https://openrouter.ai/models
