from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib, base64, bcrypt
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password utilities ────────────────────────────────────

def hash_password(password: str) -> str:
    prepared_password = _prepare(password).encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared_password, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    prepared_password = _prepare(plain_password).encode('utf-8')
    # Bcrypt stores the salt inside the hash, so we verify against the stored string
    return bcrypt.checkpw(prepared_password, hashed_password.encode('utf-8'))


# ── Token utilities ───────────────────────────────────────
def _prepare(password: str) -> str:
    # Hash and encode to maintain your current database format
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    prepared = base64.b64encode(digest).decode("utf-8")
    return prepared

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_tokens(user_id: int) -> dict:
    return {
        "access_token":  create_access_token({"sub": str(user_id)}),
        "refresh_token": create_refresh_token({"sub": str(user_id)}),
        "token_type":    "bearer",
    }


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
