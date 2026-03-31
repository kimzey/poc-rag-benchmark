# FAQ — ระบบ RAG Internal / TechCore Knowledge Base
## คำถามที่พบบ่อย (Frequently Asked Questions)

---

## หมวด: การใช้งาน API (API Usage)

**Q: ฉันจะขอ API Token ได้อย่างไร?**

A: ติดต่อทีม Platform Engineering ผ่าน Slack channel `#platform-help` พร้อมระบุ:
- ชื่อ service ของคุณ
- ประเภท token ที่ต้องการ (Employee / Customer / Service)
- Use case และ expected traffic

Token จะถูกสร้างภายใน 1 วันทำการ

---

**Q: API เรียกใช้ endpoint /query แล้วได้ error 503 ควรทำอย่างไร?**

A: Error 503 (`SERVICE_UNAVAILABLE`) หมายความว่า LLM provider หรือ Vector DB กำลัง downtime ชั่วคราว ให้ทำดังนี้:
1. รอ 30 วินาที แล้ว retry
2. ตรวจสอบ status page ที่ `status.techcore.internal`
3. หากยังไม่หาย ให้แจ้ง `#platform-oncall` บน Slack

---

**Q: Rate limit ของ Customer Token คือเท่าไหร่?**

A: Customer Token มี rate limit **30 requests/นาที** และ **1,000 requests/วัน**
ดูข้อมูลเพิ่มเติมได้จาก headers `X-RateLimit-Remaining` และ `X-RateLimit-Reset` ในทุก response

---

**Q: ฉันจะ upload เอกสาร PDF ได้อย่างไร?**

A: ขณะนี้ endpoint `POST /documents` รับ `content_type: "pdf_text"` ซึ่งต้องแปลง PDF เป็น plain text ก่อน
ในอนาคต (v1.1.0) จะรองรับการ upload ไฟล์ PDF ตรงได้เลย

เครื่องมือแปลง PDF เป็น text ที่แนะนำ:
- Python: `pypdf2` หรือ `pdfplumber`
- CLI: `pdftotext` (poppler)

---

**Q: Webhook signature ตรวจสอบอย่างไร?**

A: ใช้ HMAC-SHA256 กับ webhook secret ที่ตั้งค่าไว้:

```python
import hmac, hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## หมวด: การลาและสิทธิ์พนักงาน (HR & Leave)

**Q: ฉันสามารถสะสมวันลาพักร้อนข้ามปีได้หรือไม่?**

A: โดยปกติ **ไม่สามารถสะสมข้ามปีได้** วันลาพักร้อนที่ไม่ได้ใช้จะหมดอายุเมื่อสิ้นปีปฏิทิน
ยกเว้นกรณีพิเศษที่ได้รับการอนุมัติจาก HR เช่น พนักงานที่ไม่สามารถหยุดได้เนื่องจากโครงการฉุกเฉิน

---

**Q: ถ้าฉันทำงานมา 4 ปี จะได้วันลาพักร้อนกี่วัน?**

A: พนักงานที่ทำงานครบ **3 ปี** จะได้รับวันลาพักร้อน **15 วัน** ต่อปี (เพิ่มจาก 10 วันปกติ)
วันลา 20 วันจะได้รับเมื่อทำงานครบ 5 ปี ดังนั้นที่ปีที่ 4 ยังอยู่ที่ 15 วัน

---

**Q: พนักงาน Probation ใช้ WFH ได้ไหม?**

A: **ไม่ได้** พนักงานในช่วงทดลองงาน (Probation) ไม่มีสิทธิ์ใช้ WFH
สิทธิ์ WFH จะเริ่มต้นหลังผ่านการทดลองงานแล้ว

---

**Q: ฉันต้องการลาพักร้อน 5 วัน ต้องแจ้งล่วงหน้ากี่วัน?**

A: การลา **มากกว่า 3 วัน** ต้องแจ้งล่วงหน้า **2 สัปดาห์** (14 วันปฏิทิน)
การลา 1-3 วัน ต้องแจ้งล่วงหน้า **3 วันทำการ**

---

**Q: OT วันเสาร์ได้รับค่าตอบแทนเท่าไหร่?**

A: OT วันหยุด (รวมถึงวันเสาร์-อาทิตย์และวันหยุดนักขัตฤกษ์) ได้รับค่า OT **3 เท่า** ของอัตราค่าจ้างรายชั่วโมง
สำหรับพนักงาน Senior (Grade 4+) ที่เป็น Salaried จะได้วันหยุดชดเชยแทน ไม่ใช่ค่า OT เป็นเงิน

---

## หมวด: ระบบ Internal Tools

**Q: ใช้ระบบ Performance Review ที่ไหน?**

A: บริษัทใช้ **Lattice** สำหรับ Performance Review ทั้ง Self-assessment และ Manager review
เข้าถึงได้ที่ `lattice.techcore.co.th` ด้วย SSO account ของบริษัท

---

**Q: เอกสาร HR Policy ล่าสุดอยู่ที่ไหน?**

A: อยู่ที่ Notion ของบริษัท: `hr.techcore.co.th/policy`
เข้าถึงได้ด้วย email ของบริษัท (`@techcore.co.th`)

---

**Q: ถ้าลาป่วย 4 วันติดต่อกัน ต้องทำอะไรบ้าง?**

A: ลาป่วยติดต่อกัน **3 วันขึ้นไป** ต้องแนบ **ใบรับรองแพทย์** ส่งให้ HR ผ่าน email หรือ Notion
หากลาป่วยไม่มีใบรับรองแพทย์เกิน **3 ครั้งต่อปี** อาจถูกหัก OT credit หรือต้องใช้วันลากิจแทน

---

## หมวด: Security & Compliance

**Q: API Key หาย / ถูก Compromise ควรทำอะไร?**

A: ทำดังนี้ทันที:
1. แจ้ง `#platform-oncall` บน Slack ว่าขอ **revoke token ด่วน**
2. Platform team จะ revoke token ภายใน 15 นาที
3. ขอ token ใหม่ผ่าน `#platform-help`
4. Review logs ผ่าน `logs.techcore.internal` เพื่อตรวจสอบการใช้งานผิดปกติ

---

**Q: ข้อมูล Customer จัดเก็บอย่างไร ปลอดภัยไหม?**

A: ข้อมูล Customer ถูกจัดเก็บแยกจาก Employee data ด้วย:
- Namespace isolation ใน Vector DB
- RBAC ตาม token type (`customer` visibility filter)
- ข้อมูลทั้งหมด encrypted at rest (AES-256) และ in transit (TLS 1.3)
- Audit log บันทึกทุก query ที่เกี่ยวข้องกับข้อมูล Customer

---

*อัปเดตล่าสุด: มกราคม 2025 | ทีม Platform Engineering & HR*
