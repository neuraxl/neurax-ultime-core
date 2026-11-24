from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings


def test_compare_fails_closed_without_a_configured_service_key(monkeypatch):
    monkeypatch.setattr(settings, "unx2_api_key", "")
    with TestClient(app) as client:
        response = client.post("/api/v1/ai/compare", json={"prompt": "Test"})
    assert response.status_code == 503


def test_compare_rejects_a_missing_bearer_token(monkeypatch):
    monkeypatch.setattr(settings, "unx2_api_key", "x" * 48)
    with TestClient(app) as client:
        response = client.post("/api/v1/ai/compare", json={"prompt": "Test"})
    assert response.status_code == 401
