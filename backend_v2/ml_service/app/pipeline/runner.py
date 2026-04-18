"""End-to-end preprocessing orchestrator.

Input:  base64 image + optional client landmarks + questionnaire dict
Output: aligned face, skin mask, 5 patches, classifier input tensor, metadata
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from ..config import Settings
from ..onnx_runner import OnnxRegistry
from .align import align_face
from .decode import decode_base64_image
from .detect import Detection, detect
from .normalize import normalize
from .patches import Patch, extract_patches
from .segment import segment_skin


@dataclass
class PipelineResult:
    detection: Detection
    aligned: np.ndarray           # (S, S, 3) BGR
    normalized: np.ndarray        # (S, S, 3) BGR after CLAHE + WB
    skin_mask: np.ndarray         # (S, S) uint8 0/255
    patches: list[Patch]
    meta: dict = field(default_factory=dict)


class SkinPipeline:
    """Composed pipeline. Cheap to construct; ONNX sessions load lazily on first call."""

    def __init__(self, settings: Settings, registry: OnnxRegistry, aligned_size: int = 256):
        self._settings = settings
        self._registry = registry
        self._aligned_size = aligned_size

    def run(self, image_b64: str, client_landmarks: list[dict] | None = None) -> PipelineResult:
        image = decode_base64_image(image_b64)

        retinaface = self._registry.get(self._settings.face_detector_model)
        det = detect(image, client_landmarks=client_landmarks, retinaface_session=retinaface)
        if det is None:
            raise NoFaceFoundError("no face detected in image")

        aligned = align_face(image, det.landmarks, size=self._aligned_size)
        normalized = normalize(aligned)

        segmenter = self._registry.get(self._settings.segmenter_model)
        skin_mask = segment_skin(normalized, onnx_session=segmenter)

        patches = extract_patches(normalized, skin_mask, patch_size=self._settings.input_size)

        meta = {
            "source": det.source,
            "bbox": det.bbox,
            "patch_regions": [p.region for p in patches],
            "retinaface_loaded": retinaface is not None,
            "segmenter_loaded": segmenter is not None,
        }
        return PipelineResult(
            detection=det,
            aligned=aligned,
            normalized=normalized,
            skin_mask=skin_mask,
            patches=patches,
            meta=meta,
        )

    def build_classifier_batch(self, patches: list[Patch]) -> np.ndarray:
        """Stack patches into an ImageNet-normalised (N, 3, H, W) float32 tensor."""
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        tensors = []
        for p in patches:
            rgb = cv2.cvtColor(p.image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            tensors.append(((rgb - mean) / std).transpose(2, 0, 1))
        return np.stack(tensors).astype(np.float32) if tensors else np.empty((0, 3, 1, 1), np.float32)


class NoFaceFoundError(ValueError):
    """Raised when no face could be detected or localised from landmarks."""
