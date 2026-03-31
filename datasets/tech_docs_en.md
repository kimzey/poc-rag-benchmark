# TechCore Internal API Documentation
## RAG Service API — v1.0.0

Base URL: `https://api.techcore.internal/rag/v1`

---

## Authentication

All API requests must include an `Authorization` header with a valid Bearer token.

```
Authorization: Bearer <your_api_token>
```

### Token Types

| Token Type | Prefix | Scope | Expiry |
|------------|--------|-------|--------|
| Employee Token | `emp_` | Full access (admin + query) | 24 hours |
| Customer Token | `cust_` | Query-only (no admin endpoints) | 1 hour |
| Service Token | `svc_` | Backend-to-backend | 30 days |

Tokens are issued via the Auth Service at `https://auth.techcore.internal/token`.

---

## Rate Limits

| Token Type | Requests/minute | Requests/day |
|------------|----------------|--------------|
| Employee | 100 | 10,000 |
| Customer | 30 | 1,000 |
| Service | 500 | Unlimited |

Rate limit headers returned in every response:
- `X-RateLimit-Limit`: max requests per window
- `X-RateLimit-Remaining`: requests left in current window
- `X-RateLimit-Reset`: Unix timestamp when window resets

When rate limit is exceeded, the API returns `429 Too Many Requests`.

---

## Endpoints

### POST /documents

Upload and index a document.

**Request:**
```json
{
  "content": "string",
  "content_type": "markdown | pdf_text | plain",
  "metadata": {
    "title": "string",
    "tags": ["string"],
    "department": "string",
    "visibility": "employee | customer | public"
  }
}
```

**Response:**
```json
{
  "document_id": "doc_abc123",
  "num_chunks": 42,
  "indexed_at": "2024-01-15T10:30:00Z",
  "status": "indexed"
}
```

**Authorization required:** Employee token with `documents:write` permission.

---

### GET /documents/{document_id}

Retrieve document metadata.

**Response:**
```json
{
  "document_id": "doc_abc123",
  "title": "HR Policy 2024",
  "num_chunks": 42,
  "metadata": {},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### DELETE /documents/{document_id}

Delete a document and all its chunks from the index.

**Authorization required:** Employee token with `documents:delete` permission.

**Response:** `204 No Content`

---

### POST /query

Query the RAG system with a natural language question.

**Request:**
```json
{
  "question": "string",
  "top_k": 3,
  "filters": {
    "department": "engineering",
    "visibility": ["employee", "customer"]
  },
  "language": "th | en | auto",
  "stream": false
}
```

**Response:**
```json
{
  "answer": "string",
  "sources": [
    {
      "document_id": "doc_abc123",
      "chunk_id": "chunk_7",
      "content": "string",
      "score": 0.92,
      "metadata": {}
    }
  ],
  "query_id": "qry_xyz789",
  "latency_ms": 342,
  "model": "anthropic/claude-3-haiku"
}
```

**Streaming:** Set `"stream": true` to receive a Server-Sent Events (SSE) stream.
Each SSE event contains a partial answer token. The final event has `[DONE]`.

---

### GET /query/{query_id}/feedback

Submit quality feedback for a query response.

**Request:**
```json
{
  "rating": 1,
  "comment": "The answer was correct and cited the right policy section."
}
```

`rating` values: `1` (positive), `-1` (negative), `0` (neutral)

---

## Error Codes

| HTTP Status | Error Code | Meaning |
|-------------|------------|---------|
| 400 | `INVALID_REQUEST` | Malformed JSON or missing required fields |
| 401 | `UNAUTHORIZED` | Missing or invalid Bearer token |
| 403 | `FORBIDDEN` | Valid token but insufficient permissions |
| 404 | `NOT_FOUND` | Document or resource not found |
| 413 | `PAYLOAD_TOO_LARGE` | Document content exceeds 10MB limit |
| 422 | `VALIDATION_ERROR` | Request body fails validation schema |
| 429 | `RATE_LIMITED` | Too many requests; see `Retry-After` header |
| 500 | `INTERNAL_ERROR` | Unexpected server error; retry after 30s |
| 503 | `SERVICE_UNAVAILABLE` | LLM provider or vector DB is temporarily down |

---

## Webhook Notifications

Subscribe to document indexing events via webhooks.

**POST /webhooks**
```json
{
  "url": "https://your-service.example.com/webhook",
  "events": ["document.indexed", "document.deleted", "document.failed"],
  "secret": "your_webhook_secret"
}
```

Webhook payloads are signed with HMAC-SHA256 using your `secret`. Verify the
`X-TechCore-Signature` header on your end.

---

## SDKs

| Language | Package | Install |
|----------|---------|---------|
| Python | `techcore-rag` | `pip install techcore-rag` |
| TypeScript | `@techcore/rag` | `npm install @techcore/rag` |
| Go | `github.com/techcore/rag-go` | `go get github.com/techcore/rag-go` |

---

## Changelog

### v1.0.0 (2024-01-15)
- Initial release
- POST /query with streaming support
- POST /documents with metadata filters
- Rate limiting per token type
- Webhook subscriptions

### v0.9.0 (2023-12-01)
- Beta release (internal only)
- Basic query and document endpoints

---

*Internal use only. Do not share outside TechCore.*
