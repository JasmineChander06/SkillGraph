"""Authentication, JWT token lifecycle, and current-user dependency services."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User, hash_password, verify_password

logger = logging.getLogger("skillgraph.services.auth")

# Security Bearer schemes
security_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed HMAC-SHA256 JWT access token with an explicit expiration timestamp."""
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": int(now_utc.timestamp()),
        "exp": int(expire.timestamp()),
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT access token.

    Raises:
        HTTPException 401 if expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        logger.warning("Rejected expired authentication token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"Token expired\""},
        ) from exc
    except jwt.InvalidTokenError as exc:
        logger.warning("Rejected malformed or invalid authentication token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed authentication token.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
        ) from exc


def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to extract and verify the authenticated User entity from Bearer token.

    Enforces that the request provides a valid, unexpired token belonging to an active user.
    """
    if not auth_credentials or not auth_credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth_credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing user subject identification.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user subject in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


def get_optional_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """FastAPI dependency to extract the authenticated User if token is present, or return None."""
    if not auth_credentials or not auth_credentials.credentials:
        return None

    try:
        payload = decode_access_token(auth_credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        user_id_int = int(user_id)
        user = db.query(User).filter(User.id == user_id_int, User.is_active == True).first()
        return user
    except Exception:
        # Invalid or expired token for optional auth is treated as anonymous
        return None


def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: Optional[str] = None,
) -> User:
    """Create a new user with securely hashed password."""
    normalized_email = email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{normalized_email}' already exists.",
        )

    hashed_pw = hash_password(password)
    user = User(
        email=normalized_email,
        hashed_password=hashed_pw,
        full_name=full_name.strip() if full_name else None,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    """Verify user credentials and return the active User record.

    Raises:
        HTTPException 401 if credentials are invalid.
    """
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    return user

