#!/usr/bin/env python3
"""
respublica-gpt — CSV Exporter

Flattens prompts.jsonl into prompts.csv with one column per metadata field.
Face-only fields are empty for scene/nature rows and vice versa.

Usage:
  python export_csv.py
  python export_csv.py --input prompts.jsonl --output prompts.csv
"""

import argparse
import csv
import json
from pathlib import Path

# Column order in the output CSV
COLUMNS = [
    # Core fields
    "index",
    "category",
    "quality",
    "format",
    "compression",
    # Shared across all categories
    "photo_type",
    "lighting",
    "artifact",
    "platform_degradation",
    # Face-only
    "ethnicity",
    "skin_tone",
    "age",
    "gender_presentation",
    "background",
    "edge_case",
    # Scene / nature only
    "scene_subject",
    # Prompt text last — it's long and less useful for filtering
    "prompt",
]


def flatten(record: dict) -> dict:
    row = {col: "" for col in COLUMNS}
    row["index"]       = record["index"]
    row["category"]    = record["category"]
    row["quality"]     = record["quality"]
    row["format"]      = record["format"]
    row["compression"] = record["compression"]
    row["prompt"]      = record["prompt"]
    for key, value in record["metadata"].items():
        if key != "category" and key in row:
            row[key] = value
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  default="prompts.jsonl")
    parser.add_argument("--output", default="prompts.csv")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)

    if not src.exists():
        print(f"ERROR: {src} not found. Run prompt_builder.py first.")
        raise SystemExit(1)

    records = []
    with src.open() as f:
        for line in f:
            records.append(flatten(json.loads(line)))

    with dst.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records):,} rows → {dst}")
    print(f"Columns: {', '.join(COLUMNS)}")


if __name__ == "__main__":
    main()
