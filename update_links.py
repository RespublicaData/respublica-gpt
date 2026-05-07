#!/usr/bin/env python3
"""
respublica-gpt — Link Updater

Reads dist/upload_results.json (written by upload_gdrive.py) and patches
the real Google Drive file IDs into README.md and download.py.

Run this once after uploading:
  python update_links.py
  git add README.md download.py
  git commit -m "Add Google Drive download links"
"""

import json
import re
import sys
from pathlib import Path

RESULTS_FILE = Path("dist/upload_results.json")

# Maps zip filename → placeholder token used in README.md and download.py
PLACEHOLDER_MAP = {
    "opendeepfake_faces.zip":    "GDRIVE_FACES_ID",
    "opendeepfake_scenes.zip":   "GDRIVE_SCENES_ID",
    "opendeepfake_nature.zip":   "GDRIVE_NATURE_ID",
    "opendeepfake_metadata.zip": "GDRIVE_METADATA_ID",
}

PATCH_FILES = [Path("README.md"), Path("download.py")]


def load_results() -> dict[str, str]:
    if not RESULTS_FILE.exists():
        print(f"ERROR: {RESULTS_FILE} not found. Run upload_gdrive.py first.")
        sys.exit(1)
    data = json.loads(RESULTS_FILE.read_text())
    id_map: dict[str, str] = {}
    for entry in data.get("files", []):
        filename = entry["file"]
        file_id = entry.get("file_id", "")
        if filename in PLACEHOLDER_MAP and file_id:
            id_map[PLACEHOLDER_MAP[filename]] = file_id
    return id_map


def patch_file(path: Path, replacements: dict[str, str]) -> None:
    if not path.exists():
        print(f"  Skipping {path} (not found)")
        return
    content = path.read_text()
    changed = 0
    for placeholder, real_id in replacements.items():
        if placeholder in content:
            content = content.replace(placeholder, real_id)
            changed += 1
    if changed:
        path.write_text(content)
        print(f"  Patched {path} ({changed} replacement{'s' if changed != 1 else ''})")
    else:
        print(f"  {path}: no placeholders found (already patched?)")


def main() -> None:
    id_map = load_results()

    if not id_map:
        print("ERROR: No file IDs found in upload results. Check dist/upload_results.json.")
        sys.exit(1)

    print(f"Found {len(id_map)} Drive file ID(s):")
    for placeholder, file_id in id_map.items():
        print(f"  {placeholder} → {file_id}")

    print()
    for path in PATCH_FILES:
        patch_file(path, id_map)

    missing = set(PLACEHOLDER_MAP.values()) - set(id_map.keys())
    if missing:
        print(f"\nWarning: {len(missing)} placeholder(s) not resolved: {missing}")
        print("These archives may not have been uploaded yet.")

    print("\nNext steps:")
    print("  git add README.md download.py")
    print('  git commit -m "Add Google Drive download links"')
    print("  git push")


if __name__ == "__main__":
    main()
