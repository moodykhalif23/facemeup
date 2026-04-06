import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import base64


# MediaPipe Face Mesh landmark indices for key features
# These are stable across MediaPipe versions
_LM_LEFT_EYE_CENTER = 33    # left eye outer corner (from viewer's perspective)
_LM_RIGHT_EYE_CENTER = 263  # right eye outer corner
_LM_NOSE_TIP = 1
_LM_MOUTH_LEFT = 61
_LM_MOUTH_RIGHT = 291


class FaceLandmark:
    """Represents a single face landmark point"""
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


class FaceProcessor:
    """Process face images with MediaPipe landmarks.

    Pipeline (per the spec):
      1. Face alignment  — rotate image so eyes are horizontal
      2. Illumination normalization — CLAHE + white-balance correction in LAB space
      3. Face extraction  — crop bounding box with padding
      4. Resize + normalize — model-ready float32 array
    """

    def __init__(self):
        self.padding = 0.2        # 20% padding around face bounding box
        self.target_size = (224, 224)

    # ------------------------------------------------------------------
    # 1.  Illumination normalization (spec §3.3)
    # ------------------------------------------------------------------
    def normalize_illumination(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE + grey-world white-balance in LAB colour space.

        This is the single biggest quality improvement for skin-AI models.
        - Converts BGR → LAB
        - Applies CLAHE only to the L (luminance) channel to improve contrast
          without amplifying colour noise (Contrast Limited AHE)
        - Grey-world white-balance on A and B channels to remove colour casts
          from phone sensors / mixed lighting
        - Converts back to BGR
        """
        if image is None or image.size == 0:
            return image

        # BGR → LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)

        # CLAHE on L channel only (clip_limit=2.0 keeps noise under control)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_eq = clahe.apply(l_ch)

        # Grey-world white balance: shift A and B channels toward neutral 128
        a_mean = float(np.mean(a_ch))
        b_mean = float(np.mean(b_ch))
        a_shift = int((128 - a_mean) * 0.5)
        b_shift = int((128 - b_mean) * 0.5)
        a_balanced = np.clip(a_ch.astype(np.int32) + a_shift, 0, 255).astype(np.uint8)
        b_balanced = np.clip(b_ch.astype(np.int32) + b_shift, 0, 255).astype(np.uint8)

        # Merge back and convert LAB → BGR
        lab_eq = cv2.merge([l_eq, a_balanced, b_balanced])
        return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)

    # ------------------------------------------------------------------
    # 2.  Face alignment (spec §3.2)
    # ------------------------------------------------------------------
    def align_face(self, image: np.ndarray, landmarks: List[Dict]) -> np.ndarray:
        """Rotate image so that the eye-line is horizontal.

        Uses left-eye and right-eye landmark indices to compute the angle
        between the two eye centres, then rotates the whole image around
        its centre to correct head-tilt bias.
        """
        if not landmarks or len(landmarks) <= max(_LM_LEFT_EYE_CENTER, _LM_RIGHT_EYE_CENTER):
            return image

        h, w = image.shape[:2]
        lm = landmarks

        lx = lm[_LM_LEFT_EYE_CENTER]['x'] * w
        ly = lm[_LM_LEFT_EYE_CENTER]['y'] * h
        rx = lm[_LM_RIGHT_EYE_CENTER]['x'] * w
        ry = lm[_LM_RIGHT_EYE_CENTER]['y'] * h

        dx = rx - lx
        dy = ry - ly
        angle = float(np.degrees(np.arctan2(dy, dx)))

        # Only correct if angle is meaningful (> 1°) and not extreme (> 30° = bad detection)
        if abs(angle) < 1.0 or abs(angle) > 30.0:
            return image

        center = (w / 2.0, h / 2.0)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        aligned = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_REFLECT_101)
        return aligned

    # ------------------------------------------------------------------
    # 3.  Face region extraction (spec §3.4 + §4)
    # ------------------------------------------------------------------
    def extract_face_region(
        self,
        image: np.ndarray,
        landmarks: Optional[List[Dict]] = None,
    ) -> np.ndarray:
        """Crop the face bounding box (with padding) from landmark coordinates."""
        if landmarks is None or len(landmarks) == 0:
            return self._center_crop(image)

        x_coords = [lm['x'] for lm in landmarks]
        y_coords = [lm['y'] for lm in landmarks]

        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        width  = x_max - x_min
        height = y_max - y_min

        x_min = max(0.0, x_min - width  * self.padding)
        x_max = min(1.0, x_max + width  * self.padding)
        y_min = max(0.0, y_min - height * self.padding)
        y_max = min(1.0, y_max + height * self.padding)

        h, w = image.shape[:2]
        x1, x2 = int(x_min * w), int(x_max * w)
        y1, y2 = int(y_min * h), int(y_max * h)

        face = image[y1:y2, x1:x2]
        if face.size == 0:
            return self._center_crop(image)
        return face

    def _center_crop(self, image: np.ndarray) -> np.ndarray:
        """Fallback: square center crop when no landmarks are available."""
        h, w = image.shape[:2]
        size = min(h, w)
        y1 = (h - size) // 2
        x1 = (w - size) // 2
        return image[y1:y1 + size, x1:x1 + size]

    # ------------------------------------------------------------------
    # 4.  Resize + normalize
    # ------------------------------------------------------------------
    def preprocess_for_model(self, face_image: np.ndarray) -> np.ndarray:
        """Resize to target size, ensure RGB channel order, normalize to [0, 1]."""
        resized = cv2.resize(face_image, self.target_size, interpolation=cv2.INTER_AREA)

        if len(resized.shape) == 2:
            resized = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
        elif resized.shape[2] == 4:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGRA2RGB)
        else:
            # OpenCV loads as BGR; model expects RGB
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        return resized.astype(np.float32) / 255.0

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def decode_base64_image(self, base64_string: str) -> np.ndarray:
        """Decode base64 image string to numpy array (BGR)."""
        img_bytes = base64.b64decode(base64_string)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image")
        return image

    def process_image_with_landmarks(
        self,
        base64_image: str,
        landmarks: Optional[List[Dict]] = None,
    ) -> np.ndarray:
        """Full preprocessing pipeline: decode → align → normalise → crop → resize.

        Steps per spec:
          §3.1  Face detection   — handled by MediaPipe on the frontend
          §3.2  Face alignment   — rotate to horizontal eye-line
          §3.3  Illumination     — CLAHE + grey-world white balance in LAB space
          §3.4  Skin segmentation — (U-Net not yet integrated; landmark crop used)
          §4    Patch extraction — bounding-box crop of full face region
        """
        image = self.decode_base64_image(base64_image)

        # Step 1: align face orientation using eye landmarks
        if landmarks:
            image = self.align_face(image, landmarks)

        # Step 2: illumination normalization (CLAHE + white balance)
        image = self.normalize_illumination(image)

        # Step 3: crop face region
        face = self.extract_face_region(image, landmarks)

        # Step 4: resize + normalize for model
        return self.preprocess_for_model(face)
    
    def get_face_quality_score(self, landmarks: List[Dict]) -> float:
        """Quality score 0–1 based on face size and centering in frame."""
        if not landmarks or len(landmarks) < 468:
            return 0.0

        x_coords = [lm['x'] for lm in landmarks]
        y_coords = [lm['y'] for lm in landmarks]

        face_width  = max(x_coords) - min(x_coords)
        face_height = max(y_coords) - min(y_coords)
        size_score  = min(1.0, (face_width + face_height) / 1.0)

        center_x = (max(x_coords) + min(x_coords)) / 2
        center_y = (max(y_coords) + min(y_coords)) / 2
        center_score = max(0.0, 1.0 - abs(center_x - 0.5) - abs(center_y - 0.5))

        return size_score * 0.6 + center_score * 0.4

    def extract_face_features(self, landmarks: List[Dict]) -> Dict:
        """Return a dict of face geometry features extracted from landmarks."""
        if not landmarks:
            return {}

        x_coords = [lm['x'] for lm in landmarks]
        y_coords = [lm['y'] for lm in landmarks]

        return {
            'face_width':    max(x_coords) - min(x_coords),
            'face_height':   max(y_coords) - min(y_coords),
            'center_x':      (max(x_coords) + min(x_coords)) / 2,
            'center_y':      (max(y_coords) + min(y_coords)) / 2,
            'num_landmarks': len(landmarks),
            'quality_score': self.get_face_quality_score(landmarks),
        }


# Global instance
face_processor = FaceProcessor()
