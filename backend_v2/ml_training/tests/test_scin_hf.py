"""Tests for the HuggingFace SCIN loader helpers."""

from __future__ import annotations

import sys
from types import SimpleNamespace

from PIL import Image

from skin_training.data.sources import scin_hf


class _FakeDataset:
    def __init__(self, rows, features):
        self._rows = rows
        self.features = features

    def __iter__(self):
        return iter(self._rows)


def test_row_to_bytes_accepts_decoded_pil_image():
    image = Image.new("RGB", (4, 4), color="red")

    data = scin_hf._row_to_bytes(image, "google/scin", token=None)

    assert isinstance(data, bytes)
    assert len(data) > 0


def test_load_scin_hf_respects_all_body_parts(monkeypatch):
    rows = [{
        "case_id": "123",
        "image_1_path": Image.new("RGB", (2, 2), color="blue"),
        "body_parts_face": False,
        "dermatologist_skin_condition_on_label_name": "acne vulgaris",
        "fitzpatrick_skin_type": "3",
    }]
    fake = _FakeDataset(rows, {
        "case_id": object(),
        "image_1_path": object(),
        "body_parts_face": object(),
        "dermatologist_skin_condition_on_label_name": object(),
        "fitzpatrick_skin_type": object(),
    })
    monkeypatch.setitem(sys.modules, "datasets", SimpleNamespace(load_dataset=lambda *args, **kwargs: fake))

    samples = scin_hf.load_scin_hf(body_parts=None, max_samples=1)

    assert len(samples) == 1
    assert samples[0].case_id == "scin_123"
    assert samples[0].image_bytes is not None


def test_load_scin_hf_filters_non_face_rows_when_requested(monkeypatch):
    rows = [{
        "case_id": "456",
        "image_1_path": Image.new("RGB", (2, 2), color="green"),
        "body_parts_face": False,
        "dermatologist_skin_condition_on_label_name": "acne vulgaris",
        "fitzpatrick_skin_type": "2",
    }]
    fake = _FakeDataset(rows, {
        "case_id": object(),
        "image_1_path": object(),
        "body_parts_face": object(),
        "dermatologist_skin_condition_on_label_name": object(),
        "fitzpatrick_skin_type": object(),
    })
    monkeypatch.setitem(sys.modules, "datasets", SimpleNamespace(load_dataset=lambda *args, **kwargs: fake))

    samples = scin_hf.load_scin_hf(body_parts=frozenset({"face"}), max_samples=1)

    assert samples == []
