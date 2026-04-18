"""Run the ml_service preprocessing pipeline once over a SCIN manifest and
cache aligned face tensors + labels to disk.

Why: detection + alignment + CLAHE take ~50-200ms per image. Doing it every
epoch burns GPU time; caching once lets the training loop be I/O + model only.

Output layout:
    <output_dir>/
        aligned/<case_id>.npy       # uint8 (H, W, 3) BGR aligned face
        labels.csv                  # case_id, fitzpatrick, c0..c5, raw_conditions
        index.json                  # {aligned_size, n_samples, fitzpatrick_dist}
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from tqdm import tqdm

from .labels import CONDITION_NAMES
from .scin import parse_scin_manifest

log = logging.getLogger("precompute")


def precompute(
    scin_root: Path,
    output_dir: Path,
    aligned_size: int = 256,
    skip_existing: bool = True,
) -> dict:
    """Iterate SCIN samples → preprocessing → save .npy + labels.csv."""
    _import_ml_service_or_fail()
    from app.config import get_settings
    from app.onnx_runner import OnnxRegistry
    from app.pipeline import SkinPipeline
    from app.pipeline.decode import decode_base64_image  # noqa: F401 - keep import warm
    from app.pipeline.runner import NoFaceFoundError

    settings = get_settings()
    registry = OnnxRegistry(settings.models_dir, settings.onnx_providers)
    pipeline = SkinPipeline(settings, registry, aligned_size=aligned_size)

    aligned_dir = output_dir / "aligned"
    aligned_dir.mkdir(parents=True, exist_ok=True)
    labels_path = output_dir / "labels.csv"
    index_path = output_dir / "index.json"

    samples = parse_scin_manifest(scin_root)
    log.info("parsed %d SCIN samples", len(samples))

    fp_counter: Counter[int] = Counter()
    skipped_no_face = 0
    processed = 0

    with labels_path.open("w", encoding="utf8", newline="") as lf:
        header = ["case_id", "fitzpatrick", *[f"c{i}_{name.lower()}" for i, name in enumerate(CONDITION_NAMES)], "raw_conditions"]
        lf.write(",".join(header) + "\n")

        for s in tqdm(samples, desc="preprocess"):
            out_npy = aligned_dir / f"{s.case_id}.npy"
            if skip_existing and out_npy.is_file():
                processed += 1
                fp_counter[int(s.fitzpatrick or 0)] += 1
                lf.write(_label_row(s))
                continue

            try:
                img_bytes = s.image_path.read_bytes()
                import base64
                b64 = base64.b64encode(img_bytes).decode("ascii")
                result = pipeline.run(b64, client_landmarks=None)
            except NoFaceFoundError:
                skipped_no_face += 1
                continue
            except Exception as e:
                log.warning("skip %s: %s", s.case_id, e)
                skipped_no_face += 1
                continue

            np.save(out_npy, result.aligned)
            lf.write(_label_row(s))
            processed += 1
            fp_counter[int(s.fitzpatrick or 0)] += 1

    summary = {
        "aligned_size": aligned_size,
        "n_samples": processed,
        "skipped_no_face": skipped_no_face,
        "fitzpatrick_dist": {str(k): v for k, v in sorted(fp_counter.items())},
    }
    index_path.write_text(json.dumps(summary, indent=2))
    log.info("done: %s", summary)
    return summary


def _label_row(s) -> str:
    fp = int(s.fitzpatrick) if s.fitzpatrick else 0
    cols = [s.case_id, str(fp), *[str(v) for v in s.label_vector], "|".join(s.raw_conditions).replace(",", ";")]
    return ",".join(cols) + "\n"


def _import_ml_service_or_fail() -> None:
    try:
        import app  # noqa: F401
    except ImportError:
        print(
            "ERROR: the ml_service `app` package is not importable.\n"
            "Install it first:  pip install -e ../ml_service",
            file=sys.stderr,
        )
        sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess SCIN → aligned tensors")
    parser.add_argument("--scin-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--aligned-size", type=int, default=256)
    parser.add_argument("--force", action="store_true", help="Reprocess even if .npy exists")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    precompute(args.scin_root, args.output, args.aligned_size, skip_existing=not args.force)


if __name__ == "__main__":
    main()
