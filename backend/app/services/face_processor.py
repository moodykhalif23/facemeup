import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import base64


class FaceLandmark:
    """Represents a single face landmark point"""
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


class FaceProcessor:
    """Process face images with MediaPipe landmarks"""
    
    def __init__(self):
        self.padding = 0.2  # 20% padding around face
        self.target_size = (224, 224)  # Model input size
    
    def extract_face_region(
        self, 
        image: np.ndarray, 
        landmarks: Optional[List[Dict]] = None
    ) -> np.ndarray:
        """
        Extract and normalize face region from landmarks
        
        Args:
            image: Input image as numpy array
            landmarks: List of landmark dicts with x, y, z coordinates (normalized 0-1)
        
        Returns:
            Cropped and normalized face region
        """
        if landmarks is None or len(landmarks) == 0:
            # No landmarks - use center crop
            return self._center_crop(image)
        
        # Convert landmarks to FaceLandmark objects
        face_landmarks = [
            FaceLandmark(lm['x'], lm['y'], lm.get('z', 0.0)) 
            for lm in landmarks
        ]
        
        # Get face bounding box
        x_coords = [lm.x for lm in face_landmarks]
        y_coords = [lm.y for lm in face_landmarks]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Add padding
        width = x_max - x_min
        height = y_max - y_min
        
        x_min = max(0, x_min - width * self.padding)
        x_max = min(1, x_max + width * self.padding)
        y_min = max(0, y_min - height * self.padding)
        y_max = min(1, y_max + height * self.padding)
        
        # Convert to pixel coordinates
        h, w = image.shape[:2]
        x1, x2 = int(x_min * w), int(x_max * w)
        y1, y2 = int(y_min * h), int(y_max * h)
        
        # Crop face region
        face = image[y1:y2, x1:x2]
        
        # Ensure we got a valid crop
        if face.size == 0:
            return self._center_crop(image)
        
        return face
    
    def _center_crop(self, image: np.ndarray) -> np.ndarray:
        """Fallback: center crop if no landmarks available"""
        h, w = image.shape[:2]
        size = min(h, w)
        
        y1 = (h - size) // 2
        x1 = (w - size) // 2
        
        return image[y1:y1+size, x1:x1+size]
    
    def preprocess_for_model(self, face_image: np.ndarray) -> np.ndarray:
        """
        Preprocess face image for model input
        
        Args:
            face_image: Cropped face region
        
        Returns:
            Preprocessed image ready for model
        """
        # Resize to model input size
        resized = cv2.resize(face_image, self.target_size, interpolation=cv2.INTER_AREA)
        
        # Convert to RGB if needed
        if len(resized.shape) == 2:
            resized = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
        elif resized.shape[2] == 4:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGRA2RGB)
        
        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        return normalized
    
    def decode_base64_image(self, base64_string: str) -> np.ndarray:
        """Decode base64 image string to numpy array"""
        img_bytes = base64.b64decode(base64_string)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")
        
        return image
    
    def process_image_with_landmarks(
        self, 
        base64_image: str, 
        landmarks: Optional[List[Dict]] = None
    ) -> np.ndarray:
        """
        Complete pipeline: decode, extract face, preprocess
        
        Args:
            base64_image: Base64 encoded image string
            landmarks: Optional face landmarks from MediaPipe
        
        Returns:
            Preprocessed image ready for model inference
        """
        # Decode image
        image = self.decode_base64_image(base64_image)
        
        # Extract face region
        face = self.extract_face_region(image, landmarks)
        
        # Preprocess for model
        processed = self.preprocess_for_model(face)
        
        return processed
    
    def get_face_quality_score(self, landmarks: List[Dict]) -> float:
        """
        Calculate quality score based on face landmarks
        Higher score = better quality for analysis
        
        Args:
            landmarks: Face landmarks from MediaPipe
        
        Returns:
            Quality score between 0 and 1
        """
        if not landmarks or len(landmarks) < 468:
            return 0.0
        
        # Convert to FaceLandmark objects
        face_landmarks = [
            FaceLandmark(lm['x'], lm['y'], lm.get('z', 0.0)) 
            for lm in landmarks
        ]
        
        # Check face size (larger is better)
        x_coords = [lm.x for lm in face_landmarks]
        y_coords = [lm.y for lm in face_landmarks]
        
        face_width = max(x_coords) - min(x_coords)
        face_height = max(y_coords) - min(y_coords)
        
        size_score = min(1.0, (face_width + face_height) / 1.0)
        
        # Check face centering
        center_x = (max(x_coords) + min(x_coords)) / 2
        center_y = (max(y_coords) + min(y_coords)) / 2
        
        center_score = 1.0 - abs(center_x - 0.5) - abs(center_y - 0.5)
        center_score = max(0.0, center_score)
        
        # Combined score
        quality_score = (size_score * 0.6 + center_score * 0.4)
        
        return quality_score
    
    def extract_face_features(self, landmarks: List[Dict]) -> Dict:
        """
        Extract useful features from face landmarks
        
        Args:
            landmarks: Face landmarks from MediaPipe
        
        Returns:
            Dictionary of extracted features
        """
        if not landmarks:
            return {}
        
        face_landmarks = [
            FaceLandmark(lm['x'], lm['y'], lm.get('z', 0.0)) 
            for lm in landmarks
        ]
        
        # Calculate face dimensions
        x_coords = [lm.x for lm in face_landmarks]
        y_coords = [lm.y for lm in face_landmarks]
        
        features = {
            'face_width': max(x_coords) - min(x_coords),
            'face_height': max(y_coords) - min(y_coords),
            'center_x': (max(x_coords) + min(x_coords)) / 2,
            'center_y': (max(y_coords) + min(y_coords)) / 2,
            'num_landmarks': len(landmarks),
            'quality_score': self.get_face_quality_score(landmarks)
        }
        
        return features


# Global instance
face_processor = FaceProcessor()
