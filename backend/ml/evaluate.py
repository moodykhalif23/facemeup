"""
Model evaluation script with per-condition metrics (spec §11).

Spec requires per-condition evaluation of:
  - Precision   (avoid false conditions)
  - Recall      (detect real issues)
  - F1 Score    (balance precision and recall)
  - ROC-AUC     (classification reliability)
"""

import argparse
import json
import numpy as np
import yaml
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
import matplotlib.pyplot as plt
import seaborn as sns

from data_loader import SkinDataLoader


def _per_class_metrics(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    class_names: list[str],
    threshold: float = 0.5,
) -> list[dict]:
    """Return per-class Precision, Recall, F1, ROC-AUC (spec §11)."""
    y_pred_bin = (y_pred_proba > threshold).astype(int)
    rows = []

    for i, name in enumerate(class_names):
        t = y_true[:, i]
        p = y_pred_bin[:, i]
        proba = y_pred_proba[:, i]

        tp = int(np.sum((t == 1) & (p == 1)))
        fp = int(np.sum((t == 0) & (p == 1)))
        fn = int(np.sum((t == 1) & (p == 0)))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

        # ROC-AUC requires both classes present; skip if only one class in test set
        try:
            auc = float(roc_auc_score(t, proba)) if len(np.unique(t)) > 1 else float("nan")
        except Exception:
            auc = float("nan")

        rows.append({
            "class":     name,
            "precision": round(prec, 4),
            "recall":    round(rec, 4),
            "f1":        round(f1, 4),
            "roc_auc":   round(auc, 4) if not np.isnan(auc) else "n/a",
            "support":   int(np.sum(t == 1)),
        })

    return rows


