from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_recommend_endpoint_returns_products() -> None:
    payload = {"skin_type": "Oily", "conditions": ["Acne"]}
    resp = client.post("/api/v1/recommend", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "products" in body
    assert len(body["products"]) >= 1
