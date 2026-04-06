"""Grad-CAM heatmap generation for skin condition visualisation (spec §7).

Grad-CAM highlights which regions of the input image the model focused on
when predicting each skin condition, improving user trust and regulatory
transparency.

Usage::
    from app.services.gradcam import generate_gradcam_overlay
    heatmap_b64 = generate_gradcam_overlay(model, image_array, class_index)
"""

import base64
import io
import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Name of the last convolutional block in EfficientNetB0.
# Grad-CAM is applied at this layer to capture high-level spatial features.
_EFFICIENTNET_LAST_CONV = "top_conv"


def _get_gradcam_heatmap(
    model,
    image_array: np.ndarray,
    class_index: int,
    last_conv_layer_name: str = _EFFICIENTNET_LAST_CONV,
) -> Optional[np.ndarray]:
    """Compute Grad-CAM heatmap for a given class index.

    Args:
        model:               Loaded Keras model (EfficientNetB0 backbone).
        image_array:         Pre-processed input [1, H, W, 3] float32 in [0, 1].
        class_index:         Output neuron index to explain.
        last_conv_layer_name: Name of the last conv layer to hook gradients.

    Returns:
        Normalised heatmap array [H, W] in [0, 1], or None if the layer
        is not found or TF is unavailable.
    """
    try:
        import tensorflow as tf

        # Build a sub-model that outputs (last_conv_output, predictions)
        try:
            last_conv_layer = model.get_layer(last_conv_layer_name)
        except ValueError:
            # Fall back: find the last Conv2D layer by type
            last_conv_layer = None
            for layer in reversed(model.layers):
                if isinstance(layer, tf.keras.layers.Conv2D):
                    last_conv_layer = layer
                    break
            if last_conv_layer is None:
                logger.warning("Grad-CAM: no Conv2D layer found in model")
                return None

        grad_model = tf.keras.Model(
            inputs=model.inputs,
            outputs=[last_conv_layer.output, model.output],
        )

        with tf.GradientTape() as tape:
            inputs = tf.cast(image_array, tf.float32)
            conv_outputs, predictions = grad_model(inputs)
            loss = predictions[:, class_index]

        # Gradients of the class score w.r.t. the conv feature maps
        grads = tape.gradient(loss, conv_outputs)  # [1, h, w, filters]

        # Pool gradients over spatial dimensions → per-filter importance weights
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))  # [filters]

        # Weight the conv output channels by the pooled gradients
        conv_outputs = conv_outputs[0]  # [h, w, filters]
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]  # [h, w, 1]
        heatmap = tf.squeeze(heatmap)  # [h, w]

        # ReLU — we only care about features that increase the class score
        heatmap = tf.nn.relu(heatmap).numpy()

        # Normalise to [0, 1]
        max_val = heatmap.max()
        if max_val > 0:
            heatmap /= max_val

        return heatmap.astype(np.float32)

    except Exception as exc:
        logger.warning("Grad-CAM computation failed: %s", exc)
        return None


def generate_gradcam_overlay(
    model,
    image_array: np.ndarray,
    class_index: int,
    alpha: float = 0.4,
) -> Optional[str]:
    """Produce a base64-encoded JPEG of the Grad-CAM overlay on the input image.

    Args:
        model:        Loaded Keras/TF model.
        image_array:  Pre-processed input [1, H, W, 3] float32 in [0, 1].
        class_index:  Output neuron to visualise (e.g. index of "Acne").
        alpha:        Heatmap blend strength (0 = image only, 1 = heatmap only).

    Returns:
        Base64-encoded JPEG string (data URI prefix NOT included), or None.
    """
    heatmap = _get_gradcam_heatmap(model, image_array, class_index)
    if heatmap is None:
        return None

    # Recover uint8 RGB image from preprocessed float array
    img_uint8 = (image_array[0] * 255).astype(np.uint8)
    h, w = img_uint8.shape[:2]

    # Resize heatmap to match input image dimensions
    heatmap_resized = cv2.resize(heatmap, (w, h))

    # Apply colour map (COLORMAP_JET: blue=cold / red=hot)
    heatmap_colored = cv2.applyColorMap(
        (heatmap_resized * 255).astype(np.uint8), cv2.COLORMAP_JET
    )
    heatmap_rgb = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

    # Blend heatmap onto original image
    overlay = (img_uint8 * (1 - alpha) + heatmap_rgb * alpha).clip(0, 255).astype(np.uint8)

    # Encode to JPEG base64
    success, buffer = cv2.imencode(".jpg", cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not success:
        return None

    return base64.b64encode(buffer).decode("utf-8")


def generate_condition_heatmaps(
    model,
    image_array: np.ndarray,
    skin_labels: list[str],
    condition_labels: list[str],
    condition_scores: dict[str, float],
    threshold: float = 0.35,
) -> dict[str, str]:
    """Generate Grad-CAM overlays for all detected conditions above threshold.

    Returns a dict of condition_name → base64 JPEG string.
    Only conditions with score >= threshold are included to avoid
    generating heatmaps for irrelevant classes.
    """
    heatmaps: dict[str, str] = {}
    n_skin = len(skin_labels)

    for i, cond in enumerate(condition_labels):
        if cond == "None detected":
            continue
        score = condition_scores.get(cond, 0.0)
        if score < threshold:
            continue

        class_index = n_skin + i
        overlay = generate_gradcam_overlay(model, image_array, class_index)
        if overlay:
            heatmaps[cond] = overlay

    return heatmaps
