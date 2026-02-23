from app.schemas.analyze import SkinProfile


def run_skin_inference(image_base64: str) -> tuple[SkinProfile, str]:
    # Placeholder for SavedModel/TFLite fallback orchestration.
    _ = image_base64
    profile = SkinProfile(
        skin_type="Combination",
        conditions=["Acne", "Dehydration"],
        confidence=0.81,
    )
    return profile, "server_savedmodel_stub"
