real#!/usr/bin/env python3
"""
respublica-gpt — Structured Prompt Generator (TRIED-Aligned)

Three output categories:
  - face    (50%) — portraits and people shots
  - scene   (25%) — populated real-world settings
  - nature  (25%) — landscapes, objects, architecture, documents

30+ distinct photo types for maximum diversity.
"""

import json
import random
from pathlib import Path

from config import (
    TOTAL_IMAGES,
    QUALITIES,
    FORMATS,
    PROMPTS_FILE,
    COST_PER_IMAGE,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Category ratios
# ═══════════════════════════════════════════════════════════════════════════════
FACE_RATIO = 0.50
SCENE_RATIO = 0.25
NATURE_RATIO = 0.25

# ═══════════════════════════════════════════════════════════════════════════════
# Factor pools
# ═══════════════════════════════════════════════════════════════════════════════

# ── Demographics (faces) ─────────────────────────────────────────────────────
AGES = ["young", "middle-aged", "elderly"]

GENDER_PRESENTATIONS = ["man", "woman", "person"]

ETHNICITIES = [
    "West African", "East African", "Afro-Caribbean", "African American",
    "East Asian", "South Asian", "Southeast Asian", "Central Asian",
    "Middle Eastern", "North African", "Indigenous", "Latino",
    "Northern European", "Southern European", "Eastern European",
    "Pacific Islander",
]

SKIN_TONES = [
    "very light skin", "light skin", "medium skin", "olive skin",
    "brown skin", "dark brown skin", "very dark skin",
]

# ── Scene subjects (people-centric but not face-focused) ─────────────────────
SCENE_SUBJECTS = [
    "a crowded market street",
    "a busy city intersection",
    "a classroom full of students",
    "a restaurant interior with diners",
    "a protest march with crowds",
    "a family gathering around a table",
    "a concert audience",
    "a hospital waiting room",
    "a train station platform during rush hour",
    "a group photo at an event",
    "a wedding reception",
    "a beach with people",
    "a press conference with reporters",
    "a video call screenshot with multiple participants",
    "a sports stadium crowd",
    "people walking through a shopping mall",
    "commuters on a subway car",
    "children playing in a schoolyard",
    "a street market with vendors and shoppers",
    "an outdoor cafe with patrons",
    "a gym with people exercising",
    "a library reading room with students",
    "a music festival crowd at night",
    "a farmers market on a weekend morning",
    "a busy airport terminal with travelers",
    "a swimming pool with people around it",
    "a graduation ceremony audience",
    "a courtroom during a hearing",
    "a church congregation during service",
    "a barbershop with customers waiting",
]

# ── Nature / object / architecture subjects ──────────────────────────────────
NATURE_SUBJECTS = [
    # Landscapes
    "a mountain range at sunset",
    "a dense forest trail",
    "an ocean coastline with waves crashing on rocks",
    "a desert landscape with sand dunes",
    "a frozen lake surrounded by snow-covered trees",
    "a tropical beach with palm trees",
    "rolling green hills under a cloudy sky",
    "a river winding through a valley",
    "a volcanic landscape with steam vents",
    "a savanna with acacia trees",
    "a canyon with red rock formations",
    "a waterfall in a tropical jungle",
    "a northern lights aurora over a snowy field",
    "a coral reef seen from below the water surface",
    "a field of wildflowers in spring",
    # Urban / architecture
    "a city skyline at night",
    "an old European cathedral exterior",
    "a modern glass skyscraper reflecting clouds",
    "an abandoned building with broken windows",
    "a narrow cobblestone alley between old buildings",
    "a colorful row of townhouses",
    "a bridge over a river at twilight",
    "a neon-lit street in a city at night",
    "a subway station tunnel with graffiti",
    "a row of parked cars on a residential street",
    # Objects / still life
    "a close-up of a handwritten letter on aged paper",
    "a table with scattered documents and a coffee cup",
    "a car parked on a suburban street",
    "a plate of food on a restaurant table",
    "a smartphone screen displaying a social media feed",
    "a stack of old photographs",
    "a street sign at an intersection",
    "a pair of shoes on a doorstep",
    "a bookshelf filled with old books",
    "the interior of a car dashboard at night",
    # Documents / text
    "a printed newspaper front page",
    "an ID card or passport lying on a table",
    "a whiteboard with handwritten notes",
    "a protest sign with hand-painted text",
    "a billboard advertisement on a highway",
    "a receipt or invoice on a countertop",
    "a menu board outside a restaurant",
    "a handwritten note on a refrigerator",
    # Animals / wildlife
    "a dog sitting on a front porch",
    "a cat sleeping on a windowsill",
    "a bird perched on a fence",
    "a horse standing in a pasture",
]

# ── Photo types — split by what makes sense per category ─────────────────────

# Universal: works for faces, scenes, AND nature
PHOTO_TYPES_UNIVERSAL = [
    # Common everyday capture
    "smartphone photo",
    "smartphone photo",               # weighted — most common
    "selfie",
    "tablet camera photo",
    # Professional
    "DSLR photo",
    "mirrorless camera photo",
    "medium format film photo",
    "large format film photo",
    # Photojournalism / documentary
    "photojournalist shot",
    "documentary-style photo",
    "street photography shot",
    "candid photo taken from a distance",
    # Surveillance / security
    "security camera CCTV footage",
    "dashcam footage",
    "doorbell camera capture",
    # Action cameras
    "GoPro wide-angle action shot",
    "helmet-mounted camera capture",
    # Screen-mediated
    "video still frame",
    "screen recording or screenshot",
    "photo of a screen showing another image",
    "scanned printed photograph",
    "photo taken of a TV screen",
    "low quality compressed webcam image",
    # Vintage / alternative
    "Polaroid instant photo",
    "disposable camera photo",
    "black and white film photo",
    "infrared camera image",
    "night vision camera image",
    # Mobile / app-filtered
    "photo with Instagram-style filter applied",
    "panoramic photo",
    "HDR photo with tone-mapped highlights",
    # Point-and-shoot / older tech
    "point-and-shoot digital camera photo",
    "old flip phone camera photo",
    "early 2000s digital camera photo",
    # Aerial
    "drone aerial photo",
]

# Face-only: contextual photo types that make sense for people
PHOTO_TYPES_FACE_ONLY = [
    "selfie taken with front-facing camera",
    "professional studio portrait",
    "paparazzi-style telephoto shot",
    "body camera footage",
    "passport photo or ID headshot",
    "school yearbook photo",
    "employee badge photo",
    "dating app profile photo",
    "LinkedIn headshot",
    "mugshot-style photo",
    "medical clinical photo",
    "webcam image from a video call",
    "livestream thumbnail capture",
    "photo with heavy beauty filter",
    "portrait mode photo with artificial bokeh",
]

# Nature/scene-only: photo types for objects, places, things
PHOTO_TYPES_NATURE_SCENE_ONLY = [
    "real estate listing photo",
    "product photography on white background",
    "food photography close-up",
    "underwater camera photo",
    "thermal imaging camera capture",
    "satellite imagery",
    "ATM security camera image",
    "parking lot surveillance camera footage",
]

# ── Lighting ─────────────────────────────────────────────────────────────────
LIGHTING = [
    "soft natural daylight",
    "harsh overhead fluorescent lighting",
    "very low ambient light",
    "neon lighting",
    "golden hour sunlight",
    "backlit with rim lighting",
    "mixed indoor-outdoor lighting",
    "dramatic side lighting",
    "flat overcast daylight",
    "candlelight",
    "direct flash",
    "nighttime artificial lighting",
    "screen-lit in a dark room",
    "dappled shade under trees",
    "tungsten indoor lighting with warm cast",
    "blue hour twilight",
]

# ── Backgrounds (face prompts only) ──────────────────────────────────────────
BACKGROUNDS = [
    "plain studio background",
    "busy street",
    "office environment",
    "outdoor park",
    "dimly lit room",
    "inside a vehicle",
    "home interior",
    "conference stage",
    "hospital corridor",
    "construction site",
    "cafe or restaurant",
    "government building",
    "bathroom mirror",
    "bedroom",
    "rooftop with skyline",
    "parking garage",
    "grocery store aisle",
    "gym or fitness center",
    "stairwell",
    "elevator",
]

# ── Artifacts / distortion ───────────────────────────────────────────────────
ARTIFACTS = [
    "",  # clean
    "",  # extra clean weight
    "",  # extra clean weight
    "slight motion blur",
    "heavy JPEG compression artifacts",
    "overexposed highlights",
    "inconsistent shadows",
    "lens distortion",
    "chromatic aberration",
    "heavy noise or grain",
    "color banding",
    "digital zoom pixelation",
]

# ── Platform degradation (~30% of prompts) ───────────────────────────────────
PLATFORM_DEGRADATION = [
    "", "", "", "", "", "", "",
    "as if shared on WhatsApp with compression",
    "as if downloaded from Instagram",
    "as if shared on Twitter with reduced resolution",
    "as if forwarded on Telegram multiple times",
    "as if screenshotted from TikTok",
    "as if saved from a YouTube video at 480p",
]

# ── Edge cases (face prompts only) ───────────────────────────────────────────
EDGE_CASES = [
    "", "", "", "", "", "", "",
    "face partially occluded",
    "wearing sunglasses",
    "extreme close-up",
    "face at sharp angle",
    "multiple faces overlapping",
    "face reflected in mirror",
    "face through glass",
    "face partially in shadow",
    "face mid-expression with motion blur",
    "face very small in frame",
    "face on a screen within the image",
]

# ═══════════════════════════════════════════════════════════════════════════════
# Prompt construction
# ═══════════════════════════════════════════════════════════════════════════════

def _build_face_prompt() -> tuple[str, dict]:
    """Build a face prompt. Skin tone added ~40% of the time."""
    age = random.choice(AGES)
    gender = random.choice(GENDER_PRESENTATIONS)
    ethnicity = random.choice(ETHNICITIES)
    lighting = random.choice(LIGHTING)
    background = random.choice(BACKGROUNDS)
    photo_type = random.choice(PHOTO_TYPES_UNIVERSAL + PHOTO_TYPES_FACE_ONLY)
    artifact = random.choice(ARTIFACTS)
    edge_case = random.choice(EDGE_CASES)
    platform = random.choice(PLATFORM_DEGRADATION)

    use_skin_tone = random.random() < 0.40
    skin_tone = random.choice(SKIN_TONES) if use_skin_tone else ""

    if skin_tone:
        subject = f"{age} {ethnicity} {gender} with {skin_tone}"
    else:
        subject = f"{age} {ethnicity} {gender}"

    parts = [f"A {photo_type} of a {subject} in {background}"]
    parts.append(f"with {lighting}")
    if artifact:
        parts.append(artifact)
    if edge_case:
        parts.append(edge_case)
    if platform:
        parts.append(platform)

    prompt = ", ".join(parts)
    meta = dict(
        category="face",
        age=age,
        gender_presentation=gender,
        ethnicity=ethnicity,
        skin_tone=skin_tone,
        lighting=lighting,
        background=background,
        photo_type=photo_type,
        artifact=artifact,
        edge_case=edge_case,
        platform_degradation=platform,
    )
    return prompt, meta


def _build_scene_prompt() -> tuple[str, dict]:
    """Build a people-scene prompt."""
    scene = random.choice(SCENE_SUBJECTS)
    lighting = random.choice(LIGHTING)
    photo_type = random.choice(PHOTO_TYPES_UNIVERSAL + PHOTO_TYPES_NATURE_SCENE_ONLY)
    artifact = random.choice(ARTIFACTS)
    platform = random.choice(PLATFORM_DEGRADATION)

    parts = [f"A {photo_type} of {scene}"]
    parts.append(f"with {lighting}")
    if artifact:
        parts.append(artifact)
    if platform:
        parts.append(platform)

    prompt = ", ".join(parts)
    meta = dict(
        category="scene",
        scene_subject=scene,
        lighting=lighting,
        photo_type=photo_type,
        artifact=artifact,
        platform_degradation=platform,
    )
    return prompt, meta


def _build_nature_prompt() -> tuple[str, dict]:
    """Build a nature/object/architecture prompt."""
    subject = random.choice(NATURE_SUBJECTS)
    lighting = random.choice(LIGHTING)
    photo_type = random.choice(PHOTO_TYPES_UNIVERSAL + PHOTO_TYPES_NATURE_SCENE_ONLY)
    artifact = random.choice(ARTIFACTS)
    platform = random.choice(PLATFORM_DEGRADATION)

    parts = [f"A {photo_type} of {subject}"]
    parts.append(f"with {lighting}")
    if artifact:
        parts.append(artifact)
    if platform:
        parts.append(platform)

    prompt = ", ".join(parts)
    meta = dict(
        category="nature",
        scene_subject=subject,
        lighting=lighting,
        photo_type=photo_type,
        artifact=artifact,
        platform_degradation=platform,
    )
    return prompt, meta


def generate_prompts(n: int = TOTAL_IMAGES, seed: int = 42) -> list[dict]:
    """Generate n prompt entries with factorized sampling."""
    random.seed(seed)

    n_face = int(n * FACE_RATIO)
    n_scene = int(n * SCENE_RATIO)
    n_nature = n - n_face - n_scene

    quality_assignments = _equal_distribute(QUALITIES, n)
    format_assignments = _equal_distribute(FORMATS, n)
    random.shuffle(quality_assignments)
    random.shuffle(format_assignments)

    entries = []
    for i in range(n):
        if i < n_face:
            prompt_text, meta = _build_face_prompt()
        elif i < n_face + n_scene:
            prompt_text, meta = _build_scene_prompt()
        else:
            prompt_text, meta = _build_nature_prompt()

        quality = quality_assignments[i]
        fmt = format_assignments[i]
        compression = random.randint(30, 100) if fmt in ("jpeg", "webp") else 100

        entries.append(dict(
            index=i,
            prompt=prompt_text,
            quality=quality,
            format=fmt,
            compression=compression,
            category=meta["category"],
            metadata=meta,
        ))

    random.shuffle(entries)
    for i, entry in enumerate(entries):
        entry["index"] = i

    return entries


def _equal_distribute(items: list, n: int) -> list:
    base = n // len(items)
    remainder = n % len(items)
    result = []
    for i, item in enumerate(items):
        count = base + (1 if i < remainder else 0)
        result.extend([item] * count)
    return result


def save_prompts(entries: list[dict], path: str = PROMPTS_FILE):
    p = Path(path)
    with p.open("w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return p


def print_stats(entries: list[dict]):
    total = len(entries)
    face = sum(1 for e in entries if e["category"] == "face")
    scene = sum(1 for e in entries if e["category"] == "scene")
    nature = sum(1 for e in entries if e["category"] == "nature")

    print(f"\n{'='*60}")
    print(f"  respublica-gpt Prompt Generator — Statistics")
    print(f"{'='*60}")
    print(f"  Total:    {total:,}")
    print(f"  Face:     {face:,}  ({face/total*100:.1f}%)")
    print(f"  Scene:    {scene:,}  ({scene/total*100:.1f}%)")
    print(f"  Nature:   {nature:,}  ({nature/total*100:.1f}%)")

    print(f"\n  Quality:")
    for q in QUALITIES:
        c = sum(1 for e in entries if e["quality"] == q)
        print(f"    {q:>8s}:  {c:,}  ({c/total*100:.1f}%)")

    print(f"\n  Format:")
    for fmt in FORMATS:
        c = sum(1 for e in entries if e["format"] == fmt)
        print(f"    {fmt:>8s}:  {c:,}  ({c/total*100:.1f}%)")

    # Photo type distribution
    print(f"\n  Photo type distribution (top 15):")
    type_counts = {}
    for e in entries:
        pt = e["metadata"].get("photo_type", "unknown")
        type_counts[pt] = type_counts.get(pt, 0) + 1
    for pt, c in sorted(type_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"    {pt:>45s}: {c:>4} ({c/total*100:.1f}%)")
    remaining = len(type_counts) - 15
    if remaining > 0:
        print(f"    {'... and ' + str(remaining) + ' more types':>45s}")

    # Face stats
    face_entries = [e for e in entries if e["category"] == "face"]
    if face_entries:
        with_skin = sum(1 for e in face_entries if e["metadata"].get("skin_tone"))
        print(f"\n  Face prompts with explicit skin tone: {with_skin}/{len(face_entries)} ({with_skin/len(face_entries)*100:.0f}%)")

    degraded = sum(1 for e in entries if e["metadata"].get("platform_degradation", ""))
    print(f"  With platform degradation: {degraded}/{total} ({degraded/total*100:.0f}%)")

    edged = sum(1 for e in face_entries if e["metadata"].get("edge_case", ""))
    print(f"  Face prompts with edge case: {edged}/{len(face_entries)} ({edged/len(face_entries)*100:.0f}%)")

    est = sum(COST_PER_IMAGE.get(e["quality"], 0) for e in entries)
    print(f"\n  Unique photo types: {len(type_counts)}")
    print(f"  Estimated API cost:  ${est:,.2f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate structured prompts for respublica-gpt")
    parser.add_argument("-n", "--count", type=int, default=TOTAL_IMAGES,
                        help=f"Number of prompts (default: {TOTAL_IMAGES})")
    parser.add_argument("-o", "--output", type=str, default=PROMPTS_FILE,
                        help=f"Output JSONL path (default: {PROMPTS_FILE})")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    args = parser.parse_args()

    entries = generate_prompts(n=args.count, seed=args.seed)
    path = save_prompts(entries, args.output)
    print_stats(entries)
    print(f"  Saved to: {path.resolve()}\n")
