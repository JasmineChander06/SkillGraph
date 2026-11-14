"""Authentication, JWT token lifecycle, and current-user dependency services."""

from __future__ import annotations

import hashlib
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User, hash_password, verify_password
from app.services.email import send_password_reset_email

logger = logging.getLogger("skillgraph.services.auth")

# In-memory sliding window rate limiter tracking
_reset_request_history: Dict[str, list[float]] = {}

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


def check_reset_rate_limit(identifier: str) -> None:
    """Sliding-window rate limiter for password reset requests to mitigate abuse and harassment."""
    now = time.time()
    window = settings.RESET_RATE_LIMIT_WINDOW_SECONDS
    max_attempts = settings.RESET_RATE_LIMIT_MAX_ATTEMPTS

    history = _reset_request_history.get(identifier, [])
    valid_history = [t for t in history if now - t < window]

    if len(valid_history) >= max_attempts:
        retry_after = int(window - (now - valid_history[0]))
        logger.warning("Password reset rate limit exceeded for %s. Retry after %ds", identifier, retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many password reset requests. Please wait {max(1, retry_after // 60)} minute(s) before trying again.",
            headers={"Retry-After": str(max(1, retry_after))},
        )

    valid_history.append(now)
    _reset_request_history[identifier] = valid_history


def hash_reset_token(raw_token: str) -> str:
    """Compute deterministic SHA-256 hash of a reset token for database persistence."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def generate_reset_token() -> str:
    """Generate a high-entropy cryptographically random URL-safe token."""
    return secrets.token_urlsafe(32)


def request_password_reset(
    db: Session,
    email: str,
    client_ip: str = "unknown",
) -> bool:
    """Initiate password recovery for a candidate email with rate limiting and constant-time response."""
    normalized_email = email.strip().lower()

    # Rate limit by both client IP and email
    check_reset_rate_limit(f"ip:{client_ip}")
    check_reset_rate_limit(f"email:{normalized_email}")

    user = db.query(User).filter(User.email == normalized_email).first()
    if user and user.is_active:
        raw_token = generate_reset_token()
        token_hash = hash_reset_token(raw_token)
        now_utc = datetime.now(timezone.utc)
        expires_at = now_utc + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

        user.reset_token_hash = token_hash
        user.reset_token_expires_at = expires_at
        db.commit()

        # Dispatch reset email via SMTP
        send_password_reset_email(
            to_email=user.email,
            recipient_name=user.full_name,
            reset_token=raw_token,
        )
    else:
        # Constant-time mitigation against timing side-channel attacks
        hash_password("dummy-timing-mitigation-password")
        logger.info("Password reset requested for non-existent or inactive email: %s", normalized_email)

    return True


def reset_password_with_token(
    db: Session,
    token: str,
    new_password: str,
) -> User:
    """Verify reset token, validate expiration, hash new password, and invalidate token."""
    token_hash = hash_reset_token(token)
    user = db.query(User).filter(User.reset_token_hash == token_hash).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used password reset link. Please request a new one.",
        )

    now_utc = datetime.now(timezone.utc)
    expires_at = user.reset_token_expires_at

    if expires_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset link.",
        )

    # Standardize timezone for comparison across SQLite naive and postgres aware timestamps
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now_utc:
        # Clean up expired token
        user.reset_token_hash = None
        user.reset_token_expires_at = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset link has expired. Please request a new one.",
        )

    # Update password with standard PBKDF2 salted hash
    user.hashed_password = hash_password(new_password)
    # Immediately invalidate reset token (single-use enforcement)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.commit()
    db.refresh(user)

    logger.info("Successfully updated password for User ID %s via reset token", user.id)
    return user


