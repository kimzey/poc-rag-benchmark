"""
Phase 4: FastAPI auth dependencies — get_current_user, require_permission

Usage:
    @router.post("/chat")
    async def chat(
        user: User = Depends(get_current_user),
        _: None = Depends(require_permission(Permission.chat_query)),
    ):
        ...
"""
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from api.auth.jwt_handler import decode_access_token
from api.auth.models import Permission, User, ROLE_PERMISSIONS
from api.store import user_store  # in-memory user store for PoC

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    token = credentials.credentials
    try:
        token_data = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_store.get(token_data.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_permission(permission: Permission) -> Callable:
    """Factory: returns a dependency that checks a specific permission."""
    async def _check(user: User = Depends(get_current_user)) -> User:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return user
    return _check
