#!/usr/bin/env python3
"""
respublica-gpt — OpenAI Batch API Generation Pipeline

NOTE: As of May 2026, OpenAI's Batch API does NOT support /v1/images/generations.
It only covers /v1/chat/completions and /v1/embeddings. This script is stubbed
for when/if OpenAI adds image generation batch support. Until then, use
generate_images.py for all image generation.

Reference: https://platform.openai.com/docs/guides/batch

Usage:
  python generate_batch.py submit               # build + upload + submit a batch job
  python generate_batch.py status               # check job status
  python generate_batch.py download             # download + save images when done
  python generate_batch.py run                  # submit, poll until done, then download

  python generate_batch.py submit --dry-run     # preview what would be submitted
  python generate_batch.py submit --budget 50   # cap spend at $50
  python generate_batch.py submit --start 3000 --end 6000  # specific range

State file:
  batch_state.json  — tracks active job ID, input file ID, submission time
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from config import (
    MODEL, SIZE, OUTPUT_DIR,
    PROMPTS_FILE, MANIFEST_FILE, PROGRESS_FILE,
    COST_PER_IMAGE,
)

BATCH_STATE_FILE = "batch_state.json"
BATCH_INPUT_FILE = "batch_input.jsonl"
BATCH_OUTPUT_FILE = "batch_output.jsonl"
POLL_INTERVAL = 60  # seconds between status checks in `run` mode


# ── Shared helpers (mirrored from generate_images.py) ────────────────────────

def load_progress() -> set[int]:
    p = Path(PROGRESS_FILE)
    if p.exists():
        return set(json.loads(p.read_text()).get("completed", []))
    return set()


def save_progress(completed: set[int]):
    Path(PROGRESS_FILE).write_text(json.dumps({
        "completed": sorted(completed),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }))


def append_manifest(entry: dict):
    with open(MANIFEST_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def sanitize_filename(prompt: str, max_len: int = 120) -> str:
    s = re.sub(r'[^a-z0-9]+', '_', prompt.lower()).strip('_')
    return s[:max_len].rstrip('_') if len(s) > max_len else s


def category_dir(base: Path, category: str) -> Path:
    subdir = "faces" if category == "face" else category
    d = base / subdir
    d.mkdir(parents=True, exist_ok=True)
    return d


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    i = 2
    while True:
        candidate = path.with_stem(f"{path.stem}_{i}")
        if not candidate.exists():
            return candidate
        i += 1


# ── Batch state ───────────────────────────────────────────────────────────────

def save_state(state: dict):
    Path(BATCH_STATE_FILE).write_text(json.dumps(state, indent=2))


def load_state() -> dict:
    p = Path(BATCH_STATE_FILE)
    if not p.exists():
        print(f"ERROR: {BATCH_STATE_FILE} not found. Run `submit` first.")
        sys.exit(1)
    return json.loads(p.read_text())


# ── Build batch input JSONL ───────────────────────────────────────────────────

def build_batch_input(
    prompts: list[dict],
    completed: set[int],
) -> list[dict]:
    """Convert prompt records into Batch API request objects."""
    requests = []
    for p in prompts:
        if p["index"] in completed:
            continue
        requests.append({
            "custom_id": f"img-{p['index']:05d}",
            "method": "POST",
            "url": "/v1/images/generations",
            "body": {
                "model": MODEL,
                "prompt": p["prompt"],
                "n": 1,
                "size": SIZE,
                "quality": p["quality"],
                "output_format": p["format"],
                "output_compression": p["compression"],
            },
        })
    return requests


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_submit(args):
    with open(PROMPTS_FILE) as f:
        all_prompts = [json.loads(l) for l in f]

    end = min(args.end, len(all_prompts)) if args.end else len(all_prompts)
    prompts = [p for p in all_prompts if args.start <= p["index"] < end]

    # Budget cap
    if args.budget:
        capped, running = [], 0.0
        for p in prompts:
            cost = COST_PER_IMAGE.get(p["quality"], 0)
            if running + cost > args.budget:
                break
            capped.append(p)
            running += cost
        prompts = capped

    completed = load_progress()
    pending = [p for p in prompts if p["index"] not in completed]

    est_cost = sum(COST_PER_IMAGE.get(p["quality"], 0) for p in pending)
    batch_cost = est_cost * 0.5

    print(f"\n{'='*60}")
    print(f"  respublica-gpt Batch Submitter")
    print(f"{'='*60}")
    print(f"  Prompts in range : {len(prompts)}")
    print(f"  Already done     : {len(prompts) - len(pending)}")
    print(f"  To submit        : {len(pending)}")
    print(f"  Real-time cost   : ${est_cost:,.2f}")
    print(f"  Batch cost (~50%): ${batch_cost:,.2f}")

    if args.dry_run:
        print(f"\n  [DRY RUN] Would submit {len(pending)} requests. No job created.")
        return

    if not pending:
        print("\n  Nothing to submit — all images already generated.")
        return

    client = OpenAI()

    # Write batch input file
    requests = build_batch_input(prompts, completed)
    input_path = Path(BATCH_INPUT_FILE)
    with input_path.open("w") as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")
    print(f"\n  Wrote {len(requests)} requests to {BATCH_INPUT_FILE}")

    # Upload input file
    print("  Uploading batch input file...")
    with input_path.open("rb") as f:
        upload = client.files.create(file=f, purpose="batch")
    print(f"  Uploaded: {upload.id}")

    # Submit batch
    print("  Submitting batch job...")
    batch = client.batches.create(
        input_file_id=upload.id,
        endpoint="/v1/images/generations",
        completion_window="24h",
        metadata={"project": "respublica-gpt", "count": str(len(requests))},
    )

    state = {
        "batch_id": batch.id,
        "input_file_id": upload.id,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "request_count": len(requests),
        "estimated_cost_usd": round(batch_cost, 2),
        "status": batch.status,
    }
    save_state(state)

    print(f"\n  ✅ Batch submitted!")
    print(f"     Job ID   : {batch.id}")
    print(f"     Requests : {len(requests)}")
    print(f"     Est. cost: ${batch_cost:.2f}")
    print(f"     State    : {BATCH_STATE_FILE}")
    print(f"\n  Check status : python generate_batch.py status")
    print(f"  Download     : python generate_batch.py download")


def cmd_status(args):
    state = load_state()
    client = OpenAI()
    batch = client.batches.retrieve(state["batch_id"])

    counts = batch.request_counts
    submitted = state["request_count"]
    done = (counts.completed or 0) + (counts.failed or 0)
    pct = done / submitted * 100 if submitted else 0

    submitted_at = state["submitted_at"]
    elapsed_hrs = (
        datetime.now(timezone.utc) -
        datetime.fromisoformat(submitted_at)
    ).total_seconds() / 3600

    print(f"\n  Batch ID  : {batch.id}")
    print(f"  Status    : {batch.status}")
    print(f"  Progress  : {done}/{submitted} ({pct:.1f}%)")
    print(f"    Completed : {counts.completed}")
    print(f"    Failed    : {counts.failed}")
    print(f"    In queue  : {counts.total - done}")
    print(f"  Elapsed   : {elapsed_hrs:.1f} hours")

    if batch.status == "completed":
        print(f"\n  ✅ Done! Run:  python generate_batch.py download")
    elif batch.status in ("failed", "expired", "cancelled"):
        print(f"\n  ❌ Job ended with status: {batch.status}")


def cmd_download(args):
    state = load_state()
    client = OpenAI()

    batch = client.batches.retrieve(state["batch_id"])
    if batch.status != "completed":
        print(f"Batch not ready — status: {batch.status}")
        print("Check again with: python generate_batch.py status")
        sys.exit(1)

    output_file_id = batch.output_file_id
    if not output_file_id:
        print("ERROR: No output file ID on completed batch. Check for errors.")
        sys.exit(1)

    # Download output
    print(f"Downloading output file {output_file_id}...")
    content = client.files.content(output_file_id)
    Path(BATCH_OUTPUT_FILE).write_bytes(content.read())
    print(f"Saved to {BATCH_OUTPUT_FILE}")

    # Parse and save images
    output_dir = Path(OUTPUT_DIR)
    with open(PROMPTS_FILE) as f:
        prompt_index = {json.loads(l)["index"]: json.loads(l) for l in open(PROMPTS_FILE)}

    completed = load_progress()
    saved, failed, skipped = 0, 0, 0

    with open(BATCH_OUTPUT_FILE) as f:
        lines = [json.loads(l) for l in f]

    print(f"Processing {len(lines)} results...")

    for result in lines:
        custom_id = result["custom_id"]           # "img-00042"
        idx = int(custom_id.split("-")[1])

        if result.get("error"):
            print(f"  FAILED [{idx:05d}]: {result['error']}")
            failed += 1
            continue

        if idx in completed:
            skipped += 1
            continue

        response_body = result["response"]["body"]
        b64 = response_body["data"][0].get("b64_json")
        if not b64:
            print(f"  NO IMAGE [{idx:05d}]: no b64_json in response")
            failed += 1
            continue

        prompt_entry = prompt_index.get(idx)
        if not prompt_entry:
            print(f"  UNKNOWN INDEX [{idx:05d}]")
            failed += 1
            continue

        img_bytes = base64.b64decode(b64)
        fmt = prompt_entry["format"]
        safe_name = sanitize_filename(prompt_entry["prompt"])
        cat_dir = category_dir(output_dir, prompt_entry["category"])
        filepath = unique_path(cat_dir / f"{safe_name}.{fmt}")
        filepath.write_bytes(img_bytes)

        completed.add(idx)
        append_manifest({
            "index": idx,
            "filename": filepath.name,
            "prompt": prompt_entry["prompt"],
            "quality": prompt_entry["quality"],
            "format": fmt,
            "compression": prompt_entry["compression"],
            "category": prompt_entry["category"],
            "metadata": prompt_entry.get("metadata", {}),
            "file_size_bytes": len(img_bytes),
            "generation_time_s": None,
            "estimated_cost_usd": COST_PER_IMAGE.get(prompt_entry["quality"], 0) * 0.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "via_batch": True,
        })
        saved += 1

    save_progress(completed)

    print(f"\n{'='*60}")
    print(f"  Download complete")
    print(f"  Saved  : {saved}")
    print(f"  Failed : {failed}")
    print(f"  Skipped (already done) : {skipped}")
    print(f"  Total completed: {len(completed)}")
    print(f"{'='*60}")


def cmd_run(args):
    """Submit, poll, download in one blocking call."""
    cmd_submit(args)

    if args.dry_run:
        return

    state = load_state()
    client = OpenAI()
    print(f"\n  Polling every {POLL_INTERVAL}s (Ctrl+C to stop — job keeps running)...")

    while True:
        time.sleep(POLL_INTERVAL)
        batch = client.batches.retrieve(state["batch_id"])
        counts = batch.request_counts
        done = (counts.completed or 0) + (counts.failed or 0)
        total = state["request_count"]
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {batch.status} — {done}/{total}")

        if batch.status == "completed":
            print("  ✅ Complete! Downloading...")
            cmd_download(args)
            return
        elif batch.status in ("failed", "expired", "cancelled"):
            print(f"  ❌ Job ended: {batch.status}")
            sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="respublica-gpt — OpenAI Batch API (50% cheaper, 24hr turnaround)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Shared args for submit/run
    for name in ("submit", "run"):
        p = sub.add_parser(name)
        p.add_argument("--start",   type=int,   default=0)
        p.add_argument("--end",     type=int,   default=None)
        p.add_argument("--budget",  type=float, default=None, help="Max $ to spend (batch price)")
        p.add_argument("--dry-run", action="store_true")

    sub.add_parser("status")
    sub.add_parser("download")

    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set.")
        sys.exit(1)

    {"submit": cmd_submit, "status": cmd_status, "download": cmd_download, "run": cmd_run}[
        args.command
    ](args)


if __name__ == "__main__":
    main()
