"""
Phase 4: JWT Handler — encode / decode tokens
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from api.config import settings
from api.auth.models import TokenData, UserType

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, username: str, user_type: UserType,
                        expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": user_id,
        "username": username,
        "user_type": user_type.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> TokenData:
    """Decode JWT and return TokenData. Raises JWTError on failure."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    user_id: str = payload.get("sub")
    username: str = payload.get("username")
    user_type_str: str = payload.get("user_type")
    if not user_id or not username or not user_type_str:
        raise JWTError("Invalid token payload")
    return TokenData(
        user_id=user_id,
        username=username,
        user_type=UserType(user_type_str),
    )
