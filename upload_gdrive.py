#!/usr/bin/env python3
"""
respublica-gpt — Google Drive Upload Script

Uploads dist/*.zip to a shared Google Drive folder using the respublica account.
Uses resumable uploads so large files survive network interruptions.

Setup (one-time):
  1. Go to https://console.cloud.google.com/
  2. Create a project, enable "Google Drive API"
  3. Create OAuth2 credentials → Desktop App → download as credentials.json
  4. Place credentials.json in this directory
  5. pip install google-auth-oauthlib google-api-python-client tqdm

Usage:
  python upload_gdrive.py                        # upload all dist/*.zip
  python upload_gdrive.py --folder-name MyName   # custom Drive folder name
  python upload_gdrive.py --skip-existing        # skip files already in Drive
  python upload_gdrive.py --dry-run              # list files without uploading
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")
DIST_DIR = Path("dist")
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB resumable upload chunks
DEFAULT_FOLDER_NAME = "respublica-gpt"


def _check_deps() -> None:
    missing = []
    for pkg in ("google.auth", "googleapiclient", "google_auth_oauthlib", "tqdm"):
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    if missing:
        print("Missing packages. Run:")
        print(f"  pip install google-auth-oauthlib google-api-python-client tqdm")
        sys.exit(1)


def _authenticate():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: {CREDENTIALS_FILE} not found.")
                print("Download OAuth2 Desktop App credentials from Google Cloud Console.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
        print(f"Credentials saved to {TOKEN_FILE}")

    return creds


def _build_service(creds):
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, name: str) -> str:
    query = (
        f"name='{name}' "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get("files", [])
    if items:
        folder_id = items[0]["id"]
        print(f"Using existing Drive folder '{name}' (id: {folder_id})")
        return folder_id

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    folder_id = folder["id"]
    print(f"Created Drive folder '{name}' (id: {folder_id})")
    return folder_id


def _list_folder_files(service, folder_id: str) -> dict[str, str]:
    """Returns {filename: file_id} for files in the folder."""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return {f["name"]: f["id"] for f in results.get("files", [])}


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _upload_resumable(service, local_path: Path, folder_id: str) -> str:
    """Upload with resumable protocol + progress bar. Returns file id."""
    from googleapiclient.http import MediaFileUpload
    from tqdm import tqdm

    file_size = local_path.stat().st_size
    mime = "application/zip"

    metadata = {"name": local_path.name, "parents": [folder_id]}
    media = MediaFileUpload(str(local_path), mimetype=mime, chunksize=CHUNK_SIZE, resumable=True)

    request = service.files().create(body=metadata, media_body=media, fields="id")

    print(f"  Uploading {local_path.name} ({_human_size(file_size)})")
    bar = tqdm(total=file_size, unit="B", unit_scale=True, unit_divisor=1024)

    response = None
    uploaded = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                new_uploaded = int(status.resumable_progress)
                bar.update(new_uploaded - uploaded)
                uploaded = new_uploaded
        except Exception as e:
            print(f"\n  Chunk error ({e}), retrying in 5s...")
            time.sleep(5)

    bar.update(file_size - uploaded)
    bar.close()
    return response["id"]


def _make_public(service, file_id: str) -> str:
    service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()
    file_meta = service.files().get(fileId=file_id, fields="webContentLink,webViewLink").execute()
    return file_meta.get("webContentLink") or file_meta.get("webViewLink", "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder-name",  default=DEFAULT_FOLDER_NAME)
    parser.add_argument("--skip-existing", action="store_true", help="Skip files already in Drive")
    parser.add_argument("--make-public",   action="store_true", help="Make uploaded files publicly accessible")
    parser.add_argument("--dry-run",       action="store_true")
    args = parser.parse_args()

    _check_deps()

    zips = sorted(DIST_DIR.glob("*.zip"))
    if not zips:
        print(f"No zip files found in {DIST_DIR}/. Run package.py first.")
        sys.exit(1)

    print(f"Files to upload ({len(zips)}):")
    total_bytes = 0
    for z in zips:
        size = z.stat().st_size
        total_bytes += size
        print(f"  {z.name}  ({_human_size(size)})")
    print(f"Total: {_human_size(total_bytes)}")

    if args.dry_run:
        print("\n[DRY RUN] No files uploaded.")
        return

    print("\nAuthenticating with Google Drive...")
    creds = _authenticate()
    service = _build_service(creds)

    folder_id = _get_or_create_folder(service, args.folder_name)
    existing = _list_folder_files(service, folder_id)

    results: list[dict] = []

    for zip_path in zips:
        if args.skip_existing and zip_path.name in existing:
            print(f"\nSkipping {zip_path.name} (already in Drive)")
            results.append({"file": zip_path.name, "status": "skipped", "file_id": existing[zip_path.name]})
            continue

        file_id = _upload_resumable(service, zip_path, folder_id)
        link = ""
        if args.make_public:
            link = _make_public(service, file_id)
            print(f"  Public link: {link}")
        results.append({"file": zip_path.name, "status": "uploaded", "file_id": file_id, "link": link})

    # Write results summary
    out = DIST_DIR / "upload_results.json"
    out.write_text(json.dumps({"folder_id": folder_id, "files": results}, indent=2))
    print(f"\nUpload results saved to {out}")

    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    print(f"Drive folder: {folder_url}")


if __name__ == "__main__":
    main()
