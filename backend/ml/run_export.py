#!/usr/bin/env python3
"""
Quick script to export the best checkpoint to SavedModel without retraining.
Run this from the backend/ directory inside the training environment:

    cd backend
    python ml/run_export.py
    python ml/run_export.py --checkpoint ml/checkpoints/phase2_best.keras

After exporting, restart the API container:
    docker-compose restart api
"""

import sys
import argparse
from pathlib import Path

os_error = None
try:
    import tensorflow as tf
    from tensorflow import keras
except ImportError as e:
    os_error = e

CHECKPOINT_DIR = Path("ml/checkpoints")
SAVED_MODEL_DIR = Path("app/models_artifacts/saved_model")
IMG_SIZE = 224


def export(checkpoint_path: Path):
    if os_error:
        print(f"✗ TensorFlow not available: {os_error}")
        sys.exit(1)

    if not checkpoint_path.exists():
        print(f"✗ Checkpoint not found: {checkpoint_path}")
        sys.exit(1)

    print(f"Loading checkpoint: {checkpoint_path}")
    model = keras.models.load_model(str(checkpoint_path))
    print(f"  input  shape : {model.input_shape}")
    print(f"  output shape : {model.output_shape}")
    print(f"  params       : {model.count_params():,}")

    SAVED_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    @tf.function(input_signature=[
        tf.TensorSpec(shape=[None, IMG_SIZE, IMG_SIZE, 3],
                      dtype=tf.float32, name="input_image")
    ])
    def serve(input_image):
        return {"output": model(input_image, training=False)}

    tf.saved_model.save(model, str(SAVED_MODEL_DIR), signatures={"serving_default": serve})

    # Validate
    loaded = tf.saved_model.load(str(SAVED_MODEL_DIR))
    infer = loaded.signatures.get("serving_default")
    if infer is None:
        print("✗ serving_default signature missing — export failed")
        sys.exit(1)

    dummy = tf.random.uniform([1, IMG_SIZE, IMG_SIZE, 3])
    out = infer(input_image=dummy)
    probs = list(out.values())[0].numpy()[0]
    size_mb = sum(f.stat().st_size for f in SAVED_MODEL_DIR.rglob("*") if f.is_file()) / 1_048_576

    print(f"\n✓ SavedModel exported to : {SAVED_MODEL_DIR}")
    print(f"✓ Size                   : {size_mb:.1f} MB")
    print(f"✓ Output shape           : {probs.shape}")
    print(f"✓ Prob range             : [{probs.min():.4f}, {probs.max():.4f}]")
    print("\nNext: docker-compose restart api")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export best checkpoint to SavedModel")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str(CHECKPOINT_DIR / "phase2_best.keras"),
        help="Path to .keras checkpoint (default: ml/checkpoints/phase2_best.keras)",
    )
    args = parser.parse_args()
    export(Path(args.checkpoint))
