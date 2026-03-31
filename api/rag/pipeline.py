"""
Phase 4: RAG Pipeline

Wires together: retrieve → prompt → LLM call

Uses OpenRouter (OpenAI-compatible) from Phase 3.5.
Falls back to a mock response if no API key is configured.
"""
from openai import AsyncOpenAI

from api.auth.models import User
from api.config import settings
from api.rag.models import ChatRequest, ChatResponse, RetrievedChunk
from api.rag.retrieval import retrieve


def _build_system_prompt(chunks: list[RetrievedChunk]) -> str:
    context = "\n\n".join(
        f"[{c.title}]\n{c.content}" for c in chunks
    )
    return (
        "You are a helpful assistant. Answer the user's question using ONLY "
        "the context below. If the answer is not in the context, say you don't know.\n\n"
        f"Context:\n{context}"
    )


async def run_rag(request: ChatRequest, user: User) -> ChatResponse:
    # 1. Retrieve — permission-filtered
    query = request.messages[-1].content
    chunks = retrieve(query, user, top_k=request.top_k)

    # 2. Build messages for LLM
    system_msg = _build_system_prompt(chunks)
    messages = [{"role": "system", "content": system_msg}] + [
        {"role": m.role, "content": m.content} for m in request.messages
    ]

    # 3. Call LLM (OpenRouter, OpenAI-compatible)
    if not settings.openrouter_api_key:
        # Mock response for PoC demo without API key
        answer = (
            f"[MOCK — no API key] Retrieved {len(chunks)} chunk(s) for user "
            f"'{user.username}' ({user.user_type.value}): "
            + " | ".join(c.title for c in chunks)
        )
        return ChatResponse(answer=answer, retrieved_chunks=chunks, model="mock")

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    completion = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=messages,
    )
    answer = completion.choices[0].message.content
    usage = {
        "prompt_tokens": completion.usage.prompt_tokens,
        "completion_tokens": completion.usage.completion_tokens,
    } if completion.usage else None

    return ChatResponse(
        answer=answer,
        retrieved_chunks=chunks,
        model=settings.openrouter_model,
        usage=usage,
    )
