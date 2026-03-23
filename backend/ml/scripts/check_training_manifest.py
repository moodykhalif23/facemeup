import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "image_path",
    "skin_type",
    "condition",
    "skin_idx",
    "cond_idx",
    "source",
    "questionnaire",
]


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ml/data/ham10000/training_manifest.csv")
    if not path.exists():
        print(f"Manifest not found: {path}")
        return 1

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing_fields = [f for f in EXPECTED_FIELDS if f not in (reader.fieldnames or [])]
        if missing_fields:
            print(f"Manifest missing fields: {missing_fields}")
            return 1

        total = 0
        missing_files = 0
        by_source = {}
        by_skin = {}
        by_condition = {}

        for row in reader:
            total += 1
            img_path = Path(row.get("image_path") or "")
            if img_path and not img_path.exists():
                missing_files += 1

            src = row.get("source") or "unknown"
            by_source[src] = by_source.get(src, 0) + 1

            skin = row.get("skin_type") or "unknown"
            by_skin[skin] = by_skin.get(skin, 0) + 1

            cond = row.get("condition") or "unknown"
            by_condition[cond] = by_condition.get(cond, 0) + 1

    print(f"Manifest: {path}")
    print(f"Rows: {total}")
    print(f"Missing image files: {missing_files}")
    print("By source:", by_source)
    print("By skin type:", by_skin)
    print("By condition:", by_condition)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
