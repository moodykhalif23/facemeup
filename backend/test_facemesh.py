#!/usr/bin/env python3
"""
Test script for MediaPipe Face Mesh integration
Tests face processor functionality without requiring full API setup
"""

import sys
import base64
import numpy as np
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.face_processor import face_processor


def create_dummy_image() -> str:
    """Create a dummy image for testing"""
    from PIL import Image
    import io
    
    # Create a simple test image
    img = Image.new('RGB', (640, 480), color='white')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    
    return base64.b64encode(img_bytes).decode('utf-8')


def create_dummy_landmarks() -> list:
    """Create dummy face landmarks for testing"""
    # Create 468 landmarks in a face-like pattern
    landmarks = []
    
    # Face oval (centered, reasonable size)
    center_x, center_y = 0.5, 0.5
    width, height = 0.3, 0.4
    
    for i in range(468):
        # Distribute landmarks in an oval pattern
        angle = (i / 468) * 2 * np.pi
        x = center_x + (width / 2) * np.cos(angle)
        y = center_y + (height / 2) * np.sin(angle)
        z = 0.0
        
        landmarks.append({
            'x': float(x),
            'y': float(y),
            'z': float(z)
        })
    
    return landmarks


def test_face_quality_score():
    """Test face quality scoring"""
    print("Testing face quality score...")
    
    # Test with centered face
    centered_landmarks = create_dummy_landmarks()
    score = face_processor.get_face_quality_score(centered_landmarks)
    print(f"✓ Centered face quality score: {score:.4f}")
    
    # Test with off-center face
    off_center_landmarks = [
        {'x': lm['x'] + 0.2, 'y': lm['y'], 'z': lm['z']}
        for lm in centered_landmarks
    ]
    off_center_score = face_processor.get_face_quality_score(off_center_landmarks)
    print(f"✓ Off-center face quality score: {off_center_score:.4f}")
    
    # Test with small face
    small_landmarks = [
        {'x': 0.5 + (lm['x'] - 0.5) * 0.5, 'y': 0.5 + (lm['y'] - 0.5) * 0.5, 'z': lm['z']}
        for lm in centered_landmarks
    ]
    small_score = face_processor.get_face_quality_score(small_landmarks)
    print(f"✓ Small face quality score: {small_score:.4f}")
    
    # Test with no landmarks
    empty_score = face_processor.get_face_quality_score([])
    print(f"✓ Empty landmarks quality score: {empty_score:.4f}")
    
    assert score > off_center_score, "Centered face should have higher score"
    assert score > small_score, "Larger face should have higher score"
    assert empty_score == 0.0, "Empty landmarks should return 0"
    
    print("✓ All quality score tests passed!\n")


def test_face_features():
    """Test face feature extraction"""
    print("Testing face feature extraction...")
    
    landmarks = create_dummy_landmarks()
    features = face_processor.extract_face_features(landmarks)
    
    print(f"✓ Extracted features:")
    print(f"  - Face width: {features['face_width']:.4f}")
    print(f"  - Face height: {features['face_height']:.4f}")
    print(f"  - Center X: {features['center_x']:.4f}")
    print(f"  - Center Y: {features['center_y']:.4f}")
    print(f"  - Num landmarks: {features['num_landmarks']}")
    print(f"  - Quality score: {features['quality_score']:.4f}")
    
    assert features['num_landmarks'] == 468, "Should have 468 landmarks"
    assert 0 <= features['center_x'] <= 1, "Center X should be normalized"
    assert 0 <= features['center_y'] <= 1, "Center Y should be normalized"
    
    print("✓ All feature extraction tests passed!\n")


def test_image_processing():
    """Test image processing pipeline"""
    print("Testing image processing...")
    
    base64_image = create_dummy_image()
    landmarks = create_dummy_landmarks()
    
    # Test decoding
    image = face_processor.decode_base64_image(base64_image)
    print(f"✓ Decoded image shape: {image.shape}")
    assert len(image.shape) == 3, "Image should be 3D array"
    
    # Test face extraction
    face = face_processor.extract_face_region(image, landmarks)
    print(f"✓ Extracted face shape: {face.shape}")
    assert face.size > 0, "Face region should not be empty"
    
    # Test preprocessing
    processed = face_processor.preprocess_for_model(face)
    print(f"✓ Preprocessed shape: {processed.shape}")
    assert processed.shape == (224, 224, 3), "Should be resized to model input size"
    assert processed.dtype == np.float32, "Should be float32"
    assert 0 <= processed.min() <= processed.max() <= 1, "Should be normalized to [0, 1]"
    
    # Test complete pipeline
    result = face_processor.process_image_with_landmarks(base64_image, landmarks)
    print(f"✓ Complete pipeline result shape: {result.shape}")
    assert result.shape == (224, 224, 3), "Pipeline should produce model-ready image"
    
    print("✓ All image processing tests passed!\n")


def test_fallback_processing():
    """Test processing without landmarks (fallback)"""
    print("Testing fallback processing (no landmarks)...")
    
    base64_image = create_dummy_image()
    
    # Test without landmarks
    result = face_processor.process_image_with_landmarks(base64_image, None)
    print(f"✓ Fallback processing result shape: {result.shape}")
    assert result.shape == (224, 224, 3), "Should still produce valid output"
    
    # Test with empty landmarks
    result_empty = face_processor.process_image_with_landmarks(base64_image, [])
    print(f"✓ Empty landmarks processing result shape: {result_empty.shape}")
    assert result_empty.shape == (224, 224, 3), "Should handle empty landmarks"
    
    print("✓ All fallback tests passed!\n")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("MediaPipe Face Mesh Integration Tests")
    print("=" * 60)
    print()
    
    try:
        test_face_quality_score()
        test_face_features()
        test_image_processing()
        test_fallback_processing()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
