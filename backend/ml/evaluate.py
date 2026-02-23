"""
Model evaluation script with detailed metrics.
"""

import argparse
import numpy as np
import yaml
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from data_loader import SkinDataLoader


def evaluate_model(model_path: str, config_path: str = "ml/config.yaml"):
    """Evaluate trained model on test set."""
    
    print("="*80)
    print("MODEL EVALUATION")
    print("="*80)
    
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Load model
    print(f"\nLoading model from: {model_path}")
    model = keras.models.load_model(model_path)
    print("Model loaded successfully")
    
    # Load test data
    print("\nLoading test dataset...")
    data_loader = SkinDataLoader(config_path)
    _, _, test_ds = data_loader.create_datasets()
    
    # Get all test data
    test_images = []
    test_labels = []
    for images, labels in test_ds:
        test_images.append(images.numpy())
        test_labels.append(labels.numpy())
    
    test_images = np.concatenate(test_images, axis=0)
    test_labels = np.concatenate(test_labels, axis=0)
    
    print(f"Test samples: {len(test_images)}")
    
    # Make predictions
    print("\nMaking predictions...")
    predictions = model.predict(test_images, verbose=1)
    
    # Calculate metrics
    print("\n" + "="*80)
    print("EVALUATION METRICS")
    print("="*80)
    
    # Overall metrics
    test_loss, test_acc, test_prec, test_rec = model.evaluate(
        test_ds, verbose=0
    )
    
    print(f"\nOverall Metrics:")
    print(f"  Loss: {test_loss:.4f}")
    print(f"  Accuracy: {test_acc:.4f}")
    print(f"  Precision: {test_prec:.4f}")
    print(f"  Recall: {test_rec:.4f}")
    print(f"  F1-Score: {2 * (test_prec * test_rec) / (test_prec + test_rec):.4f}")
    
    # Per-class metrics
    class_names = config['model']['skin_types'] + config['model']['conditions']
    
    print(f"\nPer-Class Metrics:")
    print("-"*80)
    
    # Convert predictions to binary (threshold = 0.5)
    pred_binary = (predictions > 0.5).astype(int)
    
    for i, class_name in enumerate(class_names):
        true_class = test_labels[:, i]
        pred_class = pred_binary[:, i]
        
        # Calculate metrics for this class
        tp = np.sum((true_class == 1) & (pred_class == 1))
        fp = np.sum((true_class == 0) & (pred_class == 1))
        fn = np.sum((true_class == 1) & (pred_class == 0))
        tn = np.sum((true_class == 0) & (pred_class == 0))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"{class_name:20s} - Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
    
    # Confusion matrix for skin types
    print("\n" + "="*80)
    print("CONFUSION MATRIX (Skin Types)")
    print("="*80)
    
    num_skin_types = len(config['model']['skin_types'])
    skin_type_labels = np.argmax(test_labels[:, :num_skin_types], axis=1)
    skin_type_preds = np.argmax(predictions[:, :num_skin_types], axis=1)
    
    cm = confusion_matrix(skin_type_labels, skin_type_preds)
    
    # Print confusion matrix
    print("\n" + " "*15 + "  ".join([f"{name[:8]:8s}" for name in config['model']['skin_types']]))
    for i, name in enumerate(config['model']['skin_types']):
        print(f"{name[:12]:12s}  " + "  ".join([f"{cm[i, j]:8d}" for j in range(len(config['model']['skin_types']))]))
    
    # Save confusion matrix plot
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=config['model']['skin_types'],
                yticklabels=config['model']['skin_types'])
    plt.title('Confusion Matrix - Skin Types')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    
    output_dir = Path("ml/models")
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / "confusion_matrix.png", dpi=300, bbox_inches='tight')
    print(f"\nConfusion matrix saved to: {output_dir / 'confusion_matrix.png'}")
    
    # Model size
    model_size = Path(model_path).stat().st_size / (1024 * 1024)  # MB
    print(f"\nModel size: {model_size:.2f} MB")
    
    # Check if meets targets
    validation_config = config['validation']
    print("\n" + "="*80)
    print("VALIDATION TARGETS")
    print("="*80)
    
    targets_met = True
    
    if test_acc >= validation_config['min_accuracy']:
        print(f"✓ Accuracy: {test_acc:.4f} >= {validation_config['min_accuracy']} (target)")
    else:
        print(f"✗ Accuracy: {test_acc:.4f} < {validation_config['min_accuracy']} (target)")
        targets_met = False
    
    if test_prec >= validation_config['min_precision']:
        print(f"✓ Precision: {test_prec:.4f} >= {validation_config['min_precision']} (target)")
    else:
        print(f"✗ Precision: {test_prec:.4f} < {validation_config['min_precision']} (target)")
        targets_met = False
    
    if test_rec >= validation_config['min_recall']:
        print(f"✓ Recall: {test_rec:.4f} >= {validation_config['min_recall']} (target)")
    else:
        print(f"✗ Recall: {test_rec:.4f} < {validation_config['min_recall']} (target)")
        targets_met = False
    
    f1_score = 2 * (test_prec * test_rec) / (test_prec + test_rec)
    if f1_score >= validation_config['min_f1_score']:
        print(f"✓ F1-Score: {f1_score:.4f} >= {validation_config['min_f1_score']} (target)")
    else:
        print(f"✗ F1-Score: {f1_score:.4f} < {validation_config['min_f1_score']} (target)")
        targets_met = False
    
    if targets_met:
        print("\n✓ All validation targets met!")
    else:
        print("\n✗ Some validation targets not met. Consider retraining.")
    
    return {
        'loss': test_loss,
        'accuracy': test_acc,
        'precision': test_prec,
        'recall': test_rec,
        'f1_score': f1_score,
        'model_size_mb': model_size,
        'targets_met': targets_met
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
