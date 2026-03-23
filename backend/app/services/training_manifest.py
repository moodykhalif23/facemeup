import csv
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "data" / "ham10000"

SKIN_TYPES = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
CONDITIONS = ["Acne", "Hyperpigmentation", "Uneven tone", "Dehydration", "None detected"]

HAM_TO_SKIN_TYPE = {
    "nv": "Normal",
    "mel": "Sensitive",
    "bkl": "Combination",
    "bcc": "Oily",
    "akiec": "Dry",
    "vasc": "Sensitive",
    "df": "Normal",
}
HAM_TO_CONDITION = {
    "nv": "None detected",
    "mel": "Hyperpigmentation",
    "bkl": "Hyperpigmentation",
    "bcc": "Acne",
    "akiec": "Uneven tone",
    "vasc": "Acne",
    "df": "None detected",
}


def _resolve_condition(conditions: list[str]) -> str:
    for c in conditions or []:
        if c in CONDITIONS and c != "None detected":
            return c
    for c in conditions or []:
        if c in CONDITIONS:
            return c
    return "None detected"


def _load_ham_labels(meta_path: Path, images: list[Path]) -> list[dict]:
    img_lookup = {p.stem: p for p in images}
    delimiter = "\t" if meta_path.suffix == ".tab" else ","
    rows = []
    with open(meta_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            img_id = row.get("image_id", "").strip()
            dx = row.get("dx", "").strip().lower()
            if img_id not in img_lookup:
                continue
            if dx not in HAM_TO_SKIN_TYPE:
                continue
            skin_type = HAM_TO_SKIN_TYPE[dx]
            condition = HAM_TO_CONDITION[dx]
            rows.append(
                {
                    "image_path": str(img_lookup[img_id]),
                    "skin_type": skin_type,
                    "condition": condition,
                    "skin_idx": SKIN_TYPES.index(skin_type),
                    "cond_idx": CONDITIONS.index(condition),
                    "source": "ham10000",
                    "questionnaire": "{}",
                }
            )
    return rows


def _load_user_labels(data_dir: Path) -> list[dict]:
    rows = []
    for user_dir in data_dir.glob("user_*"):
        if not user_dir.is_dir():
            continue
        for img_path in user_dir.glob("*.*"):
            if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue
            meta_path = Path(str(img_path) + ".json")
            metadata = {}
            if meta_path.exists():
                try:
                    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    metadata = {}
            skin_type = metadata.get("skin_type") or user_dir.name.replace("user_", "")
            if skin_type not in SKIN_TYPES:
                continue
            condition = _resolve_condition(metadata.get("conditions") or [])
            if condition not in CONDITIONS:
                condition = "None detected"
            rows.append(
                {
                    "image_path": str(img_path),
                    "skin_type": skin_type,
                    "condition": condition,
                    "skin_idx": SKIN_TYPES.index(skin_type),
                    "cond_idx": CONDITIONS.index(condition),
                    "source": "user_captured",
                    "questionnaire": json.dumps(metadata.get("questionnaire") or {}, ensure_ascii=False),
                }
            )
    return rows


def refresh_training_manifest(output_path: Path | None = None) -> dict:
    """
    Build a unified training manifest for HAM10000 + user-captured images.
    """
    output_path = output_path or (DATA_DIR / "training_manifest.csv")
    rows: list[dict] = []

    meta_path_tab = DATA_DIR / "HAM10000_metadata.tab"
    meta_path_csv = DATA_DIR / "HAM10000_metadata.csv"
    meta_path = meta_path_tab if meta_path_tab.exists() else meta_path_csv

    if meta_path.exists():
        images = list(DATA_DIR.glob("*.jpg"))
        rows.extend(_load_ham_labels(meta_path, images))

    rows.extend(_load_user_labels(DATA_DIR))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image_path",
                "skin_type",
                "condition",
                "skin_idx",
                "cond_idx",
                "source",
                "questionnaire",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return {"rows": len(rows), "path": str(output_path)}
