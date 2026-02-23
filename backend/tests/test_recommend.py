from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_recommend_endpoint_returns_products_for_authenticated_user() -> None:
    signup_payload = {"email": "tester@example.com", "password": "Password123!", "full_name": "Test User"}
    client.post("/api/v1/auth/signup", json=signup_payload)

    login_payload = {"email": "tester@example.com", "password": "Password123!"}
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    rec_payload = {"skin_type": "Oily", "conditions": ["Acne"]}
    rec_resp = client.post(
        "/api/v1/recommend",
        json=rec_payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert rec_resp.status_code == 200
    body = rec_resp.json()
    assert "products" in body
    assert len(body["products"]) >= 1
