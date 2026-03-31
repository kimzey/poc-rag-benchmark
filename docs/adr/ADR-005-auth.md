# ADR-005: Authentication & Authorization Approach

| ฟิลด์ | ค่า |
|------|-----|
| **ID** | ADR-005 |
| **สถานะ** | 🟡 Draft |
| **วันที่** | 2026-03-31 |
| **Deciders** | Engineering Team, พี่ตั๊ก |
| **Phase** | Phase 4 |

---

## บริบท (Context)

ระบบ RAG ต้องรองรับ **multi-tenant access control** ที่แยก Employee กับ Customer ออกจากกัน และสำคัญมากคือต้องมี **document-level permission filtering** ที่ retrieval step ไม่ใช่แค่ที่ API layer

**User types:**
- **Employee** — เข้าถึง internal + customer knowledge base
- **Customer** — เข้าถึงเฉพาะ customer-facing knowledge base
- **Admin** — จัดการทุกอย่าง
- **Service (Bot)** — API keys สำหรับ LINE bot, Discord bot ฯลฯ

**Options ที่พิจารณา:**
1. JWT + RBAC (PoC ใช้แบบนี้)
2. JWT + ABAC
3. OAuth 2.0 + OIDC (SSO)
4. Keycloak (self-hosted IdP)
5. Auth0 (managed)

---

## Decision

> **[TODO หลัง Phase 4 PoC + team discussion]**
>
> Short-term (Production v1): _______________  
> Long-term (เมื่อต้องการ SSO / corporate IdP): _______________

**PoC ใช้:** JWT + RBAC พร้อม permission-filtered retrieval — ผลการทดสอบในเอกสาร [phase-4-api-auth.md](../phases/phase-4-api-auth.md)

---

## เหตุผล (Rationale)

**Comparison:**

| Strategy | Complexity | Flexibility | SSO Support | Vendor Lock-in | Verdict |
|----------|-----------|-------------|-------------|----------------|---------|
| JWT + RBAC | ต่ำ | ปานกลาง | ❌ | ไม่มี | ✅ PoC / v1 |
| JWT + ABAC | กลาง | สูง | ❌ | ไม่มี | พิจารณา v2 |
| OAuth2 + OIDC | สูง | สูง | ✅ | ต่ำ | Production |
| Keycloak | สูงมาก | สูงมาก | ✅ | ไม่มี (OSS) | ถ้าต้องการ on-prem |
| Auth0 | ต่ำ | สูง | ✅ | สูง | ถ้า simplicity สำคัญกว่า |

**Document-level access control:**

PoC พิสูจน์ว่า permission filter ที่ retrieval step ทำงานได้:
```python
vector_search(query, filter={"access_level": {"$in": user.allowed_access_levels}})
```
- Customer ไม่เห็น internal docs แม้พยายาม bypass API
- Employee เห็นทั้ง internal + customer docs

> [TODO] ยืนยันผลจาก Scenario 2 integration test

---

## ผลที่ตามมา (Consequences)

**ข้อดี:**
- [TODO]

**ข้อเสีย / Trade-offs:**
- RBAC อาจไม่พอถ้า permission granularity ซับซ้อนขึ้นในอนาคต → ต้องมีแผน migrate to ABAC
- ถ้าเลือก JWT custom → ต้องจัดการ token revocation, refresh tokens เอง

**สิ่งที่ต้องทำสำหรับ Production:**
- [ ] ตัดสินใจ production IdP (Keycloak / Auth0 / custom)
- [ ] Design token refresh strategy
- [ ] Design token revocation (logout, account deactivation)
- [ ] Rate limiting per user type
- [ ] Audit logging สำหรับ compliance

---

## Migration Path

> ถ้าเริ่มด้วย JWT + RBAC แล้วต้องการ SSO:
> - เพิ่ม OAuth2 layer ด้านหน้า — JWT format ยังเหมือนเดิม
> - Application code ไม่ต้องเปลี่ยน เพราะใช้ `get_current_user` dependency

---

## ข้อมูลที่ใช้ตัดสินใจ

- PoC implementation: `api/auth/`
- Integration test Scenario 2 results
- Phase 4 notes: `docs/phases/phase-4-api-auth.md`
