"""
Main training script for skin analysis model.
"""

import os
import argparse
import yaml
from pathlib import Path
import tensorflow as tf
from tensorflow import keras

from data_loader import SkinDataLoader
from model_builder import SkinAnalysisModel


def train_phase(phase: int, config_path: str = "ml/config.yaml", 
                model_path: str = None):
    """
    Train model for specified phase.
    
    Args:
        phase: 1 for feature extraction, 2 for fine-tuning
        config_path: Path to config file
        model_path: Path to pre-trained model (for phase 2)
    """
    print("="*80)
    print(f"TRAINING PHASE {phase}")
    print("="*80)
    
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Get training config
    if phase == 1:
        train_config = config['training']['phase1']
    else:
        train_config = config['training']['phase2']
    
    # Create data loader
    print("\n[1/5] Loading datasets...")
    data_loader = SkinDataLoader(config_path)
    train_ds, val_ds, test_ds = data_loader.create_datasets()
    
    # Build or load model
    print("\n[2/5] Building model...")
    model_builder = SkinAnalysisModel(config_path)
    
    if phase == 2 and model_path:
        # Load Phase 1 model and rebuild for Phase 2
        print(f"Loading Phase 1 model from: {model_path}")
        model = keras.models.load_model(model_path)
        # Rebuild with Phase 2 configuration
        model = model_builder.build_model(phase=2)
        # Load weights from Phase 1
        try:
            model.load_weights(model_path)
            print("Loaded Phase 1 weights successfully")
        except Exception as e:
            print(f"Warning: Could not load Phase 1 weights: {e}")
    else:
        model = model_builder.build_model(phase=phase)
    
    # Get callbacks
    print("\n[3/5] Configuring callbacks...")
    callbacks = model_builder.get_callbacks(phase=phase)
    
    # Train model
    print("\n[4/5] Starting training...")
    print(f"Epochs: {train_config['epochs']}")
    print(f"Learning rate: {train_config['learning_rate']}")
    print(f"Freeze base: {train_config.get('freeze_base', True)}")
    print("-"*80)
    
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=train_config['epochs'],
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate on test set
    print("\n[5/5] Evaluating on test set...")
    test_results = model.evaluate(test_ds, verbose=1)
    
    print("\n" + "="*80)
    print("TRAINING COMPLETE")
    print("="*80)
    print(f"Test Loss: {test_results[0]:.4f}")
    for i, metric_name in enumerate(config['metrics'], start=1):
        print(f"Test {metric_name.capitalize()}: {test_results[i]:.4f}")
    
    # Save final model
    final_model_path = f"{config['logging']['checkpoint_dir']}/phase{phase}_final_model.h5"
    model.save(final_model_path)
    print(f"\nFinal model saved to: {final_model_path}")
    
    return model, history


def main():
    parser = argparse.ArgumentParser(description='Train skin analysis model')
    parser.add_argument('--config', type=str, default='ml/config.yaml',
                       help='Path to config file')
    parser.add_argument('--phase', type=int, choices=[1, 2], required=True,
                       help='Training phase: 1 (feature extraction) or 2 (fine-tuning)')
    parser.add_argument('--model', type=str, default=None,
                       help='Path to Phase 1 model (required for Phase 2)')
    parser.add_argument('--gpu', type=str, default='0',
                       help='GPU device ID')
    
    args = parser.parse_args()
    
    # Set GPU
    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu
    
    # Check GPU availability
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print(f"\nGPU available: {len(gpus)} device(s)")
        for gpu in gpus:
            print(f"  - {gpu}")
        # Enable memory growth
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    else:
        print("\nNo GPU available. Training on CPU.")
    
    # Validate Phase 2 requirements
    if args.phase == 2 and not args.model:
        # Try to find Phase 1 model automatically
        checkpoint_dir = Path("ml/checkpoints")
        phase1_model = checkpoint_dir / "phase1_best_model.h5"
        if phase1_model.exists():
            args.model = str(phase1_model)
            print(f"\nAutomatically found Phase 1 model: {args.model}")
        else:
            print("\nError: Phase 2 requires --model argument with Phase 1 model path")
            return
    
    # Train
    model, history = train_phase(
        phase=args.phase,
        config_path=args.config,
        model_path=args.model
    )
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    
    if args.phase == 1:
        print("Phase 1 complete! Next:")
        print("1. Review training metrics in TensorBoard:")
        print("   tensorboard --logdir ml/logs")
        print("2. Start Phase 2 fine-tuning:")
        print("   python ml/train.py --phase 2")
    else:
        print("Phase 2 complete! Next:")
        print("1. Evaluate model:")
        print("   python ml/evaluate.py --model ml/checkpoints/phase2_best_model.h5")
        print("2. Export to TFLite:")
        print("   python ml/export_tflite.py --model ml/checkpoints/phase2_best_model.h5")
        print("3. Export to SavedModel:")
        print("   python ml/export_savedmodel.py --model ml/checkpoints/phase2_best_model.h5")


if __name__ == "__main__":
    main()
