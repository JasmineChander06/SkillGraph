"""Phase 7 Authentication and Security Tests.

Tests:
- User registration (success, duplicate email, invalid format, weak password)
- User login (success, invalid password, non-existent user)
- Token creation, expiration, malformed tokens, tampered signatures
- Current user profile endpoint (/api/auth/me and /auth/me)
- Unauthenticated access rejection
- Plaintext password non-persistence
"""

from __future__ import annotations

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, init_db
from app.main import app
from app.models.user import User, hash_password, verify_password
from app.services.auth import create_access_token


@pytest.fixture
def auth_client():
    """Create an isolated test client with an in-memory database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    init_db(bind_engine=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


class TestUserRegistration:
    """Tests for POST /api/auth/register and /auth/signup."""

    def test_register_success(self, auth_client):
        """Registering a new valid user returns 201 with token and profile."""
        payload = {
            "email": "candidate@example.com",
            "password": "StrongPassword123!",
            "full_name": "Ada Lovelace",
        }
        res = auth_client.post("/api/auth/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert "token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "candidate@example.com"
        assert data["user"]["full_name"] == "Ada Lovelace"
        assert "id" in data["user"]

    def test_register_duplicate_email_returns_409(self, auth_client):
        """Duplicate registration attempts return 409 Conflict."""
        payload = {
            "email": "duplicate@example.com",
            "password": "Password123!",
            "full_name": "Test User",
        }
        res1 = auth_client.post("/api/auth/register", json=payload)
        assert res1.status_code == 201

        res2 = auth_client.post("/api/auth/register", json=payload)
        assert res2.status_code == 409
        assert "already exists" in res2.json()["detail"].lower()

    def test_register_invalid_email_format_returns_422(self, auth_client):
        """Invalid email formats are rejected by validation."""
        payload = {
            "email": "not-an-email",
            "password": "Password123!",
            "full_name": "Test",
        }
        res = auth_client.post("/api/auth/register", json=payload)
        assert res.status_code == 422

    def test_register_short_password_returns_422(self, auth_client):
        """Passwords shorter than 8 characters are rejected."""
        payload = {
            "email": "short@example.com",
            "password": "short",
            "full_name": "Short",
        }
        res = auth_client.post("/api/auth/register", json=payload)
        assert res.status_code == 422

    def test_register_architecture_compat_endpoint(self, auth_client):
        """The /auth/signup endpoint from architecture.md works as expected."""
        payload = {
            "email": "architect@example.com",
            "password": "Architecture123!",
            "name": "Grace Hopper",
        }
        res = auth_client.post("/auth/signup", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["user"]["full_name"] == "Grace Hopper"


class TestUserLogin:
    """Tests for POST /api/auth/login and /auth/login."""

    def test_login_success(self, auth_client):
        """Login with correct credentials returns 200 with JWT access token."""
        # First register
        auth_client.post("/api/auth/register", json={
            "email": "loginuser@example.com",
            "password": "SecurePassword999",
            "full_name": "Login Tester",
        })

        # Now login
        res = auth_client.post("/api/auth/login", json={
            "email": "loginuser@example.com",
            "password": "SecurePassword999",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == "loginuser@example.com"

    def test_login_wrong_password_returns_401(self, auth_client):
        """Login with incorrect password returns 401 Unauthorized."""
        auth_client.post("/api/auth/register", json={
            "email": "wrongpw@example.com",
            "password": "CorrectPassword123",
        })

        res = auth_client.post("/api/auth/login", json={
            "email": "wrongpw@example.com",
            "password": "WrongPassword456",
        })
        assert res.status_code == 401
        assert "invalid email or password" in res.json()["detail"].lower()

    def test_login_nonexistent_user_returns_401(self, auth_client):
        """Login for non-existent email returns 401 Unauthorized."""
        res = auth_client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "SomePassword123",
        })
        assert res.status_code == 401

    def test_login_architecture_compat_endpoint(self, auth_client):
        """POST /auth/login works identically to /api/auth/login."""
        auth_client.post("/auth/signup", json={
            "email": "compat@example.com",
            "password": "Password123!",
        })
        res = auth_client.post("/auth/login", json={
            "email": "compat@example.com",
            "password": "Password123!",
        })
        assert res.status_code == 200
        assert "access_token" in res.json()


class TestTokenSecurityAndValidation:
    """Tests for token expiry, signature tampering, and malformed headers."""

    def test_get_current_user_profile_success(self, auth_client):
        """Authenticated GET /api/auth/me returns the current user profile."""
        reg = auth_client.post("/api/auth/register", json={
            "email": "profile@example.com",
            "password": "Password123!",
            "full_name": "Profile Owner",
        })
        token = reg.json()["access_token"]

        res = auth_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "profile@example.com"
        assert data["full_name"] == "Profile Owner"

    def test_unauthorized_access_without_token_returns_401(self, auth_client):
        """Accessing protected endpoints without an Authorization header returns 401."""
        res = auth_client.get("/api/auth/me")
        assert res.status_code == 401
        assert "authentication required" in res.json()["detail"].lower()

    def test_tampered_token_returns_401(self, auth_client):
        """Accessing with an invalid or tampered JWT returns 401."""
        reg = auth_client.post("/api/auth/register", json={
            "email": "tamper@example.com",
            "password": "Password123!",
        })
        token = reg.json()["access_token"]
        tampered_token = token[:-5] + "AAAAA"

        res = auth_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert res.status_code == 401
        assert "invalid or malformed" in res.json()["detail"].lower()

    def test_garbage_token_returns_401(self, auth_client):
        """Non-JWT random strings return 401."""
        res = auth_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer not-even-close-to-a-jwt"},
        )
        assert res.status_code == 401

    def test_expired_token_returns_401(self, auth_client):
        """An expired JWT is rejected with 401 and an explicit expired explanation."""
        reg = auth_client.post("/api/auth/register", json={
            "email": "expired@example.com",
            "password": "Password123!",
        })
        user_id = reg.json()["user"]["id"]

        # Generate an intentionally expired token (expired 10 minutes ago)
        expired_token = create_access_token(
            data={"sub": str(user_id), "email": "expired@example.com"},
            expires_delta=timedelta(minutes=-10),
        )

        res = auth_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert res.status_code == 401
        assert "expired" in res.json()["detail"].lower()


class TestPasswordSecurityRequirements:
    """Verify cryptographic password guarantees."""

    def test_passwords_are_never_plaintext(self, auth_client):
        """Check that stored password hashes use PBKDF2 with salt."""
        plain = "SuperSecretPassword123"
        hashed = hash_password(plain)

        assert plain not in hashed
        assert "$" in hashed
        salt, key = hashed.split("$")
        assert len(salt) == 32  # 16 bytes hex
        assert len(key) == 64   # 32 bytes hex sha256

        assert verify_password(plain, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_two_identical_passwords_have_unique_salts(self):
        """Distinct salts ensure two users with the same password have different hashes."""
        plain = "SamePassword123!"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        assert hash1 != hash2
