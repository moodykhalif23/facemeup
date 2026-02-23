"""
Export trained model to TensorFlow Lite format with quantization.
"""

import argparse
import yaml
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
import numpy as np


def export_to_tflite(model_path: str, output_path: str, 
                     config_path: str = "ml/config.yaml",
                     quantize: str = "int8"):
    """
    Export Keras model to TFLite format.
    
    Args:
        model_path: Path to trained Keras model
        output_path: Output path for TFLite model
        config_path: Path to config file
        quantize: Quantization type ('none', 'float16', 'int8')
    """
    
    print("="*80)
    print("EXPORTING TO TENSORFLOW LITE")
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
    
    # Convert to TFLite
    print(f"\nConverting to TFLite (quantization: {quantize})...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Set optimization flags
    if quantize == "int8":
        print("Applying INT8 quantization...")
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Representative dataset for quantization
        def representative_dataset():
            # Generate dummy data for calibration
            input_size = config['model']['input_size']
            for _ in range(100):
                data = np.random.rand(1, input_size, input_size, 3).astype(np.float32)
                yield [data]
        
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.uint8
        converter.inference_output_type = tf.uint8
        
    elif quantize == "float16":
        print("Applying FLOAT16 quantization...")
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
    
    elif quantize == "none":
        print("No quantization applied")
    
    else:
        raise ValueError(f"Unknown quantization type: {quantize}")
    
    # Convert
    tflite_model = converter.convert()
    
    # Save TFLite model
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    # Get file size
    file_size = output_path.stat().st_size / (1024 * 1024)  # MB
    
    print(f"\n✓ TFLite model saved to: {output_path}")
    print(f"✓ Model size: {file_size:.2f} MB")
    
    # Validate model
    print("\nValidating TFLite model...")
    interpreter = tf.lite.Interpreter(model_path=str(output_path))
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    print(f"✓ Input shape: {input_details[0]['shape']}")
    print(f"✓ Input dtype: {input_details[0]['dtype']}")
    print(f"✓ Output shape: {output_details[0]['shape']}")
    print(f"✓ Output dtype: {output_details[0]['dtype']}")
    
    # Test inference
    print("\nTesting inference...")
    input_size = config['model']['input_size']
    test_input = np.random.rand(1, input_size, input_size, 3).astype(np.float32)
    
    if quantize == "int8":
        # Scale input for INT8
        test_input = (test_input * 255).astype(np.uint8)
    
    interpreter.set_tensor(input_details[0]['index'], test_input)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])
    
    print(f"✓ Inference successful")
    print(f"✓ Output shape: {output.shape}")
    print(f"✓ Output range: [{output.min():.3f}, {output.max():.3f}]")
    
    # Check size target
    target_size = 5.0  # MB
    if file_size <= target_size:
        print(f"\n✓ Model size ({file_size:.2f} MB) meets target (<= {target_size} MB)")
    else:
        print(f"\n✗ Model size ({file_size:.2f} MB) exceeds target (<= {target_size} MB)")
        print("  Consider using INT8 quantization or a smaller base model")
    
    return output_path, file_size


def main():
    parser = argparse.ArgumentParser(description='Export model to TFLite')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained Keras model')
    parser.add_argument('--output', type=str, default='app/models_artifacts/model.tflite',
                       help='Output path for TFLite model')
    parser.add_argument('--config', type=str, default='ml/config.yaml',
                       help='Path to config file')
    parser.add_argument('--quantize', type=str, default='int8',
                       choices=['none', 'float16', 'int8'],
                       help='Quantization type')
    
    args = parser.parse_args()
    
    output_path, file_size = export_to_tflite(
        args.model,
        args.output,
        args.config,
        args.quantize
    )
    
    print("\n" + "="*80)
    print("EXPORT COMPLETE")
    print("="*80)
    print(f"\nTFLite model ready for mobile deployment!")
    print(f"Location: {output_path}")
    print(f"Size: {file_size:.2f} MB")
    
    print("\nNext steps:")
    print("1. Copy TFLite model to frontend:")
    print(f"   cp {output_path} ../frontend/assets/model.tflite")
    print("2. Integrate with React Native app")
    print("3. Test on-device inference")


if __name__ == "__main__":
    main()
