"""Run the ml_service preprocessing pipeline over one or more data sources and
cache aligned face tensors + labels to disk.

Data sources (choose with --source):
  scin_hf       Google SCIN via HuggingFace (no Drive needed, needs HF login)
  fitzpatrick17k  Fitzpatrick17k via HuggingFace or CSV fallback
  scin_csv      Legacy: parse raw SCIN CSVs from a local folder (--scin-root required)
  all           scin_hf + fitzpatrick17k combined

Why precompute: detection + alignment + CLAHE take ~50–200 ms per image.
Doing it every epoch wastes GPU time. Cache once, train fast.

Output layout:
    <output_dir>/
        aligned/<case_id>.npy       # uint8 (H, W, 3) BGR aligned face
        labels.csv                  # case_id, fitzpatrick, body_part, c0..c5, raw_conditions
        index.json                  # detailed summary
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from tqdm import tqdm

from .labels import CONDITION_NAMES
from .scin import FACE_BODY_PARTS, SCINSample, body_part_distribution, parse_scin_manifest

log = logging.getLogger("precompute")


def load_samples(
    source: str,
    scin_root: Path | None = None,
    hf_cache_dir: str | None = None,
    hf_token: str | None = None,
    face_only: bool = True,
) -> list[SCINSample]:
    """Load samples from the requested source(s)."""
    body_filter = FACE_BODY_PARTS if face_only else None
    sources_to_load = _expand_source(source)
    all_samples: list[SCINSample] = []

    for src in sources_to_load:
        log.info("loading source: %s", src)
        try:
            batch = _load_single(src, scin_root, hf_cache_dir, hf_token, body_filter)
            log.info("  → %d samples from %s", len(batch), src)
            all_samples.extend(batch)
        except Exception as e:
            log.error("source %s failed: %s", src, e)
            raise

    # Deduplicate by case_id (keep first occurrence if the same ID appears twice).
    seen: set[str] = set()
    deduped: list[SCINSample] = []
    for s in all_samples:
        if s.case_id not in seen:
            seen.add(s.case_id)
            deduped.append(s)
    if len(deduped) < len(all_samples):
        log.info("deduplication: %d → %d samples", len(all_samples), len(deduped))

    return deduped


def precompute(
    source: str,
    output_dir: Path,
    scin_root: Path | None = None,
    aligned_size: int = 256,
    skip_existing: bool = True,
    hf_cache_dir: str | None = None,
    hf_token: str | None = None,
    face_only: bool = True,
) -> dict:
    """Run the full preprocessing pipeline and save to output_dir."""
    _import_ml_service_or_fail()
    from app.config import get_settings
    from app.onnx_runner import OnnxRegistry
    from app.pipeline import SkinPipeline
    from app.pipeline.runner import NoFaceFoundError

    settings = get_settings()
    registry = OnnxRegistry(settings.models_dir, settings.onnx_providers)
    pipeline = SkinPipeline(settings, registry, aligned_size=aligned_size)

    aligned_dir = output_dir / "aligned"
    aligned_dir.mkdir(parents=True, exist_ok=True)
    labels_path = output_dir / "labels.csv"
    index_path = output_dir / "index.json"

    samples = load_samples(source, scin_root, hf_cache_dir, hf_token, face_only)
    if not samples:
        log.error("0 samples loaded — check source, auth, and body-part filter settings")
        sys.exit(3)

    bp_dist = body_part_distribution(samples)
    log.info("body-part distribution (top 10): %s", dict(list(bp_dist.items())[:10]))

    fp_counter: Counter[int] = Counter()
    skipped_no_face = 0
    processed = 0

    with labels_path.open("w", encoding="utf8", newline="") as lf:
        header = [
            "case_id", "fitzpatrick", "body_part",
            *[f"c{i}_{name.lower()}" for i, name in enumerate(CONDITION_NAMES)],
            "raw_conditions",
        ]
        lf.write(",".join(header) + "\n")

        for s in tqdm(samples, desc="preprocess", unit="img"):
            out_npy = aligned_dir / f"{s.case_id}.npy"
            if skip_existing and out_npy.is_file():
                processed += 1
                fp_counter[int(s.fitzpatrick or 0)] += 1
                lf.write(_label_row(s))
                continue

            try:
                img_bytes = s.get_bytes()
                b64 = base64.b64encode(img_bytes).decode("ascii")
                result = pipeline.run(b64, client_landmarks=None)
            except NoFaceFoundError:
                skipped_no_face += 1
                continue
            except Exception as e:
                log.warning("skip %s (%s): %s", s.case_id, s.body_part, e)
                skipped_no_face += 1
                continue

            np.save(out_npy, result.aligned)
            lf.write(_label_row(s))
            processed += 1
            fp_counter[int(s.fitzpatrick or 0)] += 1

    face_detect_skip_pct = skipped_no_face / max(1, len(samples)) * 100
    if face_detect_skip_pct > 40:
        log.warning(
            "%.0f%% skip rate at face-detection stage. Consider adding "
            "the RetinaFace ONNX model: python ml_service/scripts/download_models.py",
            face_detect_skip_pct,
        )

    summary = {
        "source": source,
        "aligned_size": aligned_size,
        "face_only_filter": face_only,
        "n_candidates": len(samples),
        "n_samples": processed,
        "skipped_no_face": skipped_no_face,
        "face_detect_skip_pct": round(face_detect_skip_pct, 1),
        "body_part_dist": dict(list(bp_dist.items())[:20]),
        "fitzpatrick_dist": {str(k): v for k, v in sorted(fp_counter.items())},
    }
    index_path.write_text(json.dumps(summary, indent=2))
    log.info("done: processed=%d, skipped_no_face=%d (%.0f%%)",
             processed, skipped_no_face, face_detect_skip_pct)
    return summary


# ── helpers ───────────────────────────────────────────────────────────────────

def _expand_source(source: str) -> list[str]:
    if source == "all":
        return ["scin_hf", "fitzpatrick17k"]
    return [source]


def _load_single(
    source: str,
    scin_root: Path | None,
    hf_cache_dir: str | None,
    hf_token: str | None,
    body_filter,
) -> list[SCINSample]:
    if source == "scin_hf":
        from .sources.scin_hf import load_scin_hf
        return load_scin_hf(body_parts=body_filter, cache_dir=hf_cache_dir, token=hf_token)

    if source == "fitzpatrick17k":
        from .sources.fitzpatrick17k import load_fitzpatrick17k
        return load_fitzpatrick17k(body_parts=body_filter, cache_dir=hf_cache_dir, token=hf_token)

    if source == "scin_csv":
        if scin_root is None:
            raise ValueError("--scin-root is required for source=scin_csv")
        return parse_scin_manifest(scin_root, body_parts=body_filter)

    raise ValueError(f"unknown source: {source!r} — use scin_hf | fitzpatrick17k | scin_csv | all")


def _label_row(s: SCINSample) -> str:
    fp = int(s.fitzpatrick) if s.fitzpatrick else 0
    bp = (s.body_part or "").replace(",", ";")
    cond_str = "|".join(s.raw_conditions).replace(",", ";")
    return ",".join([s.case_id, str(fp), bp,
                     *[str(v) for v in s.label_vector],
                     cond_str]) + "\n"


def _import_ml_service_or_fail() -> None:
    """Ensure ml_service's `app` package is importable.

    When installed with `pip install -e ml_service`, the editable install adds
    the ml_service directory to the path so `import app` works. If that fails
    (e.g. Colab subprocess with a different env), we auto-add the most likely
    ml_service paths and retry before giving up.
    """
    try:
        import app  # noqa: F401
        return
    except ImportError:
        pass

    # Auto-discovery: look for ml_service relative to this file and typical Colab paths.
    import pathlib
    candidates = [
        pathlib.Path(__file__).resolve().parents[5] / "ml_service",   # ../../../.. from data/
        pathlib.Path("/content/skincare/backend_v2/ml_service"),
        pathlib.Path("/content/facemeup/backend_v2/ml_service"),
    ]
    # Also check PYTHONPATH env var
    for extra in os.environ.get("PYTHONPATH", "").split(":"):
        if extra:
            candidates.append(pathlib.Path(extra))

    for candidate in candidates:
        if (candidate / "app").is_dir() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
            try:
                import app  # noqa: F401
                log.info("ml_service auto-added to sys.path from %s", candidate)
                return
            except ImportError:
                sys.path.pop(0)

    print(
        "ERROR: the ml_service `app` package is not importable.\n"
        "Fix:  pip install -e /path/to/backend_v2/ml_service\n"
        "  OR: PYTHONPATH=/path/to/backend_v2/ml_service python -m skin_training.data.precompute ...",
        file=sys.stderr,
    )
    sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preprocess face-skin images → aligned tensors for training"
    )
    parser.add_argument("--source", default="scin_hf",
                        choices=["scin_hf", "fitzpatrick17k", "scin_csv", "all"],
                        help="Data source (default: scin_hf)")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scin-root", type=Path, default=None,
                        help="Path to local SCIN folder (only for source=scin_csv)")
    parser.add_argument("--aligned-size", type=int, default=256)
    parser.add_argument("--force", action="store_true",
                        help="Reprocess even if .npy already exists")
    parser.add_argument("--all-body-parts", action="store_true",
                        help="Disable face/neck filter (higher skip rate at face-detector)")
    parser.add_argument("--hf-cache-dir", default=None,
                        help="HuggingFace cache directory (e.g. /content/drive/.../hf_cache)")
    parser.add_argument("--hf-token", default=None,
                        help="HuggingFace access token (reads HUGGINGFACE_TOKEN env if unset)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    precompute(
        source=args.source,
        output_dir=args.output,
        scin_root=args.scin_root,
        aligned_size=args.aligned_size,
        skip_existing=not args.force,
        hf_cache_dir=args.hf_cache_dir,
        hf_token=args.hf_token,
        face_only=not args.all_body_parts,
    )


if __name__ == "__main__":
    main()
