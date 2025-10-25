# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from passlib.context import CryptContext
from jose import jwt, JWTError

# ---- Crypt / Hashing ----
# Use bcrypt_sha256 to avoid bcrypt's 72-byte truncation issue.
# If you need to verify old bcrypt-only hashes, include "bcrypt" second:
# pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password for storing in DB.
    bcrypt_sha256 avoids the 72-byte limit of plain bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ---- JWT / Tokens ----
# IMPORTANT: Keep SECRET_KEY the same as used elsewhere in your project.
# If you are replacing this file in an existing deployment, copy the SECRET_KEY from env/config.
SECRET_KEY = "CHANGE_ME_TO_REAL_SECRET"  # <-- replace with your real secret (or import from settings)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.
    `data` is typically {"sub": user_id, ...}
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT access token and return payload.
    Raises JWTError on invalid/expired token (caller can handle).
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        # Re-raise so callers (dependencies) can convert to HTTPException appropriately
        raise


# Optional helper that returns subject (user id) or None (not required, but often handy)
def get_token_subject(token: str) -> Optional[str]:
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except JWTError:
        return None
