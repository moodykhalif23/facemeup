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
import json
import zipfile
import argparse
from pathlib import Path

import requests

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import numpy as np
import yaml

# ---------------------------------------------------------------------------
# Paths (all relative to backend/ = Docker /app)
# ---------------------------------------------------------------------------
CONFIG_PATH     = Path("ml/config.yaml")
DATA_DIR        = Path("ml/data/ham10000")
BITMOJI_DIR     = Path("ml/data/bitmoji")   # Device-captured face images with JSON labels
CHECKPOINT_DIR  = Path("ml/checkpoints")
LOGS_DIR        = Path("ml/logs")
SAVED_MODEL_DIR = Path("app/models_artifacts/saved_model")

# ---------------------------------------------------------------------------
# Label spaces (must match config.yaml and inference.py)
# ---------------------------------------------------------------------------
SKIN_TYPES = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
CONDITIONS = [
    "Acne",
    "Hyperpigmentation",
    "Uneven tone",
    "Redness",
    "None detected",
    # Dehydration and Wrinkles removed: no labeled training data yet
]
NUM_CLASSES = len(SKIN_TYPES) + len(CONDITIONS)  # 10

# ---------------------------------------------------------------------------
# HAM10000 clinical label → our label space
# Mapping based on dermatological characteristics:
#   nv   = melanocytic nevi (common benign moles)    → Normal / None detected
#   mel  = melanoma (pigmented, sun-sensitive)        → Sensitive / Hyperpigmentation
#   bkl  = benign keratosis (pigmented plaques)       → Combination / Hyperpigmentation
#   bcc  = basal cell carcinoma (oily/exposed areas)  → Oily / Acne
#   akiec= actinic keratoses (dry sun-damaged)        → Dry / Uneven tone
#   vasc = vascular lesions (redness, dilation)       → Sensitive / Redness
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
    "vasc":  "Redness",       # vascular lesions → Redness (more accurate than Acne)
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
_CHUNK = 8 * 1024 * 1024  # 8 MB chunks


def download_file(url: str, dest: Path, label: str):
    """Download with requests streaming + resume support via .part files."""
    if dest.exists():
        print(f"  ✓ Already downloaded: {dest.name}")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SkinCareML/1.0; Python/3.11)",
        "Accept": "*/*",
    }

    # Resume a previous partial download if a .part file exists
    tmp = dest.with_suffix(dest.suffix + ".part")
    existing = tmp.stat().st_size if tmp.exists() else 0
    if existing:
        headers["Range"] = f"bytes={existing}-"
        print(f"\n  Resuming {label} from {existing/1e6:.1f} MB …")
    else:
        print(f"\n  Downloading {label} …")

    try:
        with requests.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0)) + existing
            mode = "ab" if existing else "wb"

            downloaded = existing
            last_print = time.time()

            with open(tmp, mode) as f:
                for chunk in r.iter_content(chunk_size=_CHUNK):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        if now - last_print >= 5:  # print every 5s
                            pct = (downloaded / total * 100) if total else 0
                            mb = downloaded / 1e6
                            total_mb = total / 1e6
                            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
                            print(f"  [{bar}] {pct:5.1f}%  {mb:.0f}/{total_mb:.0f} MB",
                                  flush=True)
                            last_print = now

        tmp.rename(dest)
        print(f"  ✓ Saved: {dest}  ({dest.stat().st_size/1e6:.1f} MB)")

    except Exception as e:
        print(f"\n  ✗ Failed: {label}: {e}")
        # Leave the .part file in place so the next run can resume
        raise


def extract_zip(zip_path: Path, dest: Path) -> int:
    """
    Extract zip file, skipping any entries with bad CRC (partial downloads).
    Returns count of successfully extracted files.
    """
    print(f"  Extracting {zip_path.name} …")
    ok = 0
    skipped = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            out = dest / info.filename
            if out.exists():
                ok += 1
                continue
            try:
                zf.extract(info, dest)
                ok += 1
            except (zipfile.BadZipFile, Exception):
                skipped += 1
    if skipped:
        print(f"  ⚠ Extracted {ok} files, skipped {skipped} with bad CRC")
    else:
        print(f"  ✓ Extracted {ok} files to {dest}")
    return ok


