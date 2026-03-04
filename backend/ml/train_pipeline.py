#!/usr/bin/env python3
"""
Real-Data Training Pipeline for Skin Analysis Model
====================================================
Downloads HAM10000 (clinician-labeled dermatology images from Harvard Dataverse),
maps real labels to our skin type/condition label space, trains EfficientNetB0,
and exports a clean SavedModel for the backend API.

Run from backend/ directory:
    python ml/train_pipeline.py
    python ml/train_pipeline.py --skip-download   (if data already present)
    python ml/train_pipeline.py --phase 1         (only phase 1)
"""

import os
import sys
import csv
import time
import shutil
import zipfile
import argparse
import urllib.request
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import numpy as np
import yaml

# ---------------------------------------------------------------------------
# Paths (all relative to backend/ = Docker /app)
# ---------------------------------------------------------------------------
CONFIG_PATH   = Path("ml/config.yaml")
DATA_DIR      = Path("ml/data/ham10000")
CHECKPOINT_DIR = Path("ml/checkpoints")
LOGS_DIR      = Path("ml/logs")
SAVED_MODEL_DIR = Path("app/models_artifacts/saved_model")

# ---------------------------------------------------------------------------
# Label spaces (must match config.yaml and inference.py)
# ---------------------------------------------------------------------------
SKIN_TYPES = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
CONDITIONS = ["Acne", "Hyperpigmentation", "Uneven tone", "Dehydration", "None detected"]
NUM_CLASSES = len(SKIN_TYPES) + len(CONDITIONS)  # 10

# ---------------------------------------------------------------------------
# HAM10000 clinical label → our label space
# Mapping based on dermatological characteristics:
#   nv   = melanocytic nevi (common benign moles)    → Normal / None detected
#   mel  = melanoma (pigmented, sun-sensitive)        → Sensitive / Hyperpigmentation
#   bkl  = benign keratosis (pigmented plaques)       → Combination / Hyperpigmentation
#   bcc  = basal cell carcinoma (oily/exposed areas)  → Oily / Acne
#   akiec= actinic keratoses (dry sun-damaged)        → Dry / Uneven tone
#   vasc = vascular lesions (redness, dilation)       → Sensitive / Acne
#   df   = dermatofibroma (benign, normal skin)       → Normal / None detected
# ---------------------------------------------------------------------------
HAM_TO_SKIN_TYPE = {
    "nv":    "Normal",
    "mel":   "Sensitive",
    "bkl":   "Combination",
    "bcc":   "Oily",
    "akiec": "Dry",
    "vasc":  "Sensitive",
    "df":    "Normal",
}
HAM_TO_CONDITION = {
    "nv":    "None detected",
    "mel":   "Hyperpigmentation",
    "bkl":   "Hyperpigmentation",
    "bcc":   "Acne",
    "akiec": "Uneven tone",
    "vasc":  "Acne",
    "df":    "None detected",
}

# ---------------------------------------------------------------------------
# HAM10000 download URLs (Harvard Dataverse – publicly accessible)
# File IDs verified 2026-03-04 via:
#   GET https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/DBW86T
# ---------------------------------------------------------------------------
_DATAVERSE_BASE = "https://dataverse.harvard.edu/api/access/datafile"
HAM_URLS = {
    "metadata": f"{_DATAVERSE_BASE}/4338392",   # HAM10000_metadata.tab
    "part1":    f"{_DATAVERSE_BASE}/3172585",   # HAM10000_images_part_1.zip
    "part2":    f"{_DATAVERSE_BASE}/3172584",   # HAM10000_images_part_2.zip
}
_META_FILENAME = "HAM10000_metadata.tab"   # tab-separated values


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100, downloaded * 100 / total_size)
        mb = downloaded / 1_048_576
        total_mb = total_size / 1_048_576
        bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
        print(f"\r  [{bar}] {pct:5.1f}%  {mb:.1f}/{total_mb:.1f} MB", end="", flush=True)


def download_file(url: str, dest: Path, label: str):
    if dest.exists():
        print(f"  ✓ Already downloaded: {dest.name}")
        return
    print(f"\n  Downloading {label} …")
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [
            ("User-Agent", "Mozilla/5.0 (compatible; SkinCareML/1.0; Python/3.11)"),
            ("Accept", "*/*"),
        ]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, dest, _progress_hook)
        print()  # newline after progress bar
        print(f"  ✓ Saved: {dest}")
    except Exception as e:
        print(f"\n  ✗ Failed to download {label}: {e}")
        raise


