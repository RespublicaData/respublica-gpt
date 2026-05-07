#!/usr/bin/env python3
"""
respublica-gpt — Async Image Generation Pipeline

Features:
  - Reads prompts from prompts.jsonl
  - Async concurrent generation with configurable workers
  - Exponential backoff on rate-limit (429) errors
  - Resume from checkpoint (progress.json)
  - Per-image cost tracking
  - Manifest logging (manifest.jsonl)
  - Dry-run mode for cost estimation
"""

import asyncio
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import (
    AsyncOpenAI, RateLimitError, APIError, APITimeoutError,
    BadRequestError, PermissionDeniedError, AuthenticationError,
)

from config import (
    MODEL,
    SIZE,
    OUTPUT_DIR,
    PROMPTS_FILE,
    MANIFEST_FILE,
    PROGRESS_FILE,
    MAX_CONCURRENT,
    RETRY_BASE_DELAY,
    MAX_RETRIES,
    COST_PER_IMAGE,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Progress / checkpoint management
# ═══════════════════════════════════════════════════════════════════════════════

def load_progress(path: str = PROGRESS_FILE) -> set[int]:
    """Load set of completed prompt indices."""
    p = Path(path)
    if p.exists():
        data = json.loads(p.read_text())
        return set(data.get("completed", []))
    return set()


def save_progress(completed: set[int], path: str = PROGRESS_FILE):
    """Save completed indices to disk."""
    Path(path).write_text(json.dumps({
        "completed": sorted(completed),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }))


# ═══════════════════════════════════════════════════════════════════════════════
# Manifest logging
# ═══════════════════════════════════════════════════════════════════════════════

def append_manifest(entry: dict, path: str = MANIFEST_FILE):
    """Append a single generation record to the manifest."""
    with open(path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Filename sanitization
# ═══════════════════════════════════════════════════════════════════════════════

import re

def _sanitize_filename(prompt: str, max_len: int = 120) -> str:
    """Convert prompt text to a safe filename: lowercase, underscores only."""
    s = prompt.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = s.strip('_')
    if len(s) > max_len:
        s = s[:max_len].rstrip('_')
    return s


# ═══════════════════════════════════════════════════════════════════════════════
# Single image generation with retry
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_one(
    client: AsyncOpenAI,
    prompt_entry: dict,
    output_dir: Path,
    semaphore: asyncio.Semaphore,
    stats: dict,
) -> dict | None:
    """
    Generate a single image from a prompt entry.
    Returns manifest record on success, None on failure after retries.
    """
    idx = prompt_entry["index"]
    prompt = prompt_entry["prompt"]
    quality = prompt_entry["quality"]
    fmt = prompt_entry["format"]
    compression = prompt_entry["compression"]
    category = prompt_entry["category"]

    # Build prompt-based filename
    safe_name = _sanitize_filename(prompt)
    filename = f"{safe_name}.{fmt}"
    cat_dir = output_dir / (category + "s" if category == "face" else category)
    cat_dir.mkdir(parents=True, exist_ok=True)
    filepath = cat_dir / filename

    # Handle duplicates
    if filepath.exists():
        i = 2
        while filepath.exists():
            filename = f"{safe_name}_{i}.{fmt}"
            filepath = cat_dir / filename
            i += 1

    async with semaphore:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                t0 = time.monotonic()

                response = await client.images.generate(
                    model=MODEL,
                    prompt=prompt,
                    n=1,
                    size=SIZE,
                    quality=quality,
                    output_format=fmt,
                    output_compression=compression,
                )

                elapsed = time.monotonic() - t0

                # Decode and save
                b64_data = response.data[0].b64_json
                img_bytes = base64.b64decode(b64_data)
                filepath.write_bytes(img_bytes)

                # Cost tracking
                cost = COST_PER_IMAGE.get(quality, 0)
                stats["total_cost"] += cost
                stats["completed"] += 1

                record = dict(
                    index=idx,
                    filename=filename,
                    prompt=prompt,
                    quality=quality,
                    format=fmt,
                    compression=compression,
                    category=category,
                    metadata=prompt_entry.get("metadata", {}),
                    file_size_bytes=len(img_bytes),
                    generation_time_s=round(elapsed, 2),
                    estimated_cost_usd=cost,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

                return record

            except BadRequestError as e:
                # Non-retryable errors (billing limit, content policy, etc.)
                err_body = getattr(e, 'body', {}) or {}
                err_code = (err_body.get('error', {}) or {}).get('code', '')
                if 'billing' in err_code or 'limit' in err_code:
                    print(f"  🛑 [{idx:05d}] Billing limit reached. Stopping.")
                    stats["billing_stopped"] = True
                    return None
                print(f"  ❌ [{idx:05d}] Bad request: {e}")
                break

            except (PermissionDeniedError, AuthenticationError) as e:
                # Non-retryable: org not verified, wrong API key, etc.
                print(f"  🛑 [{idx:05d}] {e}")
                stats["billing_stopped"] = True  # reuse flag to halt pipeline
                return None

            except RateLimitError:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"  ⏳ [{idx:05d}] Rate limited. Retry {attempt}/{MAX_RETRIES} in {delay:.0f}s")
                await asyncio.sleep(delay)

            except (APIError, APITimeoutError) as e:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"  ⚠️  [{idx:05d}] API error: {e}. Retry {attempt}/{MAX_RETRIES} in {delay:.0f}s")
                await asyncio.sleep(delay)

            except Exception as e:
                print(f"  ❌ [{idx:05d}] Unexpected error: {e}")
                break

    print(f"  ❌ [{idx:05d}] Failed after {MAX_RETRIES} retries.")
    stats["failed"] += 1
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Main pipeline
# ═══════════════════════════════════════════════════════════════════════════════

async def run_pipeline(
    prompts_file: str,
    start: int,
    end: int | None,
    budget: float | None,
    dry_run: bool,
    max_concurrent: int,
):
    """Run the full generation pipeline."""

    # ── Load prompts ─────────────────────────────────────────────────────
    with open(prompts_file) as f:
        all_prompts = [json.loads(line) for line in f]

    total = len(all_prompts)
    end = min(end, total) if end is not None else total
    prompts = [p for p in all_prompts if start <= p["index"] < end]

    # ── Apply budget cap ─────────────────────────────────────────────────
    if budget is not None:
        budgeted = []
        running_cost = 0.0
        for p in prompts:
            cost = COST_PER_IMAGE.get(p["quality"], 0)
            if running_cost + cost > budget:
                break
            budgeted.append(p)
            running_cost += cost
        prompts = budgeted

    print(f"\n{'='*60}")
    print(f"  respublica-gpt Image Generator")
    print(f"{'='*60}")
    print(f"  Model:      {MODEL}")
    print(f"  Size:       {SIZE}")
    print(f"  Prompts:    {len(prompts)}")
    print(f"  Concurrent: {max_concurrent}")
    if budget is not None:
        print(f"  Budget:     ${budget:.2f}")

    # ── Cost estimate ────────────────────────────────────────────────────
    est_cost = sum(COST_PER_IMAGE.get(p["quality"], 0) for p in prompts)
    print(f"  Est. cost:  ${est_cost:,.2f}")

    if dry_run:
        print(f"\n  🏷️  DRY RUN — no images will be generated.")
        _print_dry_run_stats(prompts)
        return

    # ── Confirm ──────────────────────────────────────────────────────────
    print(f"\n  ⚡ Starting generation...\n")

    # ── Setup ────────────────────────────────────────────────────────────
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = AsyncOpenAI()
    semaphore = asyncio.Semaphore(max_concurrent)

    # ── Load checkpoint ──────────────────────────────────────────────────
    completed = load_progress()
    pending = [p for p in prompts if p["index"] not in completed]

    if len(pending) < len(prompts):
        skipped = len(prompts) - len(pending)
        print(f"  ♻️  Resuming: {skipped} already completed, {len(pending)} remaining.\n")

    if not pending:
        print("  ✅ All images in this range already generated!")
        return

    stats = {"completed": 0, "failed": 0, "total_cost": 0.0, "billing_stopped": False}
    t_start = time.monotonic()

    # ── Generate ─────────────────────────────────────────────────────────
    # Process in batches to enable periodic checkpoint saving
    BATCH_SIZE = 50
    for batch_start in range(0, len(pending), BATCH_SIZE):
        batch = pending[batch_start:batch_start + BATCH_SIZE]

        tasks = [
            generate_one(client, entry, output_dir, semaphore, stats)
            for entry in batch
        ]

        results = await asyncio.gather(*tasks)

        # Save results
        for result in results:
            if result is not None:
                completed.add(result["index"])
                append_manifest(result)

        save_progress(completed)

        # Check for billing stop
        if stats["billing_stopped"]:
            print(f"\n  🛑 Billing limit reached. Stopping early.")
            print(f"     Run again after raising your limit — progress is saved.")
            break

        # Progress report
        elapsed = time.monotonic() - t_start
        total_done = stats["completed"]
        total_pending = len(pending)
        rate = total_done / elapsed if elapsed > 0 else 0
        eta = (total_pending - total_done) / rate if rate > 0 else 0

        print(
            f"  📊 Progress: {total_done}/{total_pending} "
            f"| Failed: {stats['failed']} "
            f"| Cost: ${stats['total_cost']:.2f} "
            f"| Rate: {rate:.1f} img/s "
            f"| ETA: {eta/60:.1f} min"
        )

    # ── Summary ──────────────────────────────────────────────────────────
    elapsed = time.monotonic() - t_start
    print(f"\n{'='*60}")
    print(f"  ✅ Generation complete!")
    print(f"     Generated:  {stats['completed']}")
    print(f"     Failed:     {stats['failed']}")
    print(f"     Total cost: ${stats['total_cost']:.2f}")
    print(f"     Time:       {elapsed/60:.1f} minutes")
    print(f"     Output:     {output_dir.resolve()}")
    print(f"     Manifest:   {Path(MANIFEST_FILE).resolve()}")
    print(f"{'='*60}\n")


def _print_dry_run_stats(prompts: list[dict]):
    """Print detailed stats for dry run."""
    total = len(prompts)

    face = sum(1 for p in prompts if p["category"] == "face")
    scene = total - face

    print(f"\n  Category breakdown:")
    print(f"    Face:   {face} ({face/total*100:.1f}%)")
    print(f"    Scene:  {scene} ({scene/total*100:.1f}%)")

    print(f"\n  Quality breakdown:")
    for q in ["low", "medium", "high"]:
        c = sum(1 for p in prompts if p["quality"] == q)
        cost = c * COST_PER_IMAGE.get(q, 0)
        print(f"    {q:>8s}:  {c:>5} ({c/total*100:.1f}%)  → ${cost:.2f}")

    print(f"\n  Format breakdown:")
    for fmt in ["jpeg", "png", "webp"]:
        c = sum(1 for p in prompts if p["format"] == fmt)
        print(f"    {fmt:>8s}:  {c:>5} ({c/total*100:.1f}%)")

    print(f"\n  Sample prompts:")
    import random
    samples = random.sample(prompts, min(5, len(prompts)))
    for s in samples:
        print(f"    [{s['quality']:>6s}|{s['format']:>4s}] {s['prompt'][:90]}...")

    print()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate images from prompts.jsonl via OpenAI API",
        usage="%(prog)s [BUDGET] [options]",
    )
    parser.add_argument("budget", type=float, nargs="?", default=None,
                        help="Max dollars to spend (e.g. 10 = $10 worth of images)")
    parser.add_argument("--prompts", type=str, default=PROMPTS_FILE,
                        help=f"Path to prompts JSONL (default: {PROMPTS_FILE})")
    parser.add_argument("--start", type=int, default=0,
                        help="Start index (inclusive, default: 0)")
    parser.add_argument("--end", type=int, default=None,
                        help="End index (exclusive, default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Estimate cost without generating images")
    parser.add_argument("--concurrent", type=int, default=MAX_CONCURRENT,
                        help=f"Max concurrent requests (default: {MAX_CONCURRENT})")

    args = parser.parse_args()

    asyncio.run(run_pipeline(
        prompts_file=args.prompts,
        start=args.start,
        end=args.end,
        budget=args.budget,
        dry_run=args.dry_run,
        max_concurrent=args.concurrent,
    ))
