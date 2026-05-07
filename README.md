<div align="center">

# respublica-gpt

**A demographically diverse corpus of AI-generated images for deepfake detection research**

Built with OpenAI `gpt-image-2` · April–May 2026

[![License: Research Only](https://img.shields.io/badge/license-Research%20Only-red.svg)](LICENSE)
[![Images](https://img.shields.io/badge/images-2%2C797-blue.svg)]()
[![Model](https://img.shields.io/badge/model-gpt--image--2-10a37f.svg)](https://openai.com/gpt-image-2)
[![Formats](https://img.shields.io/badge/formats-JPEG%20%7C%20PNG%20%7C%20WebP-lightgrey.svg)]()
[![Size](https://img.shields.io/badge/size-~3%20GB-informational.svg)]()

</div>

---

## Why This Dataset Exists

Deepfake detection research has a representation problem.

Most synthetic image datasets — and the detectors trained on them — skew heavily toward Western subjects, lighter skin tones, and studio-quality photography. The result is a well-documented pattern: **detection systems fail disproportionately on faces from the Global Majority**. A tool that reliably catches AI-generated images of white faces in good lighting may miss the same manipulation applied to a dark-skinned face photographed under a streetlight, shared over WhatsApp, and viewed on a low-end phone.

This failure isn't just a technical shortcoming. Deepfake misinformation disproportionately targets political figures, activists, and communities in the Global South. If the detectors meant to catch it work best on the faces least likely to be targeted, the technology fails the people who need it most.

respublica-gpt is built to address that gap directly. Every axis of the prompt taxonomy — ethnicity, skin tone, lighting, camera quality, platform degradation — is designed to stress-test detection systems across the full range of real-world conditions, not just the ones that happen to be well-represented in existing benchmarks.

---

## Dataset Overview

| | |
|---|---|
| **Total images** | 2,797 |
| **Categories** | Face (50%) · Scene (25%) · Nature/context (25%) |
| **Ethnicities** | 20 — Arab, Bengali, Brazilian, Chinese, East African, Filipino, German, Haitian, Indian, Indonesian, Iranian, Japanese, Korean, Mexican, Nigerian, Pakistani, Peruvian, Russian, Turkish, Vietnamese |
| **Skin tones** | 7 (Fitzpatrick I through VI) |
| **Age groups** | 5 (child through elderly) |
| **Camera styles** | 14 (DSLR through CCTV through dashcam) |
| **Quality levels** | Equal thirds: Low · Medium · High |
| **Formats** | Equal thirds: JPEG · PNG · WebP |
| **Generation model** | `gpt-image-2` (OpenAI, April 2026) |
| **Metadata per image** | 10+ structured fields |

---

## Download

Images are hosted on Google Drive (~3 GB total). One-command download:

```bash
pip install gdown tqdm
python download.py
```

Or download individual archives:

| Archive | Contents | Size | Link |
|---------|----------|------|------|
| `opendeepfake_faces.zip` | ~1,400 face images | ~1.4 GB | [Download](https://drive.google.com/uc?id=GDRIVE_FACES_ID&export=download) |
| `opendeepfake_scenes.zip` | ~700 scene images | ~0.8 GB | [Download](https://drive.google.com/uc?id=GDRIVE_SCENES_ID&export=download) |
| `opendeepfake_nature.zip` | ~700 nature/context images | ~0.8 GB | [Download](https://drive.google.com/uc?id=GDRIVE_NATURE_ID&export=download) |
| `opendeepfake_metadata.zip` | prompts.jsonl · prompts.csv · manifest.jsonl | ~3 MB | [Download](https://drive.google.com/uc?id=GDRIVE_METADATA_ID&export=download) |

> `prompts.jsonl` and `prompts.csv` are also committed directly to this repository.

---

## Diversity Design

### Demographic coverage

The face subset (50% of the dataset) is built around 20 ethnicities drawn primarily from the Global Majority, combined with 7 skin tone levels to ensure coverage of the tones where detector bias is most pronounced. Gender presentation (man, woman, androgynous person) and age (child through elderly) are sampled uniformly.

The goal is not token representation — it is **stress coverage**. Each ethnicity × skin tone combination should appear across the full range of lighting conditions, camera qualities, and artifact levels, so that a detector's failure on dark skin in low light is detectable as a failure mode rather than hidden by aggregate accuracy.

### Platform degradation

Real-world deepfakes don't circulate as pristine PNGs. They are screenshotted, re-encoded by WhatsApp, reposted through TikTok's compression pipeline, and viewed on devices with inconsistent color profiles. respublica-gpt encodes this directly: 9 platform degradation conditions (WhatsApp, Instagram, TikTok, Telegram, Twitter/X, and others) are applied at the prompt level, producing images that simulate how synthetic media actually looks by the time a detector sees it.

### Scene diversity

The 25% scene subset includes global contexts — Lagos markets, Mumbai classrooms, Bangkok protests, Mexico City courthouses — rather than defaulting to Western environments. A detector that learns "political rally" from US footage may perform differently on a similar scene shot at a different latitude.

---

## Prompt Taxonomy

All prompts are factorized across **11 detection-relevant axes**. Full metadata for every image is in `prompts.jsonl` (nested) and `prompts.csv` (flat, one column per axis — opens directly in Excel or Sheets).

### Face axis coverage

| Axis | Count | Values (sample) |
|------|-------|-----------------|
| Ethnicity | 20 | Arab, Bengali, East African, Filipino, Haitian, Indonesian... |
| Skin tone | 7 | Fitzpatrick I (very light) → VI (very dark) |
| Age | 5 | Child, young adult, middle-aged, older adult, elderly |
| Gender presentation | 3 | Man, woman, androgynous person |
| Camera style | 14 | DSLR, iPhone, CCTV, dashcam, webcam, film grain, polaroid... |
| Lighting | 14 | Natural, neon, fluorescent, candlelight, screen-lit, golden hour... |
| Background | 16 | Studio, home interior, office, urban street, rural farmland... |
| Artifact | 14 | Clean, slight blur, heavy JPEG, rolling shutter, noise, overexposed... |
| Edge case | 22 | Occlusion, reflection, crowd, partial shadow, extreme close-up... |
| Platform degradation | 9 | WhatsApp, Instagram, TikTok, Telegram, Twitter/X, none |
| Cultural context | 13 | Traditional attire, hijab, turban, religious garment, military... |

### Scene / nature axis coverage

| Axis | Count | Values (sample) |
|------|-------|-----------------|
| Scene subject | 25 | Political rally, market, classroom, protest, wedding, courtroom... |
| Camera style | 14 | Documentary, broadcast news, dashcam, drone, CCTV, HDR... |
| Lighting | 14 | Golden hour, neon, screen-lit, fluorescent, candlelight... |
| Artifact | 14 | JPEG compression, motion blur, overexposure, noise, rolling shutter... |
| Platform degradation | 9 | WhatsApp, TikTok, Instagram, Twitter/X, screenshotted, none |

---

## Repository Structure

```
respublica-gpt/
├── images/                    # Downloaded separately (see above)
│   ├── faces/
│   ├── scene/
│   └── nature/
├── prompts.jsonl              # All prompts + full structured metadata
├── prompts.csv                # Same data, flat — one column per axis
├── manifest.jsonl             # Per-image generation record
├── download.py                # Dataset downloader
├── prompt_builder.py          # Prompt generator — reproduce or extend the taxonomy
├── generate_images.py         # Async generation pipeline
├── export_csv.py              # Regenerate prompts.csv from prompts.jsonl
├── package.py                 # Build zip archives for Drive upload
├── upload_gdrive.py           # Upload archives to Google Drive
├── update_links.py            # Patch Drive file IDs into README + download.py
└── config.py                  # Generation configuration
```

### Metadata schema

Each line of `prompts.jsonl`:

```json
{
  "index": 42,
  "prompt": "A security camera CCTV footage of a middle-aged Middle Eastern person...",
  "quality": "high",
  "format": "jpeg",
  "compression": 85,
  "category": "face",
  "metadata": {
    "ethnicity": "Middle Eastern",
    "skin_tone": "medium-dark skin",
    "age": "middle-aged",
    "gender_presentation": "person",
    "lighting": "harsh overhead fluorescent",
    "background": "office interior",
    "photo_type": "security camera CCTV footage",
    "artifact": "heavy JPEG compression",
    "edge_case": "face partially in shadow",
    "platform_degradation": "as if shared on WhatsApp"
  }
}
```

---

## Reproducing the Dataset

The full generation pipeline is included. You can regenerate all prompts deterministically or generate additional images with any compatible model.

```bash
# Install
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."

# Regenerate prompts (deterministic)
python prompt_builder.py

# Estimate cost before generating
python generate_images.py --dry-run

# Generate — safe to interrupt and resume
python generate_images.py

# Export flat CSV from prompts.jsonl
python export_csv.py
```

**Approximate cost to reproduce:** ~$490 USD at April 2026 OpenAI pricing (low: $0.011/img · medium: $0.07/img · high: $0.041/img).

---

## Ethical Statement

> **All images are entirely AI-generated.** No real person's likeness, biometric data, or identity is captured, referenced, or approximated.

Demographic descriptors (ethnicity, skin tone, age, gender presentation) exist exclusively to ensure that the dataset covers the range of human appearance that detection systems will encounter in practice — with particular emphasis on the groups where existing tools are documented to underperform.

**Intended use:** Training and evaluating synthetic media detection systems. Academic research and benchmarking.

**Prohibited use:** Generating deceptive content, surveillance, biometric identification, or any commercial or harmful application.

---

## Citation

```bibtex
@dataset{respublicagpt2026,
  title     = {respublica-gpt: A Demographically Diverse Synthetic Image Dataset for Deepfake Detection Research},
  author    = {RespublicaData},
  year      = {2026},
  url       = {https://github.com/RespublicaData/respublica-gpt},
  note      = {2,797 images generated with OpenAI gpt-image-2}
}
```

---

## License

Research use only. See [LICENSE](LICENSE).
