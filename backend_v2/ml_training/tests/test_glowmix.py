from pathlib import Path

from skin_training.data.labels import Condition
from skin_training.data.sources.glowmix import load_glowmix


def test_glowmix_folder_loader_infers_labels_from_directories(tmp_path: Path) -> None:
    dark_circles_dir = tmp_path / "Dark Circles"
    acne_dir = tmp_path / "Acne"
    dark_circles_dir.mkdir(parents=True)
    acne_dir.mkdir(parents=True)
    (dark_circles_dir / "eye_01.jpg").write_bytes(b"not-a-real-image")
    (acne_dir / "face_01.jpg").write_bytes(b"not-a-real-image")

    samples = load_glowmix(tmp_path)

    assert len(samples) == 2
    by_case = {s.case_id: s for s in samples}
    assert any(s.label_vector[Condition.DARK_CIRCLES] == 1 for s in by_case.values())
    assert any(s.label_vector[Condition.ACNE] == 1 for s in by_case.values())
