import csv
import json
from pathlib import Path
from typing import Any


CSV_FIELDS = [
    "image_path",
    "skin_type",
    "conditions",
    "questionnaire",
    "user_id",
    "captured_at",
    "source_dir",
]


def export_training_metadata_csv(root_dir: str | Path, output_path: str | Path) -> int:
    """
    Aggregate per-image metadata JSON files into a single CSV for downstream ML.
    Returns the number of rows written.
    """
    root = Path(root_dir)
    output = Path(output_path)
    rows: list[dict[str, Any]] = []

    if not root.exists():
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
        return 0

    for meta_path in root.rglob("*.json"):
        image_path = Path(str(meta_path)[:-5])  # strip .json
        if not image_path.exists():
            continue

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        rows.append(
            {
                "image_path": str(image_path),
                "skin_type": meta.get("skin_type"),
                "conditions": "|".join(meta.get("conditions") or []),
                "questionnaire": json.dumps(meta.get("questionnaire") or {}, ensure_ascii=False),
                "user_id": meta.get("user_id"),
                "captured_at": meta.get("captured_at"),
                "source_dir": str(root),
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)