# ---------------------------------------------------------------------------
# Step 1 – Download HAM10000
# ---------------------------------------------------------------------------
_MIN_PART1_IMGS = 4000   # enough images to train even if part 1 has some bad CRCs
_MIN_PART2_IMGS = 2000


def _count_imgs(sentinel: Path) -> int:
    return sum(1 for _ in DATA_DIR.glob("*.jpg"))


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
    # Check for already-extracted images directly in DATA_DIR (no subfolder)
    existing_imgs = _count_imgs(DATA_DIR)
    part1_zip = DATA_DIR / "HAM10000_images_part_1.zip"
    part1_done = DATA_DIR / ".part1_done"

    if part1_done.exists():
        print(f"  ✓ Part 1 already extracted ({existing_imgs} images present)")
    elif existing_imgs >= _MIN_PART1_IMGS and not part1_zip.exists():
        # Images extracted but sentinel missing — create it
        part1_done.touch()
        print(f"  ✓ Part 1 images found ({existing_imgs}), marking done")
    else:
        download_file(HAM_URLS["part1"], part1_zip, "images part 1/2")
        extract_zip(part1_zip, DATA_DIR)
        part1_zip.unlink(missing_ok=True)   # free disk space
        part1_done.touch()
        print(f"  ✓ Part 1 done ({_count_imgs(DATA_DIR)} images)")

    # ── Images part 2 ─────────────────────────────────────────────────────
    part2_zip = DATA_DIR / "HAM10000_images_part_2.zip"
    part2_done = DATA_DIR / ".part2_done"

    if part2_done.exists():
        print(f"  ✓ Part 2 already extracted")
    else:
        download_file(HAM_URLS["part2"], part2_zip, "images part 2/2")
        extract_zip(part2_zip, DATA_DIR)
        part2_zip.unlink(missing_ok=True)
        part2_done.touch()
        print(f"  ✓ Part 2 done ({_count_imgs(DATA_DIR)} images)")

    all_imgs = list(DATA_DIR.glob("*.jpg"))
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

    # Only use face-localised images — back/leg/abdomen images cause severe
    # distribution mismatch with phone-camera face photos at inference time.
    FACE_LOCATIONS = {"face", "neck", "ear", "scalp"}
    skipped_location = 0

    with open(meta_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            img_id = row.get("image_id", "").strip()
            dx = row.get("dx", "").strip().lower()
            loc = row.get("localization", "").strip().strip('"').lower()

            if img_id not in img_lookup:
                skipped += 1
                continue
            if dx not in HAM_TO_SKIN_TYPE:
                skipped += 1
                continue
            if loc not in FACE_LOCATIONS:
                skipped_location += 1
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
                "source":    "ham10000_face",
            }

    print(f"  Skipped {skipped_location} non-face images (back/leg/trunk/etc.)")

    user_labels = _load_user_captured_labels(DATA_DIR)
    if user_labels:
        label_index.update(user_labels)
        print(f"\n  ✓ Added user-captured images: {len(user_labels)}")

    bitmoji_labels = _load_bitmoji_labels()
    if bitmoji_labels:
        label_index.update(bitmoji_labels)
        print(f"  ✓ Added Bitmoji device images: {len(bitmoji_labels)}")
        from collections import Counter
        bm_skin_dist = Counter(v["skin_type"] for v in bitmoji_labels.values())
        bm_cond_dist = Counter(v["condition"] for v in bitmoji_labels.values())
        print(f"    Skin types : {dict(bm_skin_dist)}")
        print(f"    Conditions : {dict(bm_cond_dist)}")
    else:
        print(f"\n  ℹ  No Bitmoji images found in {BITMOJI_DIR} (add face images to include them)")

    export_training_manifest_csv(label_index, DATA_DIR / "training_manifest.csv")

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


def _resolve_condition(conditions: list[str]) -> str:
    for c in conditions or []:
        if c in CONDITIONS and c != "None detected":
            return c
    for c in conditions or []:
        if c in CONDITIONS:
            return c
    return "None detected"


