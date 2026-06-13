"""JWT-based authentication helpers for the User Management API.

Provides helpers to generate token payloads, verify signature expirations,
and validate Bearer header dependencies.
"""

import os
import jwt
import datetime
from fastapi import Header, HTTPException
from models import TokenResponse

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

def create_token(user_id: int) -> TokenResponse:
    """Generate a JWT access token for a given user ID with expiry metadata."""
    now = datetime.datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return TokenResponse(
        access_token=token,
        expires_in=TOKEN_EXPIRY_HOURS * 3600
    )

def decode_token(token: str) -> dict:
    """Decode and verify JWT signature and claims, raising ValueError if invalid or expired."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.DecodeError:
        raise ValueError("Invalid token")

def require_auth(authorization: str = Header(None)) -> dict:
    """FastAPI dependency to enforce Bearer token authentication on incoming requests."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        return payload
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
