from fastapi.testclient import TestClient

from app.main import app
from app.security import require_api_key


def test_compare_rejects_missing_credentials():
    app.dependency_overrides[require_api_key] = lambda: None
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/ai/compare", json={"prompt": "Test"})
        assert response.status_code == 503
    finally:
        app.dependency_overrides.clear()
