<!-- Generated: 2026-04-01 | Files scanned: 18 | Token estimate: ~650 -->

# Backend & API Codemap

**Last Updated:** 2026-04-01  
**Phase:** 4 (FastAPI + JWT + RBAC)  
**Entry Points:** `api/main.py` (FastAPI app), `api/auth/dependencies.py` (auth middleware)

## FastAPI Application Structure

```
api/main.py (FastAPI app)
├─ Routes registered:
│  ├─ auth_router (/api/v1/auth)          → api/routes/auth_routes.py
│  ├─ chat_router (/api/v1/chat)          → api/routes/chat.py
│  ├─ documents_router (/api/v1/documents) → api/routes/documents.py
│  ├─ feedback_router (/api/v1/feedback)   → api/routes/feedback.py
│  └─ line_router (/api/v1/webhooks/line)  → api/routes/webhooks/line.py
│
└─ Endpoints:
   ├─ GET  /                                    (root redirect)
   ├─ GET  /api/v1/me                          (current user info + permissions)
   ├─ POST /api/v1/auth/token                  (JWT login)
   ├─ POST /api/v1/chat/completions            (RAG query)
   ├─ POST /api/v1/documents/upload            (upload doc)
   ├─ GET  /api/v1/documents/search            (search visible docs)
   ├─ POST /api/v1/documents/index             (trigger indexing)
   ├─ GET  /api/v1/documents/collections       (list collections)
   ├─ POST /api/v1/feedback                    (rate RAG response)
   └─ POST /api/v1/webhooks/line               (LINE adapter)
```

## Authentication & Authorization

### Auth Models (`api/auth/models.py`)

| Type | Enum | Permissions | Visible Access Levels |
|------|------|-------------|----------------------|
| **admin** | `UserType.admin` | All 8 | customer_kb + internal_kb + confidential_kb |
| **employee** | `UserType.employee` | doc:{read,upload,delete,index}, chat:query, analytics:read | customer_kb + internal_kb |
| **customer** | `UserType.customer` | doc:read, chat:query | customer_kb only |
| **service** | `UserType.service` | doc:read, chat:query | customer_kb + internal_kb |

**Test Users:**
```
alice_admin      / admin123        → admin
bob_employee     / emp123          → employee
carol_customer   / cust123         → customer
svc_line_bot     / svc123          → service (LINE adapter)
```

### Auth Middleware (`api/auth/dependencies.py`)

```python
# Dependency chain:
@router.post("/chat")
async def chat_completions(
    body: ChatRequest,
    user: User = Depends(require_permission(Permission.chat_query))
) → ChatResponse

# Execution flow:
1. bearer_scheme extracts "Bearer <token>" from Authorization header
2. decode_access_token(token) → TokenData
3. user_store.get(token_data.user_id) → User (or 401)
4. has_permission(permission) check → 403 if denied
5. route handler executes with authenticated + authorized user
```

### JWT Handler (`api/auth/jwt_handler.py`)

- `encode_access_token(user: User) → str` — Sign token with SECRET_KEY
- `decode_access_token(token: str) → TokenData` — Verify signature + parse claims
- `hash_password(pwd) → str` — bcrypt hash
- `verify_password(pwd, hashed) → bool` — bcrypt verify

## RAG Pipeline

### Request/Response Models (`api/rag/models.py`)

```python
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    top_k: int = 3
    collection: str | None = None

class RetrievedChunk(BaseModel):
    doc_id: str
    title: str
    content: str
    access_level: str  # customer_kb, internal_kb, confidential_kb
    score: float

class ChatResponse(BaseModel):
    answer: str
    retrieved_chunks: list[RetrievedChunk]
    model: str
    usage: dict | None  # {"prompt_tokens": int, "completion_tokens": int}
```

### Pipeline Orchestration (`api/rag/pipeline.py`)

```python
async def run_rag(request: ChatRequest, user: User) → ChatResponse:
    # 1. Retrieve — permission-filtered (calls retrieval.py)
    query = request.messages[-1].content
    chunks = retrieve(query, user, top_k=request.top_k)

    # 2. Build system prompt from retrieved chunks
    system_msg = _build_system_prompt(chunks)
    messages = [{"role": "system", "content": system_msg}] + messages_list

    # 3. Call LLM via OpenRouter (OpenAI-compatible)
    if not settings.openrouter_api_key:
        return ChatResponse(answer="[MOCK]", ...)  # Demo mode

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    completion = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=messages,
    )
    return ChatResponse(answer=completion.choices[0].message.content, ...)
```

### Permission-Filtered Retrieval (`api/rag/retrieval.py`)

```python
def _vector_search(
    query: str,
    allowed_levels: Set[AccessLevel],
    top_k: int
) → list[Document]:
    """
    1. Filter doc_store by access_level (BEFORE scoring)
    2. Simulate similarity (hash-based for reproducibility)
    3. Sort by score descending, return top_k
    
    Production: Replace with real VectorDB:
      qdrant_client.search(
          collection_name=...,
          query_vector=embed(query),
          query_filter=Filter(must=[FieldCondition(
              key="access_level",
              match=MatchAny(any=[lvl.value for lvl in allowed_levels])
          )]),
          limit=top_k,
      )
    """

def retrieve(
    query: str,
    user: User,
    top_k: int = 3
) → list[RetrievedChunk]:
    # Calls _vector_search() with user.allowed_access_levels
    # Returns RetrievedChunk objects (ready for chat response)
```

## Document Store (`api/store.py`)

```python
@dataclass
class Document:
    doc_id: str
    title: str
    content: str
    access_level: AccessLevel  # metadata for retrieval filter

user_store: Dict[user_id, User] = {
    "alice": User(..., user_type=UserType.admin),
    "bob": User(..., user_type=UserType.employee),
    ...
}

password_store: Dict[username, hashed_pwd] = {...}

doc_store: List[Document] = [
    Document(doc_id="1", title="...", access_level=AccessLevel.customer_kb),
    ...
]
```

## Error Handling

| Error | Condition | Response |
|-------|-----------|----------|
| 401 Unauthorized | Invalid/expired token | `{"detail": "Invalid or expired token"}` |
| 403 Forbidden | Missing permission | `{"detail": "Permission 'chat:query' required"}` |
| 503 Service Unavailable | LLM timeout/connection error | `{"detail": "LLM service unavailable: ..."}` |

## Configuration (`api/config.py`)

```python
class Settings(BaseSettings):
    app_name: str = "RAG API"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    jwt_secret_key: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    # ... load from .env
```

## Related Codemaps

- **[architecture.md](architecture.md)** — Overall 6-phase structure
- **[tui.md](tui.md)** — TUI client that calls this API
- **[dependencies.md](dependencies.md)** — External services (OpenRouter)
