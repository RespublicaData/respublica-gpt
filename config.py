"""
respublica-gpt — Centralized Configuration
"""

# ─── Model ───────────────────────────────────────────────────────────────────
MODEL = "gpt-image-2"
SIZE = "1024x1024"

# ─── Dataset ─────────────────────────────────────────────────────────────────
TOTAL_IMAGES = 3000

# ─── Quality / format distribution (equal thirds) ───────────────────────────
QUALITIES = ["low", "medium", "high"]
FORMATS = ["jpeg", "png", "webp"]

# ─── Output ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = "images"
PROMPTS_FILE = "prompts.jsonl"
MANIFEST_FILE = "manifest.jsonl"
PROGRESS_FILE = "progress.json"

# ─── Rate limiting / concurrency ─────────────────────────────────────────────
MAX_CONCURRENT = 5
RETRY_BASE_DELAY = 2.0     # seconds
MAX_RETRIES = 5

# ─── Cost estimates (USD per image, approximate) ─────────────────────────────
COST_PER_IMAGE = {
    "low": 0.01,
    "medium": 0.07,
    "high": 0.41,
}