def _load_user_captured_labels(data_dir: Path) -> dict:
    """
    Load user-captured images (moved into DATA_DIR/user_*) and attach labels
    from their adjacent metadata JSON files.
    """
    label_index: dict[str, dict] = {}
    for user_dir in data_dir.glob("user_*"):
        if not user_dir.is_dir():
            continue
        for img_path in user_dir.glob("*.*"):
            if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            meta_path = Path(str(img_path) + ".json")
            metadata = {}
            if meta_path.exists():
                try:
                    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    metadata = {}

            skin_type = metadata.get("skin_type") or user_dir.name.replace("user_", "")
            if skin_type not in SKIN_TYPES:
                continue

            conditions = metadata.get("conditions") or []
            condition = _resolve_condition(conditions)
            if condition not in CONDITIONS:
                condition = "None detected"

            skin_idx = SKIN_TYPES.index(skin_type)
            cond_idx = CONDITIONS.index(condition)

            key = f"user_{img_path.stem}"
            label_index[key] = {
                "path": img_path,
                "skin_type": skin_type,
                "condition": condition,
                "skin_idx": skin_idx,
                "cond_idx": cond_idx,
                "questionnaire": metadata.get("questionnaire"),
                "source": "user_captured",
            }
    return label_index


def _load_bitmoji_labels() -> dict:
    """
    Load Bitmoji-device-captured face images from ml/data/bitmoji/.
    Each image (*.jpg / *.jpeg) has a companion *.json with Bitmoji ground-truth labels:
      {
        "skin_type": "Oily",
        "conditions": ["Acne", "Hyperpigmentation", "Dehydration"],
        "result_id": "...",
        ...
      }
    These are real face photos analyzed by the professional Bitmoji skin scanner,
    making them the highest-quality labels in our training set.
    """
    label_index: dict[str, dict] = {}

    if not BITMOJI_DIR.exists():
        return label_index

    img_extensions = {".jpg", ".jpeg", ".png"}
    for img_path in sorted(BITMOJI_DIR.iterdir()):
        if img_path.suffix.lower() not in img_extensions:
            continue

        # Companion JSON has the same stem (result_id.jpg → result_id.json)
        json_path = img_path.with_suffix(".json")
        if not json_path.exists():
            continue

        try:
            meta = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        skin_type = meta.get("skin_type", "")
        if skin_type not in SKIN_TYPES:
            continue

        conditions = meta.get("conditions") or []
        condition = _resolve_condition(conditions)
        if condition not in CONDITIONS:
            condition = "None detected"

        skin_idx = SKIN_TYPES.index(skin_type)
        cond_idx = CONDITIONS.index(condition)   # primary (for compat)

        # All valid condition indices for multi-hot label vector
        cond_indices = list({
            CONDITIONS.index(c) for c in conditions if c in CONDITIONS
        })
        if not cond_indices:
            cond_indices = [cond_idx]

        key = f"bitmoji_{img_path.stem}"
        label_index[key] = {
            "path":         img_path,
            "skin_type":    skin_type,
            "condition":    condition,
            "conditions":   conditions,    # full multi-label list (strings)
            "skin_idx":     skin_idx,
            "cond_idx":     cond_idx,      # primary condition index
            "cond_indices": cond_indices,  # all condition indices (multi-hot)
            "source":       "bitmoji_device",
        }

    return label_index