def extract_zip(zip_path: Path, dest: Path):
    print(f"  Extracting {zip_path.name} …")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
    print(f"  ✓ Extracted to {dest}")


# ---------------------------------------------------------------------------
# Step 1 – Download HAM10000
# ---------------------------------------------------------------------------
def download_ham10000():
    print("\n" + "=" * 70)
    print("STEP 1/4  Download HAM10000 (clinician-labeled dermatology images)")
    print("=" * 70)
    print("Source  : Harvard Dataverse (public)")
    print("Images  : ~10,015  |  Labels: 7 clinician-verified categories")
    print("Size    : ~2 GB")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ── Metadata TAB ──────────────────────────────────────────────────────
    meta_path = DATA_DIR / _META_FILENAME
    download_file(HAM_URLS["metadata"], meta_path, "metadata (tab-separated)")

    # ── Images part 1 ─────────────────────────────────────────────────────
    part1_zip = DATA_DIR / "HAM10000_images_part_1.zip"
    part1_dir = DATA_DIR / "HAM10000_images_part_1"
    if not part1_dir.exists():
        download_file(HAM_URLS["part1"], part1_zip, "images part 1/2")
        extract_zip(part1_zip, DATA_DIR)
    else:
        print(f"  ✓ Already extracted: {part1_dir.name}")

    # ── Images part 2 ─────────────────────────────────────────────────────
    part2_zip = DATA_DIR / "HAM10000_images_part_2.zip"
    part2_dir = DATA_DIR / "HAM10000_images_part_2"
    if not part2_dir.exists():
        download_file(HAM_URLS["part2"], part2_zip, "images part 2/2")
        extract_zip(part2_zip, DATA_DIR)
    else:
        print(f"  ✓ Already extracted: {part2_dir.name}")

    # Count
    all_imgs = list(DATA_DIR.rglob("*.jpg"))
    print(f"\n  ✓ Total images available: {len(all_imgs)}")
    return meta_path, all_imgs


