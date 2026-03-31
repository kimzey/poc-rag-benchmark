"""
Phase 4: In-memory stores for PoC.

In production these would be replaced with:
- user_store  → PostgreSQL (users table)
- doc_store   → Vector DB (with access_level metadata filter)
"""
from api.auth.models import User, UserType
from api.auth.jwt_handler import hash_password

# ---------------------------------------------------------------------------
# User store — keyed by user_id
# ---------------------------------------------------------------------------
user_store: dict[str, User] = {
    "u001": User(user_id="u001", username="alice_admin", user_type=UserType.admin),
    "u002": User(user_id="u002", username="bob_employee", user_type=UserType.employee),
    "u003": User(user_id="u003", username="carol_customer", user_type=UserType.customer),
    "u004": User(user_id="u004", username="svc_line_bot", user_type=UserType.service),
}

# Fake password store: username → hashed_password
password_store: dict[str, str] = {
    "alice_admin":    hash_password("admin123"),
    "bob_employee":   hash_password("emp123"),
    "carol_customer": hash_password("cust123"),
    "svc_line_bot":   hash_password("svc123"),
}

# username → user_id lookup
username_to_id: dict[str, str] = {u.username: u.user_id for u in user_store.values()}

# ---------------------------------------------------------------------------
# Document store — simulates vector DB chunks with access_level metadata
# ---------------------------------------------------------------------------
from api.auth.models import AccessLevel
from dataclasses import dataclass, field


@dataclass
class Document:
    doc_id: str
    title: str
    content: str
    access_level: AccessLevel
    embedding: list[float] = field(default_factory=list)  # placeholder


doc_store: list[Document] = [
    Document("d001", "HR Policy TH", "นโยบายการลาพักร้อน...", AccessLevel.internal_kb),
    Document("d002", "Product FAQ", "สินค้ารับประกันกี่ปี...", AccessLevel.customer_kb),
    Document("d003", "Tech Spec Internal", "Architecture ภายใน...", AccessLevel.internal_kb),
    Document("d004", "Executive Salary Band", "เงินเดือนผู้บริหาร...", AccessLevel.confidential_kb),
    Document("d005", "Return Policy", "นโยบายการคืนสินค้า...", AccessLevel.customer_kb),
]