def export_training_manifest_csv(label_index: dict, output_path: Path) -> None:
    """
    Export a unified manifest of all training items (HAM10000 + user-captured)
    for auditability and future feature-store joins.
    """
    fields = [
        "image_path",
        "skin_type",
        "condition",
        "conditions_all",
        "skin_idx",
        "cond_idx",
        "source",
        "questionnaire",
    ]
    rows = []
    for v in label_index.values():
        conds_all = v.get("conditions") or []
        rows.append(
            {
                "image_path":   str(v.get("path")),
                "skin_type":    v.get("skin_type"),
                "condition":    v.get("condition"),
                "conditions_all": "|".join(conds_all) if conds_all else v.get("condition", ""),
                "skin_idx":     v.get("skin_idx"),
                "cond_idx":     v.get("cond_idx"),
                "source":       v.get("source", "ham10000"),
                "questionnaire": json.dumps(v.get("questionnaire") or {}, ensure_ascii=False),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


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

    # ── ML-007: Rebalance training set before weighting ──────────────────
    # Val and test sets are left untouched (stratified sample of real dist).
    # For training, we:
    #   1. Undersample the dominant (skin_type, condition) pairs so that no
    #      single pair exceeds MAJORITY_CAP samples — prevents the model
    #      learning "always predict Normal/None" on a 68% majority.
    #   2. Oversample every minority pair up to MINORITY_TARGET by repeating
    #      samples — ensures rare conditions (Redness, Wrinkles, Dehydration)
    #      have enough gradient signal to learn from.
    MAJORITY_CAP     = 800    # max samples per (skin_type, condition) pair
    MINORITY_TARGET  = 300    # min samples per pair (repeat if needed)

    from collections import defaultdict
    pair_buckets: dict[tuple, list] = defaultdict(list)
    for it in train_items:
        pair_buckets[(it["skin_type"], it["condition"])].append(it)

    rebalanced: list = []
    rng = np.random.default_rng(42)
    for pair, bucket in pair_buckets.items():
        if len(bucket) > MAJORITY_CAP:
            # Undersample: random subset without replacement
            chosen = rng.choice(len(bucket), size=MAJORITY_CAP, replace=False).tolist()
            rebalanced.extend(bucket[i] for i in chosen)
        elif len(bucket) < MINORITY_TARGET:
            # Oversample: repeat with replacement until target is reached
            repeats = rng.choice(len(bucket), size=MINORITY_TARGET, replace=True).tolist()
            rebalanced.extend(bucket[i] for i in repeats)
        else:
            rebalanced.extend(bucket)

    rng.shuffle(rebalanced)
    train_items = rebalanced

    print(f"  Train  : {len(train_items)} (after rebalance; cap={MAJORITY_CAP}, target={MINORITY_TARGET})")
    print(f"  Val    : {len(val_items)}")
    print(f"  Test   : {len(test_items)}")

    from collections import Counter
    rebal_dist = Counter(f"{it['skin_type']}+{it['condition']}" for it in train_items)
    print(f"\n  Rebalanced training distribution:")
    for label, cnt in sorted(rebal_dist.items()):
        bar = "█" * (cnt // 50)
        print(f"    {label:<35} {cnt:>5}  {bar}")

    # ── ML-003: Inverse-frequency sample weights ─────────────────────────
    # After rebalancing, apply residual inverse-frequency weights so any
    # remaining imbalance within the rebalanced set is further corrected.
    skin_counts = Counter(it["skin_type"] for it in train_items)
    cond_counts = Counter(it["condition"] for it in train_items)
    total_train = len(train_items)

    n_skin_classes = len(SKIN_TYPES)
    n_cond_classes = len(CONDITIONS)

    skin_weight = {
        s: total_train / (n_skin_classes * max(c, 1))
        for s, c in skin_counts.items()
    }
    cond_weight = {
        c: total_train / (n_cond_classes * max(cnt, 1))
        for c, cnt in cond_counts.items()
    }

    # Geometric mean of skin and condition weights, then normalise
    raw_weights = np.array(
        [
            float(np.sqrt(skin_weight[it["skin_type"]] * cond_weight[it["condition"]]))
            for it in train_items
        ],
        dtype=np.float32,
    )
    mean_w = raw_weights.mean()
    train_sample_weights = raw_weights / mean_w

    print(f"\n  Class weights (skin type, normalised):")
    for s, c in sorted(skin_counts.items()):
        w = skin_weight[s] / mean_w
        print(f"    {s:<14} {c:>5} samples  → weight {w:.3f}")
    print(f"\n  Class weights (condition, normalised):")
    for c, cnt in sorted(cond_counts.items()):
        w = cond_weight[c] / mean_w
        print(f"    {c:<22} {cnt:>5} samples  → weight {w:.3f}")

    def make_label_vector(item: dict) -> np.ndarray:
        """Multi-hot vector: skin type (one-hot) + conditions (multi-hot).
        Bitmoji items carry cond_indices (list) for all conditions; HAM10000
        items have only cond_idx (single). Both are handled transparently."""
        v = np.zeros(NUM_CLASSES, dtype=np.float32)
        v[item["skin_idx"]] = 1.0
        for ci in item.get("cond_indices") or [item["cond_idx"]]:
            v[len(SKIN_TYPES) + ci] = 1.0
        return v

    def load_image(path_str: str) -> np.ndarray:
        raw = tf.io.read_file(path_str)
        img = tf.image.decode_jpeg(raw, channels=3,
                                   try_recover_truncated=True,
                                   acceptable_fraction=0.5)
        # Use LANCZOS5 to match inference _preprocess_image resize method
        img = tf.image.resize(img, [IMG_SIZE, IMG_SIZE],
                              method=tf.image.ResizeMethod.LANCZOS5)
        img = tf.cast(img, tf.float32) / 255.0
        # Match inference contrast enhancement (1.2x) so training/inference
        # see the same distribution — eliminates preprocessing mismatch (ML-002)
        img = tf.image.adjust_contrast(img, contrast_factor=1.2)
        img = tf.clip_by_value(img, 0.0, 1.0)
        return img

    IMG_SIZE = config["model"]["input_size"]
    BATCH    = config["dataset"]["batch_size"]

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

    def build_ds(items_list, augment: bool, sample_weights: np.ndarray | None = None):
        paths  = [str(it["path"]) for it in items_list]
        labels = np.array([
            make_label_vector(it)
            for it in items_list
        ], dtype=np.float32)

        path_ds  = tf.data.Dataset.from_tensor_slices(paths)
        label_ds = tf.data.Dataset.from_tensor_slices(labels)

        img_ds = path_ds.map(
            lambda p: load_image(p),
            num_parallel_calls=tf.data.AUTOTUNE
        )

        if sample_weights is not None:
            weight_ds = tf.data.Dataset.from_tensor_slices(sample_weights)
            ds = tf.data.Dataset.zip((img_ds, label_ds, weight_ds))
        else:
            ds = tf.data.Dataset.zip((img_ds, label_ds))

        if augment:
            if sample_weights is not None:
                ds = ds.map(
                    lambda img, lbl, w: (*_augment_fn(img, lbl), w),
                    num_parallel_calls=tf.data.AUTOTUNE,
                )
            else:
                ds = ds.map(_augment_fn, num_parallel_calls=tf.data.AUTOTUNE)

        ds = ds.shuffle(min(1000, len(items_list)))
        ds = ds.batch(BATCH)
        ds = ds.prefetch(tf.data.AUTOTUNE)
        return ds

    train_ds = build_ds(train_items, augment=True,  sample_weights=train_sample_weights)
    val_ds   = build_ds(val_items,   augment=False)
    test_ds  = build_ds(test_items,  augment=False)

    return train_ds, val_ds, test_ds, test_items, train_items


# ---------------------------------------------------------------------------
# Helpers for class-balanced loss
# ---------------------------------------------------------------------------
def _compute_pos_weights(train_items: list) -> np.ndarray:
    """Return per-output positive weights: neg_count / pos_count.

    For a 12-output multi-label problem, each output i gets a weight that
    amplifies the gradient from rare positive examples (Redness, Wrinkles)
    and dampens the gradient from abundant positives (Normal, None detected).
    Clipped to [1.0, 50.0] so minority classes don't explode the gradient.
    """
    label_matrix = np.array(
        [
            _make_label_vector_static(it)
            for it in train_items
        ],
        dtype=np.float32,
    )
    pos_counts = label_matrix.sum(axis=0)                      # shape (12,)
    neg_counts = len(train_items) - pos_counts
    raw = neg_counts / np.maximum(pos_counts, 1.0)
    clipped = np.clip(raw, 1.0, 50.0)
    print("\n  Per-output positive weights (neg/pos, clipped 1–50):")
    all_labels = SKIN_TYPES + CONDITIONS
    for lbl, w, p in zip(all_labels, clipped, pos_counts):
        print(f"    {lbl:<22} pos={int(p):>5}  weight={w:.1f}")
    return clipped.astype(np.float32)


def _make_label_vector_static(item: dict) -> np.ndarray:
    """Multi-hot vector for an item dict. Supports cond_indices (multi-label)
    from Bitmoji items and falls back to cond_idx for HAM10000 items."""
    v = np.zeros(NUM_CLASSES, dtype=np.float32)
    v[item["skin_idx"]] = 1.0
    for ci in item.get("cond_indices") or [item["cond_idx"]]:
        v[len(SKIN_TYPES) + ci] = 1.0
    return v


# ---------------------------------------------------------------------------
# Step 4 – Train & export
# ---------------------------------------------------------------------------
def build_model(config: dict, phase: int, train_items: list | None = None):
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
    outputs = layers.Dense(NUM_CLASSES, activation="sigmoid", name="output")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name=f"SkinAnalysis_P{phase}")

    train_cfg = config["training"][f"phase{phase}"]
    optimizer = keras.optimizers.Adam(learning_rate=train_cfg["learning_rate"])

    # Per-output positive-class weights: for each of the 12 binary outputs,
    # weight positive examples by (num_negatives / num_positives) so rare
    # conditions (Redness, Wrinkles, Dehydration) receive proportionally
    # stronger gradient signal than majority outputs (Normal, None detected).
    # This is more numerically stable than focal loss and avoids the
    # all-zeros collapse that focal gamma>2 causes on severe imbalance.
    from losses import WeightedBCE  # registers class with keras serialization

    _train_items = train_items or []
    pos_weights_np = _compute_pos_weights(_train_items) if _train_items else np.ones(NUM_CLASSES, dtype=np.float32)

    model.compile(
        optimizer=optimizer,
        loss=WeightedBCE(pos_weights_np),
        metrics=[
            keras.metrics.BinaryAccuracy(name="accuracy"),
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
                prev_model=None, train_items: list | None = None):
    import tensorflow as tf

    print(f"\n{'='*70}")
    print(f"  Training Phase {phase}  ({'feature extraction' if phase==1 else 'fine-tuning'})")
    print(f"{'='*70}")

    train_cfg = config["training"][f"phase{phase}"]

    if phase == 2 and prev_model is not None:
        # Rebuild with top layers unfrozen, reload weights
        model = build_model(config, phase=2, train_items=train_items)
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
        model = build_model(config, phase=phase, train_items=train_items)

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
    # sigmoid outputs are independent probabilities — they do NOT sum to 1.0
    print(f"  ✓ Prob range  : [{probs.min():.4f}, {probs.max():.4f}]  (sigmoid, each in [0,1])")

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
def _load_extra_labels(csv_path: Path) -> dict:
    """Load extra labeled images from a CSV (e.g. feedback_export output)."""
    if not csv_path.exists():
        print(f"  ⚠ --extra-labels file not found: {csv_path}")
        return {}

    extra: dict = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            img_path = Path(row.get("image_path", ""))
            if not img_path.exists():
                continue
            skin_type = row.get("skin_type", "")
            condition = row.get("condition", "None detected")
            if skin_type not in SKIN_TYPES or condition not in CONDITIONS:
                continue
            extra[f"extra_{i}_{img_path.stem}"] = {
                "path":      img_path,
                "skin_type": skin_type,
                "condition": condition,
                "skin_idx":  SKIN_TYPES.index(skin_type),
                "cond_idx":  CONDITIONS.index(condition),
                "source":    row.get("source", "extra"),
                "questionnaire": json.loads(row.get("questionnaire") or "{}"),
            }
    print(f"  ✓ Loaded {len(extra)} extra labels from {csv_path}")
    return extra


def main():
    parser = argparse.ArgumentParser(description="Skincare ML Training Pipeline")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip download if HAM10000 already present")
    parser.add_argument("--phase", type=int, choices=[1, 2, 12], default=12,
                        help="Training phase(s): 1, 2, or 12 (both). Default=12")
    parser.add_argument("--extra-labels", type=str, default=None,
                        help="Path to extra labels CSV (e.g. from ml/feedback_export.py)")
    args = parser.parse_args()

    print("\n" + "█" * 70)
    print("  SKINCARE ML – REAL DATA TRAINING PIPELINE")
    print("  Dataset : HAM10000 (clinician-labeled, Harvard Dataverse)")
    print(f"  Model   : EfficientNetB0 → {NUM_CLASSES}-class skin analysis ({len(SKIN_TYPES)} skin types + {len(CONDITIONS)} conditions)")
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
    if args.extra_labels:
        extra = _load_extra_labels(Path(args.extra_labels))
        label_index.update(extra)
        print(f"  ✓ Total after extra labels: {len(label_index)}")
    if len(label_index) < 100:
        print("✗ Too few labeled images to train. Check download.")
        sys.exit(1)

    # ── Step 3: Datasets ─────────────────────────────────────────────────
    train_ds, val_ds, test_ds, _, train_items = create_real_datasets(label_index, config)

    # ── Step 4: Train ────────────────────────────────────────────────────
    model = None
    if args.phase in (1, 12):
        model, _, _ = train_phase(1, config, train_ds, val_ds, test_ds, train_items=train_items)

    if args.phase in (2, 12):
        model, _, results = train_phase(2, config, train_ds, val_ds, test_ds, prev_model=model, train_items=train_items)

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
