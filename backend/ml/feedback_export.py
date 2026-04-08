#!/usr/bin/env python3
"""
ML-004: Feedback Export Pipeline
=================================
Queries SkinProfileHistory for user-confirmed/rejected analyses and exports
them as a CSV that the retraining pipeline can ingest as labeled training data.

Confirmed records map directly to training labels.
Rejected records are excluded (we don't know the true label).

Usage (from backend/ directory):
    python ml/feedback_export.py
    python ml/feedback_export.py --output ml/data/ham10000/feedback_labels.csv
    python ml/feedback_export.py --min-date 2026-01-01

Output CSV columns:
    image_path, skin_type, condition, skin_idx, cond_idx, source, questionnaire

The output is intentionally compatible with the training_manifest.csv schema
so train_pipeline.py can load it via --extra-labels (see below).
"""

import os
import sys
import csv
import json
import argparse
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR    = BACKEND_DIR / "ml" / "data" / "ham10000"
OUTPUT_DIR  = DATA_DIR / "user_feedback"

SKIN_TYPES = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
CONDITIONS = [
    "Acne", "Hyperpigmentation", "Uneven tone", "Dehydration",
    "Wrinkles", "Redness", "None detected",
]


def _resolve_condition(conditions: list[str]) -> str:
    for c in conditions:
        if c in CONDITIONS and c != "None detected":
            return c
    return "None detected"


def export_feedback(
    output_path: Path,
    min_date: str | None = None,
    db_url: str | None = None,
) -> int:
    """
    Pull confirmed feedback records from the database and write them to CSV.

    Returns the number of records exported.
    """
    # Import here so the script can be imported without app deps for testing
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
    except ImportError:
        print("✗ sqlalchemy not installed. Run: pip install sqlalchemy")
        sys.exit(1)

    if db_url is None:
        db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # Attempt to load from .env in backend/
        env_path = BACKEND_DIR / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not db_url:
        print("✗ DATABASE_URL not set. Pass --db-url or set DATABASE_URL env var.")
        sys.exit(1)

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)

    date_filter = ""
    if min_date:
        date_filter = f"AND created_at >= '{min_date}'"

    query = text(f"""
        SELECT
            id,
            user_id,
            skin_type,
            conditions_csv,
            skin_type_scores_json,
            inference_mode,
            report_image_base64,
            capture_images_json,
            questionnaire_json,
            created_at
        FROM skin_profile_history
        WHERE user_feedback = 'confirmed'
        {date_filter}
        ORDER BY created_at DESC
    """)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    exported = 0
    skipped  = 0

    with Session() as session:
        rows = session.execute(query).fetchall()

    print(f"Found {len(rows)} confirmed feedback record(s)")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "image_path", "skin_type", "condition", "skin_idx",
            "cond_idx", "source", "questionnaire",
        ])
        writer.writeheader()

        for row in rows:
            skin_type = row.skin_type
            if skin_type not in SKIN_TYPES:
                skipped += 1
                continue

            conditions = [c.strip() for c in (row.conditions_csv or "").split(",") if c.strip()]
            condition  = _resolve_condition(conditions)

            skin_idx = SKIN_TYPES.index(skin_type)
            cond_idx = CONDITIONS.index(condition)

            # Save the thumbnail as a training image if we have one
            image_path = ""
            thumbnail  = row.report_image_base64
            if thumbnail:
                # Strip data URI prefix if present
                if "," in thumbnail:
                    thumbnail = thumbnail.split(",", 1)[1]
                img_file = OUTPUT_DIR / f"feedback_{row.id}.jpg"
                if not img_file.exists():
                    try:
                        import base64
                        img_data = base64.b64decode(thumbnail)
                        img_file.write_bytes(img_data)
                    except Exception:
                        img_file = None
                if img_file:
                    image_path = str(img_file)

            # Only write rows where we have an image to train on
            if not image_path:
                skipped += 1
                continue

            writer.writerow({
                "image_path":  image_path,
                "skin_type":   skin_type,
                "condition":   condition,
                "skin_idx":    skin_idx,
                "cond_idx":    cond_idx,
                "source":      "user_feedback",
                "questionnaire": row.questionnaire_json or "{}",
            })
            exported += 1

    print(f"✓ Exported : {exported} records → {output_path}")
    print(f"  Skipped  : {skipped} (no image or unknown skin type)")
    return exported


def main():
    parser = argparse.ArgumentParser(description="Export confirmed feedback as training data")
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATA_DIR / "feedback_labels.csv"),
        help="Output CSV path (default: ml/data/ham10000/feedback_labels.csv)",
    )
    parser.add_argument(
        "--min-date",
        type=str,
        default=None,
        help="Only export records confirmed after this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="PostgreSQL connection URL (overrides DATABASE_URL env var)",
    )
    args = parser.parse_args()

    exported = export_feedback(
        output_path=Path(args.output),
        min_date=args.min_date,
        db_url=args.db_url,
    )

    if exported == 0:
        print("\nNo feedback data to export yet.")
        print("Users need to confirm/reject analyses via POST /analyze/feedback first.")
    else:
        print(f"\nNext step: retrain with feedback data")
        print(f"  python ml/train_pipeline.py --skip-download")


if __name__ == "__main__":
    main()
