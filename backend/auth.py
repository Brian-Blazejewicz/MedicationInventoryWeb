
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    user_id: int,
) -> str:
    """Create a signed JWT access token."""

    expiration = (
        datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_access_token(token: str) -> int:
    """Verify a JWT and return its user ID."""

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "exp"]},
    )

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.isdecimal():
        raise ValueError("Invalid token subject")

    return int(subject)