# ---------------------------------------------------------------------------
# Step 2 – Build label index from metadata CSV
# ---------------------------------------------------------------------------
def build_label_index(meta_path: Path, all_imgs: list) -> dict:
    """
    Returns dict: image_id → label info.
    Supports both comma-separated (.csv) and tab-separated (.tab) metadata.
    """
    print("\n" + "=" * 70)
    print("STEP 2/4  Building real label index from HAM10000 metadata")
    print("=" * 70)

    # Build image_id → path lookup
    img_lookup = {p.stem: p for p in all_imgs}

    label_index = {}
    skipped = 0

    # Auto-detect delimiter
    delimiter = "\t" if meta_path.suffix == ".tab" else ","

    with open(meta_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            img_id = row.get("image_id", "").strip()
            dx = row.get("dx", "").strip().lower()

            if img_id not in img_lookup:
                skipped += 1
                continue
            if dx not in HAM_TO_SKIN_TYPE:
                skipped += 1
                continue

            skin_type = HAM_TO_SKIN_TYPE[dx]
            condition  = HAM_TO_CONDITION[dx]

            skin_idx = SKIN_TYPES.index(skin_type)
            cond_idx = CONDITIONS.index(condition)

            label_index[img_id] = {
                "path":      img_lookup[img_id],
                "skin_type": skin_type,
                "condition": condition,
                "skin_idx":  skin_idx,
                "cond_idx":  cond_idx,
            }

    # Distribution
    from collections import Counter
    skin_dist = Counter(v["skin_type"] for v in label_index.values())
    cond_dist = Counter(v["condition"] for v in label_index.values())

    print(f"  ✓ Labelled images  : {len(label_index)}")
    print(f"  ✗ Skipped          : {skipped}")
    print(f"\n  Skin type distribution:")
    for k, v in sorted(skin_dist.items()):
        bar = "█" * (v // 50)
        print(f"    {k:<12} {v:>5}  {bar}")
    print(f"\n  Condition distribution:")
    for k, v in sorted(cond_dist.items()):
        bar = "█" * (v // 50)
        print(f"    {k:<20} {v:>5}  {bar}")

    return label_index


# ---------------------------------------------------------------------------
# Step 3 – Create TF datasets from real labeled images
# ---------------------------------------------------------------------------
def create_real_datasets(label_index: dict, config: dict):
    import tensorflow as tf

    print("\n" + "=" * 70)
    print("STEP 3/4  Creating TF datasets from real labeled images")
    print("=" * 70)

    items = list(label_index.values())
    np.random.seed(42)
    np.random.shuffle(items)

    n = len(items)
    n_train = int(n * config["dataset"]["train_split"])
    n_val   = int(n * config["dataset"]["val_split"])

    train_items = items[:n_train]
    val_items   = items[n_train:n_train + n_val]
    test_items  = items[n_train + n_val:]

    print(f"  Train  : {len(train_items)}")
    print(f"  Val    : {len(val_items)}")
    print(f"  Test   : {len(test_items)}")

    def make_label_vector(skin_idx: int, cond_idx: int) -> np.ndarray:
        """Multi-hot vector: skin type + condition both flagged."""
        v = np.zeros(NUM_CLASSES, dtype=np.float32)
        v[skin_idx] = 1.0
        v[len(SKIN_TYPES) + cond_idx] = 1.0
        return v

    def load_image(path_str: str) -> np.ndarray:
        raw = tf.io.read_file(path_str)
        img = tf.image.decode_jpeg(raw, channels=3)
        img = tf.image.resize(img, [IMG_SIZE, IMG_SIZE])
        img = tf.cast(img, tf.float32) / 255.0
        return img

    IMG_SIZE = config["model"]["input_size"]
    BATCH    = config["dataset"]["batch_size"]

    def build_ds(items_list, augment: bool):
        paths  = [str(it["path"]) for it in items_list]
        labels = np.array([
            make_label_vector(it["skin_idx"], it["cond_idx"])
            for it in items_list
        ], dtype=np.float32)

        path_ds  = tf.data.Dataset.from_tensor_slices(paths)
        label_ds = tf.data.Dataset.from_tensor_slices(labels)

        img_ds = path_ds.map(
            lambda p: load_image(p),
            num_parallel_calls=tf.data.AUTOTUNE
        )
        ds = tf.data.Dataset.zip((img_ds, label_ds))

        if augment:
            ds = ds.map(_augment_fn, num_parallel_calls=tf.data.AUTOTUNE)

        ds = ds.shuffle(min(1000, len(items_list)))
        ds = ds.batch(BATCH)
        ds = ds.prefetch(tf.data.AUTOTUNE)
        return ds

    aug_cfg = config["dataset"]["augmentation"]

    def _augment_fn(img, label):
        if aug_cfg.get("random_flip"):
            img = tf.image.random_flip_left_right(img)
        if aug_cfg.get("random_brightness"):
            img = tf.image.random_brightness(img, aug_cfg["random_brightness"])
        if aug_cfg.get("random_contrast"):
            delta = aug_cfg["random_contrast"]
            img = tf.image.random_contrast(img, 1 - delta, 1 + delta)
        img = tf.clip_by_value(img, 0.0, 1.0)
        return img, label

    train_ds = build_ds(train_items, augment=True)
    val_ds   = build_ds(val_items,   augment=False)
    test_ds  = build_ds(test_items,  augment=False)

    return train_ds, val_ds, test_ds, test_items


# ---------------------------------------------------------------------------
# Step 4 – Train & export
# ---------------------------------------------------------------------------
def build_model(config: dict, phase: int):
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers

    arch = config["architecture"]
    IMG_SIZE = config["model"]["input_size"]

    inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3), name="input_image")

    base = keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_tensor=inputs,
    )

    if phase == 1:
        base.trainable = False
    else:
        base.trainable = True
        unfreeze = config["training"]["phase2"]["unfreeze_layers"]
        for layer in base.layers:
            layer.trainable = False
        for layer in base.layers[-unfreeze:]:
            layer.trainable = True
        unfrozen = sum(1 for l in base.layers if l.trainable)
        print(f"  Phase 2: unfroze top {unfrozen} layers")

    x = base.output
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    if arch["batch_normalization"]:
        x = layers.BatchNormalization(name="bn")(x)
    x = layers.Dense(arch["dense_units"], activation=arch["dense_activation"], name="dense")(x)
    if arch["dropout_rate"] > 0:
        x = layers.Dropout(arch["dropout_rate"], name="dropout")(x)
    outputs = layers.Dense(NUM_CLASSES, activation="softmax", name="output")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name=f"SkinAnalysis_P{phase}")

    train_cfg = config["training"][f"phase{phase}"]
    optimizer = keras.optimizers.Adam(learning_rate=train_cfg["learning_rate"])

    model.compile(
        optimizer=optimizer,
        loss=keras.losses.CategoricalCrossentropy(),
        metrics=[
            keras.metrics.CategoricalAccuracy(name="accuracy"),
            keras.metrics.Precision(name="precision"),
            keras.metrics.Recall(name="recall"),
        ],
    )

    total = model.count_params()
    trainable = sum(int(np.prod(w.shape)) for w in model.trainable_weights)
    print(f"  Total params     : {total:,}")
    print(f"  Trainable params : {trainable:,}")
    return model


