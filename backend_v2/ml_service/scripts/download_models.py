"""One-shot download of pretrained ONNX artefacts for the ml_service pipeline.

Run once on a fresh checkout; the resulting files are gitignored and live under
`ml_service/models/`. Idempotent: skips files that already exist.

Usage:
    python scripts/download_models.py
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


@dataclass(frozen=True)
class Artefact:
    filename: str
    url: str
    sha256: str | None   # None = skip checksum (use only for trusted mirrors)
    notes: str


# NOTE: these URLs are placeholders — pin them to specific releases before using
# in production. The insightface and face-parsing communities publish ONNX
# exports; pick one with a permissive licence and a known SHA-256.
ARTEFACTS: list[Artefact] = [
    Artefact(
        filename="retinaface_mnet.onnx",
        url="https://github.com/deepinsight/insightface/releases/download/v0.7/retinaface_mnet.onnx",
        sha256=None,
        notes="RetinaFace MobileNet-0.25 face detector + 5-point landmarks",
    ),
    Artefact(
        filename="face_parsing_bisenet.onnx",
        url="https://github.com/zllrunning/face-parsing.PyTorch/releases/download/onnx/bisenet.onnx",
        sha256=None,
        notes="BiSeNet face parsing (19 classes; class 1 = facial skin)",
    ),
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(artefact: Artefact) -> None:
    dest = MODELS_DIR / artefact.filename
    if dest.is_file():
        print(f"✓ {artefact.filename} already present ({dest.stat().st_size:,} bytes)")
        return
    print(f"→ downloading {artefact.filename} from {artefact.url}")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        urllib.request.urlretrieve(artefact.url, tmp)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        print(f"✗ failed to fetch {artefact.filename}: {e}", file=sys.stderr)
        sys.exit(1)

    if artefact.sha256:
        got = sha256_of(tmp)
        if got != artefact.sha256:
            tmp.unlink(missing_ok=True)
            print(
                f"✗ checksum mismatch for {artefact.filename}: "
                f"got {got}, expected {artefact.sha256}",
                file=sys.stderr,
            )
            sys.exit(2)

    tmp.rename(dest)
    print(f"✓ {artefact.filename} → {dest} ({dest.stat().st_size:,} bytes) — {artefact.notes}")


def main() -> None:
    for a in ARTEFACTS:
        fetch(a)
    print("\nAll artefacts ready. Rebuild ml_service so the Dockerfile picks them up:")
    print("  docker compose -f ../docker-compose.yml build ml-service")


if __name__ == "__main__":
    main()
