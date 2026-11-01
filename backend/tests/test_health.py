"""Automated tests for the Health Endpoint and CORS configuration."""

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_health_check_returns_200():
    """Verify that GET /api/health responds with status code 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_check_payload_structure():
    """Verify that the health check payload contains all expected fields."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert data.get("status") == "ok"
    assert data.get("app") == settings.APP_NAME
    assert data.get("version") == settings.APP_VERSION
    assert data.get("environment") == settings.ENVIRONMENT


def test_root_endpoint():
    """Verify that GET / provides a valid greeting and documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data.get("docs_url") == "/docs"
    assert data.get("health_check") == "/api/health"


def test_cors_allowed_origin():
    """Verify that requests from authorized local frontend origins receive CORS headers."""
    allowed_origin = "http://localhost:3000"
    response = client.get(
        "/api/health",
        headers={"Origin": allowed_origin},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallowed_origin():
    """Verify that requests from unauthorized origins do not receive allow-origin header."""
    unauthorized_origin = "http://unauthorized-external-site.com"
    response = client.get(
        "/api/health",
        headers={"Origin": unauthorized_origin},
    )
    assert response.status_code == 200
    # Starlette CORSMiddleware omits access-control-allow-origin for unauthorized origins
    assert response.headers.get("access-control-allow-origin") != unauthorized_origin

