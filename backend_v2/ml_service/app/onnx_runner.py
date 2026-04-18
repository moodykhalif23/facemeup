"""Lazy-loading ONNX session registry.

Sessions are created on first access and cached. If a model file is missing
we log a warning and return None so callers can fall back gracefully.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import onnxruntime as ort

log = logging.getLogger(__name__)


class OnnxRegistry:
    def __init__(self, models_dir: Path, providers: tuple[str, ...]):
        self._dir = models_dir
        self._providers = list(providers)
        self._sessions: dict[str, ort.InferenceSession | None] = {}
        self._lock = threading.Lock()

    def get(self, filename: str) -> ort.InferenceSession | None:
        if filename in self._sessions:
            return self._sessions[filename]
        with self._lock:
            if filename in self._sessions:
                return self._sessions[filename]
            path = self._dir / filename
            if not path.is_file():
                log.warning("onnx model missing: %s (pipeline will use fallback)", path)
                self._sessions[filename] = None
                return None
            try:
                opts = ort.SessionOptions()
                opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                sess = ort.InferenceSession(str(path), sess_options=opts, providers=self._providers)
                log.info("loaded onnx model %s providers=%s", filename, sess.get_providers())
                self._sessions[filename] = sess
                return sess
            except Exception as e:
                log.error("failed to load onnx model %s: %s", path, e)
                self._sessions[filename] = None
                return None

    def loaded(self) -> dict[str, bool]:
        return {name: sess is not None for name, sess in self._sessions.items()}
