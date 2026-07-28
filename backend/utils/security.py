import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# bcrypt has a hard limit of 72 bytes for the password after UTF-8 encoding
MAX_BCRYPT_PASSWORD_BYTES = 72


def _password_to_bytes(password: str) -> bytes:
    b = password.encode("utf-8")
    if len(b) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError(
            f"Password too long for bcrypt (max {MAX_BCRYPT_PASSWORD_BYTES} bytes after UTF-8 encoding)"
        )
    return b


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Raises ValueError when the UTF-8 encoded password exceeds bcrypt's 72-byte limit.
    """
    pw = _password_to_bytes(password)
    hashed = bcrypt.hashpw(pw, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against a stored bcrypt hash.

    Raises ValueError when the UTF-8 encoded password exceeds bcrypt's 72-byte limit.
    Returns True/False for match.
    """
    pw = _password_to_bytes(plain_password)
    # stored hash is a str; bcrypt expects bytes
    return bcrypt.checkpw(pw, hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