def evaluate_model(model_path: str, config_path: str = "ml/config.yaml"):
    """Evaluate trained model on test set with full per-condition metrics."""

    print("=" * 80)
    print("MODEL EVALUATION  (spec §11)")
    print("=" * 80)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    print(f"\nLoading model from: {model_path}")
    model = keras.models.load_model(model_path)
    print("Model loaded successfully")

    print("\nLoading test dataset...")
    data_loader = SkinDataLoader(config_path)
    _, _, test_ds = data_loader.create_datasets()

    test_images, test_labels = [], []
    for images, labels in test_ds:
        test_images.append(images.numpy())
        test_labels.append(labels.numpy())

    test_images = np.concatenate(test_images, axis=0)
    test_labels = np.concatenate(test_labels, axis=0)
    print(f"Test samples: {len(test_images)}")

    print("\nMaking predictions...")
    predictions = model.predict(test_images, verbose=1)

    # ── Overall Keras metrics ────────────────────────────────────────────────
    test_loss, test_acc, test_prec, test_rec = model.evaluate(test_ds, verbose=0)
    overall_f1 = 2 * test_prec * test_rec / (test_prec + test_rec) if (test_prec + test_rec) > 0 else 0

    print("\n" + "=" * 80)
    print("OVERALL METRICS")
    print("=" * 80)
    print(f"  Loss      : {test_loss:.4f}")
    print(f"  Accuracy  : {test_acc:.4f}")
    print(f"  Precision : {test_prec:.4f}")
    print(f"  Recall    : {test_rec:.4f}")
    print(f"  F1-Score  : {overall_f1:.4f}")

    # ── Per-class metrics (spec §11) ─────────────────────────────────────────
    skin_types = config['model']['skin_types']
    conditions = config['model']['conditions']
    class_names = skin_types + conditions

    print("\n" + "=" * 80)
    print("PER-CLASS METRICS  (Precision / Recall / F1 / ROC-AUC)")
    print("=" * 80)

    per_class = _per_class_metrics(test_labels, predictions, class_names)

    header = f"{'Class':<22}  {'Prec':>6}  {'Recall':>6}  {'F1':>6}  {'ROC-AUC':>8}  {'Support':>8}"
    print(header)
    print("-" * len(header))

    skin_rows  = per_class[:len(skin_types)]
    cond_rows  = per_class[len(skin_types):]

    print("\n  --- Skin Types ---")
    for row in skin_rows:
        print(
            f"  {row['class']:<20}  {row['precision']:>6.3f}  {row['recall']:>6.3f}"
            f"  {row['f1']:>6.3f}  {str(row['roc_auc']):>8}  {row['support']:>8}"
        )

    print("\n  --- Conditions ---")
    for row in cond_rows:
        print(
            f"  {row['class']:<20}  {row['precision']:>6.3f}  {row['recall']:>6.3f}"
            f"  {row['f1']:>6.3f}  {str(row['roc_auc']):>8}  {row['support']:>8}"
        )

    # Save per-class metrics as JSON for CI/CD ingestion
    output_dir = Path("ml/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "per_class_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({"overall": {
            "loss": test_loss, "accuracy": test_acc,
            "precision": test_prec, "recall": test_rec, "f1": overall_f1,
        }, "per_class": per_class}, f, indent=2)
    print(f"\n  Per-class metrics saved → {metrics_path}")

    # ── Confusion matrix for skin types ─────────────────────────────────────
    print("\n" + "=" * 80)
    print("CONFUSION MATRIX (Skin Types)")
    print("=" * 80)

    num_skin = len(skin_types)
    skin_true = np.argmax(test_labels[:, :num_skin], axis=1)
    skin_pred = np.argmax(predictions[:, :num_skin], axis=1)
    cm = confusion_matrix(skin_true, skin_pred)

    print("\n" + " " * 14 + "  ".join(f"{n[:8]:8s}" for n in skin_types))
    for i, name in enumerate(skin_types):
        print(f"{name[:12]:12s}  " + "  ".join(f"{cm[i, j]:8d}" for j in range(num_skin)))

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=skin_types, yticklabels=skin_types)
    plt.title("Confusion Matrix — Skin Types")
    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    plt.tight_layout()
    cm_path = output_dir / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Confusion matrix saved → {cm_path}")

    # ── ROC curves for each condition ────────────────────────────────────────
    try:
        fig, axes = plt.subplots(1, len(conditions), figsize=(4 * len(conditions), 4))
        if len(conditions) == 1:
            axes = [axes]
        for ax, row in zip(axes, cond_rows):
            idx = class_names.index(row["class"])
            t = test_labels[:, idx]
            p = predictions[:, idx]
            if len(np.unique(t)) > 1:
                from sklearn.metrics import roc_curve
                fpr, tpr, _ = roc_curve(t, p)
                ax.plot(fpr, tpr, label=f"AUC={row['roc_auc']}")
                ax.plot([0, 1], [0, 1], "k--", lw=0.5)
            ax.set_title(row["class"], fontsize=9)
            ax.set_xlabel("FPR")
            ax.set_ylabel("TPR")
            ax.legend(fontsize=8)
        plt.tight_layout()
        roc_path = output_dir / "roc_curves_conditions.png"
        plt.savefig(roc_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  ROC curves saved       → {roc_path}")
    except Exception as exc:
        print(f"  ⚠ ROC curve plot failed: {exc}")

    # ── Validation targets (spec §11) ────────────────────────────────────────
    val = config.get("validation", {})
    print("\n" + "=" * 80)
    print("VALIDATION TARGETS")
    print("=" * 80)
    targets_met = True
    checks = [
        ("Accuracy",  test_acc,   val.get("min_accuracy",  0.75)),
        ("Precision", test_prec,  val.get("min_precision", 0.70)),
        ("Recall",    test_rec,   val.get("min_recall",    0.70)),
        ("F1-Score",  overall_f1, val.get("min_f1_score",  0.70)),
    ]
    for label, value, target in checks:
        ok = value >= target
        sign = "✓" if ok else "✗"
        print(f"  {sign} {label:<12}: {value:.4f}  (target ≥ {target})")
        if not ok:
            targets_met = False

    # Model size
    model_size = Path(model_path).stat().st_size / (1024 * 1024)
    print(f"\n  Model size: {model_size:.2f} MB")

    if targets_met:
        print("\n  ✓ All validation targets met — model is ready for export.")
    else:
        print("\n  ✗ Some targets not met — consider more epochs or additional data.")

    return {
        "loss":         test_loss,
        "accuracy":     test_acc,
        "precision":    test_prec,
        "recall":       test_rec,
        "f1_score":     overall_f1,
        "model_size_mb": model_size,
        "targets_met":  targets_met,
        "per_class":    per_class,
    }


def main():
    parser = argparse.ArgumentParser(description='Evaluate skin analysis model')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained model')
    parser.add_argument('--config', type=str, default='ml/config.yaml',
                       help='Path to config file')
    
    args = parser.parse_args()
    
    results = evaluate_model(args.model, args.config)
    
    print("\n" + "="*80)
    print("EVALUATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
