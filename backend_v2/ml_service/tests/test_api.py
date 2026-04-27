from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.pipeline.classify import ONNXClassifier


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


def test_analyze_with_onnx_classifier(
    synthetic_face_b64, fake_mediapipe_landmarks, stub_onnx_session
) -> None:
    """Exercise the ONNX classifier path by injecting a stub into app.state."""
    settings = get_settings()
    with TestClient(app) as client:
        app.state.classifier = ONNXClassifier(stub_onnx_session, settings.conditions)
        payload = {
            "image_base64": synthetic_face_b64,
            "landmarks": fake_mediapipe_landmarks,
            "questionnaire": {"oil_levels": "very_oily"},
        }
        resp = client.post("/v1/analyze", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["inference_mode"] == "onnx_mobilenet"
        assert body["skin_type"] == "Oily"   # questionnaire hint
        assert set(body["condition_scores"].keys()) == {
            "Acne", "Dryness", "Oiliness", "Dark Spots", "Wrinkles", "Redness", "Dark Circles"
        }
        # Heatmaps list is always present; may be empty if the random stub's
        # per-patch probs happen to stay below 0.5.
        assert isinstance(body["heatmaps"], list)
        for hm in body["heatmaps"]:
            assert "label" in hm and "image_base64" in hm
