"""
Export trained model to TensorFlow SavedModel format for backend deployment.
"""

import argparse
import yaml
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
import numpy as np
import losses  # noqa: F401 – registers WeightedBCE before load_model


def export_to_savedmodel(model_path: str, output_dir: str,
                         config_path: str = "ml/config.yaml"):
    """
    Export Keras model to SavedModel format.
    
    Args:
        model_path: Path to trained Keras model
        output_dir: Output directory for SavedModel
        config_path: Path to config file
    """
    
    print("="*80)
    print("EXPORTING TO SAVEDMODEL")
    print("="*80)
    
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Load model
    print(f"\nLoading model from: {model_path}")
    model = keras.models.load_model(model_path)
    print("Model loaded successfully")
    
    # Print model info
    print(f"\nModel input shape: {model.input_shape}")
    print(f"Model output shape: {model.output_shape}")
    print(f"Model parameters: {model.count_params():,}")
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as SavedModel
    print(f"\nSaving SavedModel to: {output_dir}")
    model.save(output_dir, save_format='tf')
    
    # Calculate directory size
    total_size = sum(f.stat().st_size for f in output_dir.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    print(f"✓ SavedModel saved successfully")
    print(f"✓ Total size: {size_mb:.2f} MB")
    
    # Validate SavedModel
    print("\nValidating SavedModel...")
    loaded_model = tf.saved_model.load(str(output_dir))
    
    # Get inference function
    infer = loaded_model.signatures.get('serving_default')
    if infer is None:
        print("✗ Warning: No 'serving_default' signature found")
    else:
        print("✓ 'serving_default' signature found")
        
        # Get input/output info
        input_signature = infer.structured_input_signature
        output_signature = infer.structured_outputs
        
        print(f"✓ Input signature: {input_signature}")
        print(f"✓ Output signature: {output_signature}")
    
    # Test inference
    print("\nTesting inference...")
    input_size = config['model']['input_size']
    test_input = np.random.rand(1, input_size, input_size, 3).astype(np.float32)
    
    if infer:
        # Get input key
        input_args = infer.structured_input_signature[1]
        if input_args:
            input_key = next(iter(input_args.keys()))
            tensor = tf.convert_to_tensor(test_input, dtype=tf.float32)
            outputs = infer(**{input_key: tensor})
            
            # Get output
            output_values = list(outputs.values())
            if output_values:
                output = output_values[0].numpy()
                print(f"✓ Inference successful")
                print(f"✓ Output shape: {output.shape}")
                print(f"✓ Output range: [{output.min():.3f}, {output.max():.3f}]")
            else:
                print("✗ No output from inference")
        else:
            print("✗ Could not determine input key")
    
    # List files
    print("\nSavedModel structure:")
    for item in sorted(output_dir.rglob('*')):
        if item.is_file():
            rel_path = item.relative_to(output_dir)
            file_size = item.stat().st_size / 1024  # KB
            print(f"  {rel_path} ({file_size:.1f} KB)")
    
    return output_dir, size_mb


def main():
    parser = argparse.ArgumentParser(description='Export model to SavedModel')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained Keras model')
    parser.add_argument('--output', type=str, default='app/models_artifacts/saved_model',
                       help='Output directory for SavedModel')
    parser.add_argument('--config', type=str, default='ml/config.yaml',
                       help='Path to config file')
    
    args = parser.parse_args()
    
    output_dir, size_mb = export_to_savedmodel(
        args.model,
        args.output,
        args.config
    )
    
    print("\n" + "="*80)
    print("EXPORT COMPLETE")
    print("="*80)
    print(f"\nSavedModel ready for backend deployment!")
    print(f"Location: {output_dir}")
    print(f"Size: {size_mb:.2f} MB")
    
    print("\nNext steps:")
    print("1. Update backend config:")
    print(f"   MODEL_SAVED_PATH={output_dir}")
    print("2. Restart backend server")
    print("3. Test inference via API")


if __name__ == "__main__":
    main()
