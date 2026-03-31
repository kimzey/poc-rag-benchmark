"""
Phase 4: Auth routes — login, token refresh
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.auth.jwt_handler import create_access_token, verify_password
from api.auth.models import Token
from api.store import password_store, username_to_id, user_store

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/token", response_model=Token, summary="Login and get JWT")
async def login(body: LoginRequest) -> Token:
    hashed = password_store.get(body.username)
    if not hashed or not verify_password(body.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    user_id = username_to_id[body.username]
    user = user_store[user_id]
    token = create_access_token(user.user_id, user.username, user.user_type)
    return Token(access_token=token)
