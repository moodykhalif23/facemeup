"""
Custom Keras losses – registered for model serialization.

Import this module in every script that calls keras.models.load_model()
so that @register_keras_serializable runs before the checkpoint is read.
"""
import numpy as np
import tensorflow as tf
from tensorflow import keras


@tf.keras.utils.register_keras_serializable(package="skincare")
class WeightedBCE(keras.losses.Loss):
    """Weighted binary cross-entropy with per-output positive weights and label smoothing.

    pos_weights     – 1-D array, length = NUM_CLASSES.
                      Each output i is weighted by neg_count_i / pos_count_i
                      (clipped to [1, 50]) so rare conditions receive stronger
                      gradient signal than majority-class outputs.
    label_smoothing – float (default 0.05). Smooths targets toward 0.5 to
                      reduce over-confident predictions on noisy labels.
    """

    def __init__(self, pos_weights, label_smoothing: float = 0.05, **kwargs):
        super().__init__(**kwargs)
        self.pos_weights = np.asarray(pos_weights, dtype=np.float32)
        self.label_smoothing = float(label_smoothing)

    def call(self, y_true, y_pred):
        pos_weights = tf.constant(self.pos_weights, dtype=tf.float32)
        eps = 1e-7
        y_pred = tf.clip_by_value(y_pred, eps, 1.0 - eps)
        smooth = self.label_smoothing
        y_true_s = y_true * (1.0 - smooth) + 0.5 * smooth
        loss = -(
            pos_weights * y_true_s * tf.math.log(y_pred)
            + (1.0 - y_true_s) * tf.math.log(1.0 - y_pred)
        )
        return tf.reduce_mean(loss)

    def get_config(self):
        config = super().get_config()
        config.update({
            "pos_weights": self.pos_weights.tolist(),
            "label_smoothing": self.label_smoothing,
        })
        return config

    @classmethod
    def from_config(cls, config):
        config["pos_weights"] = np.asarray(config["pos_weights"], dtype=np.float32)
        return cls(**config)
