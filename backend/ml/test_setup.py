"""
Test ML setup and verify all dependencies are installed correctly.
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...")
    print("-" * 80)
    
    tests = []
    
    # TensorFlow
    try:
        import tensorflow as tf
        print(f"✓ TensorFlow {tf.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ TensorFlow: {e}")
        tests.append(False)
    
    # Keras
    try:
        import keras
        print(f"✓ Keras {keras.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ Keras: {e}")
        tests.append(False)
    
    # NumPy
    try:
        import numpy as np
        print(f"✓ NumPy {np.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ NumPy: {e}")
        tests.append(False)
    
    # PIL
    try:
        import PIL
        print(f"✓ Pillow {PIL.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ Pillow: {e}")
        tests.append(False)
    
    # scikit-learn
    try:
        import sklearn
        print(f"✓ scikit-learn {sklearn.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ scikit-learn: {e}")
        tests.append(False)
    
    # matplotlib
    try:
        import matplotlib
        print(f"✓ matplotlib {matplotlib.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ matplotlib: {e}")
        tests.append(False)
    
    # seaborn
    try:
        import seaborn as sns
        print(f"✓ seaborn {sns.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ seaborn: {e}")
        tests.append(False)
    
    # PyYAML
    try:
        import yaml
        print(f"✓ PyYAML {yaml.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"✗ PyYAML: {e}")
        tests.append(False)
    
    # TensorFlow Datasets (optional)
    try:
        import tensorflow_datasets as tfds
        print(f"✓ TensorFlow Datasets {tfds.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"⚠ TensorFlow Datasets: {e} (optional)")
        # Don't fail on this one
    
    return all(tests)


def test_gpu():
    """Test GPU availability."""
    print("\nTesting GPU...")
    print("-" * 80)
    
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        
        if gpus:
            print(f"✓ GPU available: {len(gpus)} device(s)")
            for i, gpu in enumerate(gpus):
                print(f"  GPU {i}: {gpu}")
            return True
        else:
            print("⚠ No GPU available. Training will use CPU (slower).")
            return True
    except Exception as e:
        print(f"✗ Error checking GPU: {e}")
        return False


def test_directories():
    """Test that required directories exist."""
    print("\nTesting directories...")
    print("-" * 80)
    
    required_dirs = [
        "ml/data/isic",
        "ml/data/bitmoji",
        "ml/data/processed",
        "ml/models",
        "ml/checkpoints",
        "ml/logs",
        "ml/scripts",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} (missing)")
            all_exist = False
    
    return all_exist


def test_config():
    """Test that config file exists and is valid."""
    print("\nTesting configuration...")
    print("-" * 80)
    
    config_path = Path("ml/config.yaml")
    
    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        return False
    
    print(f"✓ Config file exists: {config_path}")
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['model', 'dataset', 'training', 'architecture', 'loss', 'metrics']
        for section in required_sections:
            if section in config:
                print(f"✓ Config section: {section}")
            else:
                print(f"✗ Missing config section: {section}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return False


def test_scripts():
    """Test that all required scripts exist."""
    print("\nTesting scripts...")
    print("-" * 80)
    
    required_scripts = [
        "ml/data_loader.py",
        "ml/model_builder.py",
        "ml/train.py",
        "ml/evaluate.py",
        "ml/export_tflite.py",
        "ml/export_savedmodel.py",
        "ml/scripts/download_isic.py",
    ]
    
    all_exist = True
    for script_path in required_scripts:
        path = Path(script_path)
        if path.exists():
            print(f"✓ {script_path}")
        else:
            print(f"✗ {script_path} (missing)")
            all_exist = False
    
    return all_exist


def test_data_loader():
    """Test data loader."""
    print("\nTesting data loader...")
    print("-" * 80)
    
    try:
        from data_loader import SkinDataLoader
        
        loader = SkinDataLoader()
        print(f"✓ Data loader initialized")
        print(f"  - Image size: {loader.image_size}")
        print(f"  - Batch size: {loader.batch_size}")
        print(f"  - Num classes: {loader.num_classes}")
        print(f"  - Skin types: {loader.skin_types}")
        print(f"  - Conditions: {loader.conditions}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing data loader: {e}")
        return False


def test_model_builder():
    """Test model builder."""
    print("\nTesting model builder...")
    print("-" * 80)
    
    try:
        from model_builder import SkinAnalysisModel
        
        builder = SkinAnalysisModel()
        print(f"✓ Model builder initialized")
        print(f"  - Input size: {builder.input_size}")
        print(f"  - Num classes: {builder.num_classes}")
        print(f"  - Skin types: {builder.num_skin_types}")
        print(f"  - Conditions: {builder.num_conditions}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing model builder: {e}")
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("ML SETUP TEST")
    print("="*80)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("GPU", test_gpu()))
    results.append(("Directories", test_directories()))
    results.append(("Configuration", test_config()))
    results.append(("Scripts", test_scripts()))
    results.append(("Data Loader", test_data_loader()))
    results.append(("Model Builder", test_model_builder()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} {name}")
    
    print("-"*80)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! ML pipeline is ready.")
        print("\nNext steps:")
        print("1. Download ISIC dataset:")
        print("   python ml/scripts/download_isic.py")
        print("2. Start training:")
        print("   python ml/train.py --phase 1")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Install dependencies:")
        print("   pip install -r requirements.txt")
        print("2. Create missing directories:")
        print("   mkdir -p ml/data/isic ml/models ml/checkpoints ml/logs")
        return 1


if __name__ == "__main__":
    sys.exit(main())
