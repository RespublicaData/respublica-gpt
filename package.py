#!/usr/bin/env python3
"""
respublica-gpt — Packaging Script

Creates zip archives ready for Google Drive upload:
  opendeepfake_faces.zip    — all face images
  opendeepfake_scenes.zip   — all scene images
  opendeepfake_nature.zip   — all nature images
  opendeepfake_metadata.zip — prompts.jsonl, manifest.jsonl, README.md, LICENSE

Usage:
  python package.py              # build all zips into ./dist/
  python package.py --force      # rebuild even if zip already exists
  python package.py --dry-run    # show what would be zipped without writing
"""

import argparse
import json
import zipfile
from pathlib import Path

from tqdm import tqdm


DIST_DIR = Path("dist")

CATEGORIES = {
    "faces":  ("opendeepfake_faces.zip",   Path("images/faces")),
    "scenes": ("opendeepfake_scenes.zip",  Path("images/scene")),
    "nature": ("opendeepfake_nature.zip",  Path("images/nature")),
}

METADATA_ZIP = "opendeepfake_metadata.zip"
METADATA_FILES = [
    Path("prompts.jsonl"),
    Path("prompts.csv"),
    Path("manifest.jsonl"),
    Path("README.md"),
    Path("LICENSE"),
]


def human_size(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} TB"


def zip_directory(src_dir: Path, dest_zip: Path, label: str, dry_run: bool) -> int:
    files = sorted(src_dir.iterdir()) if src_dir.exists() else []
    files = [f for f in files if f.is_file()]
    total_bytes = sum(f.stat().st_size for f in files)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Packing {label}")
    print(f"  Source : {src_dir}  ({len(files)} files, {human_size(total_bytes)})")
    print(f"  Output : {dest_zip}")

    if dry_run:
        return 0

    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for f in tqdm(files, desc=label, unit="file"):
            # Store as category/filename so the zip has a clean top-level folder
            arcname = f"{src_dir.name}/{f.name}"
            zf.write(f, arcname)

    zip_size = dest_zip.stat().st_size
    print(f"  Done   : {human_size(zip_size)}")
    return zip_size


def zip_metadata(dest_zip: Path, dry_run: bool) -> int:
    files = [f for f in METADATA_FILES if f.exists()]
    total_bytes = sum(f.stat().st_size for f in files)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Packing metadata")
    print(f"  Files  : {[f.name for f in files]}  ({human_size(total_bytes)})")
    print(f"  Output : {dest_zip}")

    if dry_run:
        return 0

    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in tqdm(files, desc="metadata", unit="file"):
            zf.write(f, f.name)

    zip_size = dest_zip.stat().st_size
    print(f"  Done   : {human_size(zip_size)}")
    return zip_size


def write_manifest(dist_dir: Path, zip_sizes: dict[str, int]) -> None:
    manifest = []
    for name, size in zip_sizes.items():
        manifest.append({"file": name, "size_bytes": size, "size_human": human_size(size)})
    out = dist_dir / "packages.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"\nWrote package manifest: {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force",   action="store_true", help="Rebuild zips even if they exist")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without writing")
    args = parser.parse_args()

    dist_dir = DIST_DIR
    zip_sizes: dict[str, int] = {}

    for label, (zip_name, src_dir) in CATEGORIES.items():
        dest_zip = dist_dir / zip_name
        if dest_zip.exists() and not args.force:
            print(f"\nSkipping {zip_name} (already exists — use --force to rebuild)")
            zip_sizes[zip_name] = dest_zip.stat().st_size
            continue
        size = zip_directory(src_dir, dest_zip, label, args.dry_run)
        if not args.dry_run:
            zip_sizes[zip_name] = size

    meta_zip = dist_dir / METADATA_ZIP
    if meta_zip.exists() and not args.force:
        print(f"\nSkipping {METADATA_ZIP} (already exists — use --force to rebuild)")
        zip_sizes[METADATA_ZIP] = meta_zip.stat().st_size
    else:
        size = zip_metadata(meta_zip, args.dry_run)
        if not args.dry_run:
            zip_sizes[METADATA_ZIP] = size

    if not args.dry_run and zip_sizes:
        write_manifest(dist_dir, zip_sizes)
        total = sum(zip_sizes.values())
        print(f"\nTotal upload size: {human_size(total)}")


if __name__ == "__main__":
    main()