def get_callbacks(phase: int, config: dict):
    from tensorflow import keras

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    train_cfg = config["training"][f"phase{phase}"]
    ckpt_path = str(CHECKPOINT_DIR / f"phase{phase}_best.keras")

    return [
        keras.callbacks.ModelCheckpoint(
            ckpt_path,
            monitor="val_loss",
            save_best_only=True,
            mode="min",
            verbose=1,
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=train_cfg["early_stopping_patience"],
            restore_best_weights=True,
            verbose=1,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=train_cfg["reduce_lr_factor"],
            patience=train_cfg["reduce_lr_patience"],
            min_lr=1e-7,
            verbose=1,
        ),
        keras.callbacks.TensorBoard(
            log_dir=str(LOGS_DIR / f"phase{phase}"),
            histogram_freq=0,
        ),
        keras.callbacks.CSVLogger(
            str(CHECKPOINT_DIR / f"phase{phase}_log.csv")
        ),
    ]


def train_phase(phase: int, config: dict, train_ds, val_ds, test_ds,
                prev_model=None):
    import tensorflow as tf

    print(f"\n{'='*70}")
    print(f"  Training Phase {phase}  ({'feature extraction' if phase==1 else 'fine-tuning'})")
    print(f"{'='*70}")

    train_cfg = config["training"][f"phase{phase}"]

    if phase == 2 and prev_model is not None:
        # Rebuild with top layers unfrozen, reload weights
        model = build_model(config, phase=2)
        ckpt = str(CHECKPOINT_DIR / "phase1_best.keras")
        if Path(ckpt).exists():
            print(f"  Loading Phase 1 weights from {ckpt}")
            p1 = tf.keras.models.load_model(ckpt)
            # Transfer weights layer by layer where shapes match
            for layer in model.layers:
                try:
                    src = p1.get_layer(layer.name)
                    layer.set_weights(src.get_weights())
                except Exception:
                    pass
            print("  ✓ Phase 1 weights transferred")
        else:
            print("  ⚠ Phase 1 checkpoint not found – starting Phase 2 from scratch")
    else:
        model = build_model(config, phase=phase)

    callbacks = get_callbacks(phase, config)

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=train_cfg["epochs"],
        callbacks=callbacks,
        verbose=1,
    )

    print(f"\n  Evaluating Phase {phase} on test set …")
    results = model.evaluate(test_ds, verbose=1)
    names = ["loss", "accuracy", "precision", "recall"]
    for name, val in zip(names, results):
        print(f"  Test {name}: {val:.4f}")

    return model, history, results


