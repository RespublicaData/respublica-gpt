#!/usr/bin/env python3
"""
respublica-gpt — Dataset Downloader

Downloads and extracts the full dataset from Google Drive.

Usage:
  pip install gdown tqdm
  python download.py                  # download all archives
  python download.py --faces-only     # just face images
  python download.py --metadata-only  # just prompts.jsonl + manifest.jsonl
  python download.py --no-extract     # download zips without extracting
"""

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

# ── Drive file IDs (updated automatically by update_links.py after upload) ──
FILES = {
    "faces": {
        "id":       "GDRIVE_FACES_ID",
        "filename": "opendeepfake_faces.zip",
        "dest":     Path("images/faces"),
        "size":     "~1.4 GB",
    },
    "scenes": {
        "id":       "GDRIVE_SCENES_ID",
        "filename": "opendeepfake_scenes.zip",
        "dest":     Path("images/scene"),
        "size":     "~0.8 GB",
    },
    "nature": {
        "id":       "GDRIVE_NATURE_ID",
        "filename": "opendeepfake_nature.zip",
        "dest":     Path("images/nature"),
        "size":     "~0.8 GB",
    },
    "metadata": {
        "id":       "GDRIVE_METADATA_ID",
        "filename": "opendeepfake_metadata.zip",
        "dest":     Path("."),
        "size":     "~3 MB",
    },
}


def _check_gdown() -> None:
    try:
        import gdown  # noqa: F401
    except ImportError:
        print("gdown is required. Install it with:  pip install gdown")
        sys.exit(1)


def _download(file_id: str, filename: str, size: str) -> Path:
    import gdown

    out = Path(filename)
    if out.exists():
        print(f"  {filename} already downloaded, skipping.")
        return out

    url = f"https://drive.google.com/uc?id={file_id}"
    print(f"  Downloading {filename} ({size})...")
    gdown.download(url, str(out), quiet=False, fuzzy=True)
    return out


def _extract(zip_path: Path, dest: Path, label: str) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    print(f"  Extracting {zip_path.name} → {dest}/")
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.infolist()
        from tqdm import tqdm
        for member in tqdm(members, desc=label, unit="file"):
            # Strip the top-level folder the zip was built with
            parts = Path(member.filename).parts
            if len(parts) > 1:
                member.filename = str(Path(*parts[1:]))
            zf.extract(member, dest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the respublica-gpt dataset")
    parser.add_argument("--faces-only",    action="store_true")
    parser.add_argument("--scenes-only",   action="store_true")
    parser.add_argument("--nature-only",   action="store_true")
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--no-extract",    action="store_true", help="Keep zip files without extracting")
    args = parser.parse_args()

    _check_gdown()

    # Determine which archives to fetch
    if args.faces_only:
        keys = ["faces"]
    elif args.scenes_only:
        keys = ["scenes"]
    elif args.nature_only:
        keys = ["nature"]
    elif args.metadata_only:
        keys = ["metadata"]
    else:
        keys = list(FILES.keys())

    # Validate IDs are real
    placeholders = [k for k in keys if "GDRIVE_" in FILES[k]["id"]]
    if placeholders:
        print("ERROR: Drive file IDs have not been set yet.")
        print("Run update_links.py after uploading to Google Drive, or set them manually in download.py.")
        sys.exit(1)

    for key in keys:
        info = FILES[key]
        print(f"\n── {key} ──")
        zip_path = _download(info["id"], info["filename"], info["size"])
        if not args.no_extract:
            _extract(zip_path, info["dest"], key)
            zip_path.unlink()
            print(f"  Removed {zip_path.name}")

    print("\nDone. Dataset is ready in images/")


if __name__ == "__main__":
    main()
