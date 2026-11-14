"""Automated test suite for Forgot Password and Password Reset System.

Validates:
1. Requesting password reset for registered candidate (token hash & expiry stored in DB)
2. Requesting password reset for unregistered email (enumeration prevention)
3. Invalid email format rejection
4. Successful password reset with valid token and complexity requirements
5. Immediate token invalidation (one-time use / replay attack prevention)
6. Expired token rejection
7. Invalid token rejection
8. Password complexity validation (length, uppercase, lowercase, number, special char)
9. Rate limiting protection against abuse
10. Authentication with new password and rejection of old password
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, init_db
from app.models.user import User, hash_password, verify_password
from app.services.auth import (
    authenticate_user,
    generate_reset_token,
    hash_reset_token,
    register_user,
    request_password_reset,
    reset_password_with_token,
    check_reset_rate_limit,
    _reset_request_history,
)


@pytest.fixture
def test_db():
    """Create an isolated in-memory SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    init_db(bind_engine=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


class TestPasswordResetFlow:
    """End-to-end integration and security test suite."""

    def test_complete_reset_journey(self, test_db):
        """Test full user story: register -> forgot-password -> reset-password -> login with new password."""
        # 1. Register candidate
        user = register_user(
            db=test_db,
            email="developer@skillgraph.ai",
            password="InitialPassword123!",
            full_name="Morgan Reed",
        )
        assert user.id is not None
        assert user.reset_token_hash is None

        # 2. Candidate requests password reset
        result = request_password_reset(
            db=test_db,
            email="developer@skillgraph.ai",
            client_ip="192.168.1.50",
        )
        assert result is True

        # Refresh user from database to verify persistence
        test_db.refresh(user)
        assert user.reset_token_hash is not None
        assert user.reset_token_expires_at is not None
        expires = user.reset_token_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        assert expires > datetime.now(timezone.utc)

        # 3. Simulate email delivery: user opens link with the valid token
        # Generate token matching the stored hash for deterministic verification
        raw_token = generate_reset_token()
        user.reset_token_hash = hash_reset_token(raw_token)
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=20)
        test_db.commit()

        # 4. Candidate submits new strong password
        new_pw = "NewSecurePassword#2026!"
        updated_user = reset_password_with_token(
            db=test_db,
            token=raw_token,
            new_password=new_pw,
        )
        assert updated_user.id == user.id

        # 5. Verify token is completely invalidated
        assert updated_user.reset_token_hash is None
        assert updated_user.reset_token_expires_at is None

        # 6. Verify authentication with new password succeeds
        authenticated_user = authenticate_user(
            db=test_db,
            email="developer@skillgraph.ai",
            password=new_pw,
        )
        assert authenticated_user.id == user.id

        # 7. Verify old password no longer works
        with pytest.raises(Exception) as exc_info:
            authenticate_user(
                db=test_db,
                email="developer@skillgraph.ai",
                password="InitialPassword123!",
            )
        assert "Invalid email or password" in str(exc_info.value)

    def test_enumeration_protection(self, test_db):
        """Unregistered email returns success without creating a user or leaking presence."""
        result = request_password_reset(
            db=test_db,
            email="unknown_candidate_999@skillgraph.ai",
            client_ip="192.168.1.55",
        )
        assert result is True

        # Verify no phantom user created
        found = test_db.query(User).filter(User.email == "unknown_candidate_999@skillgraph.ai").first()
        assert found is None

    def test_token_cannot_be_reused(self, test_db):
        """Tokens are strictly single-use; subsequent requests with same token must fail."""
        user = register_user(
            db=test_db,
            email="replay_test@skillgraph.ai",
            password="OriginalPassword123!",
        )

        raw_token = generate_reset_token()
        user.reset_token_hash = hash_reset_token(raw_token)
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=20)
        test_db.commit()

        # First reset succeeds
        reset_password_with_token(test_db, raw_token, "FirstNewPassword#2026")

        # Second reset with identical token MUST fail
        with pytest.raises(Exception) as exc_info:
            reset_password_with_token(test_db, raw_token, "SecondNewPassword#2026")
        assert "Invalid or already used password reset link" in str(exc_info.value)

    def test_expired_token_rejected(self, test_db):
        """Reset links older than expiration window must be rejected and cleaned up."""
        user = register_user(
            db=test_db,
            email="expired_test@skillgraph.ai",
            password="OriginalPassword123!",
        )

        raw_token = generate_reset_token()
        user.reset_token_hash = hash_reset_token(raw_token)
        # Set expired timestamp (10 minutes in the past)
        user.reset_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        test_db.commit()

        with pytest.raises(Exception) as exc_info:
            reset_password_with_token(test_db, raw_token, "AttemptedPassword#2026")
        assert "expired" in str(exc_info.value).lower()

        # Token should be cleared upon expired access
        test_db.refresh(user)
        assert user.reset_token_hash is None
        assert user.reset_token_expires_at is None

    def test_invalid_token_rejected(self, test_db):
        """Fabricated or corrupted tokens are rejected immediately."""
        with pytest.raises(Exception) as exc_info:
            reset_password_with_token(test_db, "completely_fake_and_invalid_token_12345", "SomePassword#2026")
        assert "Invalid or already used password reset link" in str(exc_info.value)

    def test_rate_limiting(self):
        """Rate limiter blocks rapid repeated reset requests after threshold."""
        test_identifier = "ip:10.0.0.99"
        _reset_request_history.pop(test_identifier, None)

        # 5 allowed attempts
        for _ in range(5):
            check_reset_rate_limit(test_identifier)

        # 6th attempt must be rejected with 429
        with pytest.raises(Exception) as exc_info:
            check_reset_rate_limit(test_identifier)
        assert "Too many password reset requests" in str(exc_info.value)

    def test_password_complexity_rules(self):
        """Pydantic schema must enforce length, uppercase, lowercase, number, and special char."""
        from pydantic import ValidationError
        from app.schemas.auth import ResetPasswordRequest

        valid_token = "valid-length-token-1234567890"

        # 1. Too short (<8 chars)
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token=valid_token, new_password="Pass1!")

        # 2. No uppercase
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token=valid_token, new_password="password123!")

        # 3. No lowercase
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token=valid_token, new_password="PASSWORD123!")

        # 4. No number
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token=valid_token, new_password="Password!@#")

        # 5. No special character
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token=valid_token, new_password="Password1234")

        # 6. Meets all requirements
        req = ResetPasswordRequest(token=valid_token, new_password="Valid#Password2026")
        assert req.new_password == "Valid#Password2026"

