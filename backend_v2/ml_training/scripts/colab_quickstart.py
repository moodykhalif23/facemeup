"""Colab/Kaggle quickstart for training the skin-condition classifier.

Paste-and-run in a Colab cell, or `%run scripts/colab_quickstart.py`.

Workflow (one-time per runtime):
    1. Clone the repo (or mount Drive).
    2. Install ml_service + ml_training in editable mode.
    3. Download SCIN to /content/scin (see note below).
    4. Run this script; it precomputes aligned faces then trains.

NOTE on SCIN access: the Google SCIN dataset requires a data-use agreement at
https://github.com/google-research-datasets/scin . Download the ZIP manually,
extract to `/content/scin/`, and pass `--scin-root /content/scin`.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(str(c) for c in cmd)}\n", flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scin-root", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, default=Path("/content/work"))
    parser.add_argument("--config", type=Path, default=Path("configs/base.yaml"))
    parser.add_argument("--skip-precompute", action="store_true")
    args = parser.parse_args()

    aligned = args.work_dir / "aligned"
    aligned.mkdir(parents=True, exist_ok=True)

    if not args.skip_precompute:
        run([sys.executable, "-m", "skin_training.data.precompute",
             "--scin-root", args.scin_root, "--output", args.work_dir])

    # Patch the config to point at this Colab work dir.
    import yaml
    cfg_raw = yaml.safe_load(args.config.read_text())
    cfg_raw["data"]["aligned_dir"] = str(args.work_dir)
    cfg_raw["train"]["checkpoint_dir"] = str(args.work_dir / "runs" / "colab")
    patched = args.work_dir / "config.yaml"
    patched.write_text(yaml.safe_dump(cfg_raw))

    run([sys.executable, "-m", "skin_training.train.loop", "--config", patched, "-v"])

    best = Path(cfg_raw["train"]["checkpoint_dir"]) / "best.pt"
    onnx_out = args.work_dir / "skin_classifier_mobilenet.onnx"
    run([sys.executable, "-m", "skin_training.export.to_onnx",
         "--checkpoint", best, "--config", patched, "--output", onnx_out])

    print(f"\n✓ training complete — download {onnx_out} and drop into ml_service/models/")


if __name__ == "__main__":
    main()