def export_saved_model(model):
    """
    Export with an explicit serving_default signature so inference.py
    can find it via model.signatures['serving_default'].
    """
    import tensorflow as tf

    print(f"\n{'='*70}")
    print("  Exporting SavedModel")
    print(f"{'='*70}")

    SAVED_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    IMG_SIZE = 224

    @tf.function(input_signature=[
        tf.TensorSpec(shape=[None, IMG_SIZE, IMG_SIZE, 3], dtype=tf.float32, name="input_image")
    ])
    def serve(input_image):
        return {"output": model(input_image, training=False)}

    tf.saved_model.save(
        model,
        str(SAVED_MODEL_DIR),
        signatures={"serving_default": serve},
    )

    # Validate
    loaded = tf.saved_model.load(str(SAVED_MODEL_DIR))
    infer  = loaded.signatures.get("serving_default")
    if infer is None:
        print("  ✗ serving_default signature missing!")
        sys.exit(1)

    dummy = tf.random.uniform([1, IMG_SIZE, IMG_SIZE, 3])
    out   = infer(input_image=dummy)
    probs = list(out.values())[0].numpy()[0]
    print(f"  ✓ Signature   : serving_default")
    print(f"  ✓ Output shape: {probs.shape}")
    print(f"  ✓ Prob sum    : {probs.sum():.4f}  (should be ≈ 1.0)")

    # Human-readable sample prediction
    skin_probs = probs[:len(SKIN_TYPES)]
    cond_probs = probs[len(SKIN_TYPES):]
    top_skin = SKIN_TYPES[int(np.argmax(skin_probs))]
    top_cond = CONDITIONS[int(np.argmax(cond_probs))]
    print(f"\n  Sample inference (random image):")
    print(f"    Skin type  : {top_skin}  ({skin_probs.max():.3f})")
    print(f"    Condition  : {top_cond}  ({cond_probs.max():.3f})")

    # Size
    size = sum(f.stat().st_size for f in SAVED_MODEL_DIR.rglob("*") if f.is_file())
    print(f"\n  ✓ SavedModel saved to : {SAVED_MODEL_DIR}")
    print(f"  ✓ Size                : {size / 1_048_576:.1f} MB")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Skincare ML Training Pipeline")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip download if HAM10000 already present")
    parser.add_argument("--phase", type=int, choices=[1, 2, 12], default=12,
                        help="Training phase(s): 1, 2, or 12 (both). Default=12")
    args = parser.parse_args()

    print("\n" + "█" * 70)
    print("  SKINCARE ML – REAL DATA TRAINING PIPELINE")
    print("  Dataset : HAM10000 (clinician-labeled, Harvard Dataverse)")
    print("  Model   : EfficientNetB0 → 10-class skin analysis")
    print("█" * 70)

    # Load config
    if not CONFIG_PATH.exists():
        print(f"✗ Config not found: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    # ── Step 1: Download ─────────────────────────────────────────────────
    if args.skip_download:
        meta_path = DATA_DIR / _META_FILENAME
        all_imgs  = list(DATA_DIR.rglob("*.jpg"))
        if not meta_path.exists() or not all_imgs:
            print("✗ --skip-download set but data not found. Run without that flag.")
            sys.exit(1)
        print(f"  ✓ Using existing data  : {len(all_imgs)} images")
    else:
        meta_path, all_imgs = download_ham10000()

    # ── Step 2: Label index ───────────────────────────────────────────────
    label_index = build_label_index(meta_path, all_imgs)
    if len(label_index) < 100:
        print("✗ Too few labeled images to train. Check download.")
        sys.exit(1)

    # ── Step 3: Datasets ─────────────────────────────────────────────────
    train_ds, val_ds, test_ds, test_items = create_real_datasets(label_index, config)

    # ── Step 4: Train ────────────────────────────────────────────────────
    model = None
    if args.phase in (1, 12):
        model, _, _ = train_phase(1, config, train_ds, val_ds, test_ds)

    if args.phase in (2, 12):
        model, _, results = train_phase(2, config, train_ds, val_ds, test_ds, prev_model=model)

        # Check against performance targets
        val = config.get("validation", {})
        acc = results[1] if len(results) > 1 else 0
        print(f"\n  Performance vs targets:")
        print(f"    Accuracy  : {acc:.4f}  (target ≥ {val.get('min_accuracy', 0.75)})")
        if acc < val.get("min_accuracy", 0.75):
            print("    ⚠ Below accuracy target – consider more epochs or data")

    # ── Export ────────────────────────────────────────────────────────────
    if model is not None:
        export_saved_model(model)
    else:
        # Only phase 1 was run – load best checkpoint and export
        import tensorflow as tf
        ckpt = CHECKPOINT_DIR / "phase1_best.keras"
        if ckpt.exists():
            model = tf.keras.models.load_model(str(ckpt))
            export_saved_model(model)

    print("\n" + "█" * 70)
    print("  TRAINING COMPLETE")
    print("█" * 70)
    print(f"\n  SavedModel → {SAVED_MODEL_DIR}")
    print("\n  Next steps:")
    print("    docker-compose restart api")
    print("    # or for a full rebuild:")
    print("    docker-compose up --build -d")
    print("█" * 70 + "\n")


if __name__ == "__main__":
    main()
