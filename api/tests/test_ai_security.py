from fastapi.testclient import TestClient

from app.main import app


def test_compare_requires_a_configured_server_key():
    with TestClient(app) as client:
        response = client.post("/api/v1/ai/compare", json={"prompt": "Test"})
    assert response.status_code == 503
