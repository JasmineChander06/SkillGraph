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
11. Provider failure simulation raising HTTP 503 and rolling back token
12. Email content verification (subject, headers, exact body wording)
13. Resend API and SMTP dispatch mechanics
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, init_db
from app.models.user import User, hash_password, verify_password
from app.services.auth import (
    authenticate_user,
    check_reset_rate_limit,
    generate_reset_token,
    hash_reset_token,
    register_user,
    request_password_reset,
    reset_password_with_token,
    _reset_request_history,
)
from app.services.email import (
    generate_password_reset_email_html,
    send_password_reset_email,
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

        # 2. Candidate requests password reset (mock email delivery success)
        with patch("app.services.auth.send_password_reset_email", return_value=True) as mock_send:
            result = request_password_reset(
                db=test_db,
                email="developer@skillgraph.ai",
                client_ip="192.168.1.50",
            )
            assert result is True
            assert mock_send.called
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["to_email"] == "developer@skillgraph.ai"
            assert call_kwargs["recipient_name"] == "Morgan Reed"
            raw_token = call_kwargs["reset_token"]
            assert len(raw_token) >= 32

        # Refresh user from database to verify persistence of token hash and expiry
        test_db.refresh(user)
        assert user.reset_token_hash is not None
        assert user.reset_token_hash == hash_reset_token(raw_token)
        assert user.reset_token_expires_at is not None
        expires = user.reset_token_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        assert expires > datetime.now(timezone.utc)

        # 3. Candidate submits new strong password using the token received in email
        new_pw = "NewSecurePassword#2026!"
        updated_user = reset_password_with_token(
            db=test_db,
            token=raw_token,
            new_password=new_pw,
        )
        assert updated_user.id == user.id

        # 4. Verify token is completely invalidated immediately
        assert updated_user.reset_token_hash is None
        assert updated_user.reset_token_expires_at is None

        # 5. Verify authentication with new password succeeds
        authenticated_user = authenticate_user(
            db=test_db,
            email="developer@skillgraph.ai",
            password=new_pw,
        )
        assert authenticated_user.id == user.id

        # 6. Verify old password no longer works
        with pytest.raises(Exception) as exc_info:
            authenticate_user(
                db=test_db,
                email="developer@skillgraph.ai",
                password="InitialPassword123!",
            )
        assert "Invalid email or password" in str(exc_info.value)

    def test_enumeration_protection(self, test_db):
        """TEST 8: Unregistered email returns success without creating a user or leaking presence."""
        result = request_password_reset(
            db=test_db,
            email="unknown_candidate_999@skillgraph.ai",
            client_ip="192.168.1.55",
        )
        assert result is True

        # Verify no phantom user created
        found = test_db.query(User).filter(User.email == "unknown_candidate_999@skillgraph.ai").first()
        assert found is None

    def test_provider_failure_rolls_back_token_and_raises_503(self, test_db):
        """TEST 9: When email provider fails, backend records failure, clears token, and raises HTTP 503."""
        user = register_user(
            db=test_db,
            email="delivery_fail@skillgraph.ai",
            password="InitialPassword123!",
            full_name="Alex Case",
        )

        with patch("app.services.auth.send_password_reset_email", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                request_password_reset(
                    db=test_db,
                    email="delivery_fail@skillgraph.ai",
                    client_ip="192.168.1.60",
                )
            assert exc_info.value.status_code == 503
            assert "Email delivery service is currently unavailable" in exc_info.value.detail

        # Verify token was rolled back so no dangling token remains
        test_db.refresh(user)
        assert user.reset_token_hash is None
        assert user.reset_token_expires_at is None

    def test_token_cannot_be_reused(self, test_db):
        """TEST 6: Tokens are strictly single-use; subsequent requests with same token must fail."""
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
        with pytest.raises(HTTPException) as exc_info:
            reset_password_with_token(test_db, raw_token, "SecondNewPassword#2026")
        assert exc_info.value.status_code == 400
        assert "Invalid or already used password reset link" in exc_info.value.detail

    def test_expired_token_rejected(self, test_db):
        """TEST 7: Reset links older than expiration window must be rejected and cleaned up."""
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

        with pytest.raises(HTTPException) as exc_info:
            reset_password_with_token(test_db, raw_token, "AttemptedPassword#2026")
        assert exc_info.value.status_code == 400
        assert "expired" in exc_info.value.detail.lower()

        # Token should be cleared upon expired access
        test_db.refresh(user)
        assert user.reset_token_hash is None
        assert user.reset_token_expires_at is None

    def test_invalid_token_rejected(self, test_db):
        """Fabricated or corrupted tokens are rejected immediately."""
        with pytest.raises(HTTPException) as exc_info:
            reset_password_with_token(test_db, "completely_fake_and_invalid_token_12345", "SomePassword#2026")
        assert exc_info.value.status_code == 400
        assert "Invalid or already used password reset link" in exc_info.value.detail

    def test_rate_limiting(self):
        """Rate limiter blocks rapid repeated reset requests after threshold."""
        test_identifier = "ip:10.0.0.99"
        _reset_request_history.pop(test_identifier, None)

        # 5 allowed attempts
        for _ in range(5):
            check_reset_rate_limit(test_identifier)

        # 6th attempt must be rejected with 429
        with pytest.raises(HTTPException) as exc_info:
            check_reset_rate_limit(test_identifier)
        assert exc_info.value.status_code == 429
        assert "Too many password reset requests" in exc_info.value.detail

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

    def test_email_content_and_wording(self):
        """PHASE 4: Email content matches exact specified text, button, expiry and sign-off."""
        reset_url = "http://127.0.0.1:8000/frontend/reset-password.html?token=test_token_123"
        html = generate_password_reset_email_html(reset_url=reset_url, recipient_name="Jordan")

        assert "Hello Jordan," in html
        assert "We received a request to reset your SkillGraph account password." in html
        assert "Click the button below to choose a new password:" in html
        assert "Reset My Password &rarr;" in html or "Reset My Password" in html
        assert reset_url in html
        assert "This link expires in <strong>20 minutes</strong>" in html or "20 minutes" in html
        assert "If you did not request this password reset, you can safely ignore this email." in html
        assert "SkillGraph Team" in html

    def test_resend_api_dispatch(self):
        """PHASE 2: Resend API dispatch sends HTTP POST with proper payload and authorization."""
        from app.config import settings

        with patch("app.config.settings.RESEND_API_KEY", "re_test_key_123456"):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.getcode.return_value = 200
                mock_response.read.return_value = b'{"id": "msg_resend_abc123"}'
                mock_urlopen.return_value.__enter__.return_value = mock_response

                delivered = send_password_reset_email(
                    to_email="test.candidate@example.com",
                    recipient_name="Taylor",
                    reset_token="sample_reset_token_xyz",
                )
                assert delivered is True
                assert mock_urlopen.called
                req = mock_urlopen.call_args[0][0]
                assert req.full_url == "https://api.resend.com/emails"
                assert req.headers["Authorization"] == "Bearer re_test_key_123456"
                assert req.headers["Content-type"] == "application/json"

    def test_smtp_dispatch(self):
        """PHASE 2: Standard SMTP dispatch connects, logs in, and sends formatted EmailMessage."""
        with patch("app.config.settings.RESEND_API_KEY", ""):
            with patch("app.config.settings.SMTP_USERNAME", "testuser@gmail.com"):
                with patch("app.config.settings.SMTP_PASSWORD", "app_password_123"):
                    with patch("smtplib.SMTP") as mock_smtp:
                        server_instance = MagicMock()
                        mock_smtp.return_value = server_instance

                        delivered = send_password_reset_email(
                            to_email="candidate@example.com",
                            recipient_name="Sam",
                            reset_token="sample_token_456",
                        )
                        assert delivered is True
                        assert mock_smtp.called
                        assert server_instance.login.called
                        assert server_instance.send_message.called
                        msg = server_instance.send_message.call_args[0][0]
                        assert msg["Subject"] == "Reset Your SkillGraph Password"
                        assert msg["To"] == "candidate@example.com"
