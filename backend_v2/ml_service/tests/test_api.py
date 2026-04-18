from fastapi.testclient import TestClient

from app.main import app


def test_healthz() -> None:
    with TestClient(app) as client:
        resp = client.get("/healthz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "providers" in body


def test_analyze_with_landmarks(synthetic_face_b64, fake_mediapipe_landmarks) -> None:
    with TestClient(app) as client:
        payload = {
            "image_base64": synthetic_face_b64,
            "landmarks": fake_mediapipe_landmarks,
            "questionnaire": {"oil_levels": "very_oily"},
        }
        resp = client.post("/v1/analyze", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["inference_mode"] == "placeholder_phase1"
        assert body["skin_type"] == "Oily"   # questionnaire hint
        assert set(body["skin_type_scores"].keys()) == {
            "Oily", "Dry", "Combination", "Normal", "Sensitive"
        }
        assert "disclaimer" in body
        assert "not replace professional" in body["disclaimer"].lower()


def test_analyze_rejects_bad_image() -> None:
    with TestClient(app) as client:
        resp = client.post(
            "/v1/analyze", json={"image_base64": "not-base64!!!", "questionnaire": {}}
        )
        assert resp.status_code == 400
