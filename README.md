<div align="center">

# respublica-gpt

**3,000 AI-generated images for deepfake detection research**

Built with OpenAI `gpt-image-2` (April 2026) · Aligned with the [WITNESS TRIED Benchmark](https://arxiv.org/abs/2504.21489)

[![License: Research Only](https://img.shields.io/badge/license-Research%20Only-red.svg)](LICENSE)
[![Images](https://img.shields.io/badge/images-3%2C000-blue.svg)]()
[![Model](https://img.shields.io/badge/model-gpt--image--2-10a37f.svg)](https://openai.com/gpt-image-2)
[![TRIED Aligned](https://img.shields.io/badge/TRIED%20Benchmark-Aligned-orange.svg)](https://arxiv.org/abs/2504.21489)
[![Formats](https://img.shields.io/badge/formats-JPEG%20%7C%20PNG%20%7C%20WebP-lightgrey.svg)]()
[![Size](https://img.shields.io/badge/size-~3%20GB-informational.svg)]()

</div>

---

## Overview

respublica-gpt is a **factorized, TRIED-aligned dataset** of 3,000 synthetic images generated using OpenAI's most capable image model. Every image is paired with full structured metadata — model quality, format, compression level, camera style, lighting, demographic attributes, platform degradation, and more — making it uniquely suited for training and benchmarking deepfake detection systems.

| Stat | Value |
|------|-------|
| **Total images** | 3,000 |
| **Categories** | Face (50%) · Scene (25%) · Nature/context (25%) |
| **Formats** | Equal thirds: JPEG · PNG · WebP |
| **Quality levels** | Equal thirds: Low · Medium · High |
| **Generation model** | `gpt-image-2` (OpenAI, April 2026) |
| **Metadata per image** | 10+ structured fields |
| **Combinatorial space** | ~236 billion unique face prompts |
| **Benchmark alignment** | WITNESS TRIED §5.1, §5.2, §5.4 |

---

## Download

Images are hosted on Google Drive due to size (~3 GB total). Use the helper script for a one-command download:

```bash
pip install gdown tqdm
python download.py
```

Or download individual archives:

| Archive | Contents | Size | Link |
|---------|----------|------|------|
| `opendeepfake_faces.zip` | 1,500 face images | ~1.4 GB | [Download](https://drive.google.com/uc?id=GDRIVE_FACES_ID&export=download) |
| `opendeepfake_scenes.zip` | 750 scene images | ~0.8 GB | [Download](https://drive.google.com/uc?id=GDRIVE_SCENES_ID&export=download) |
| `opendeepfake_nature.zip` | 750 nature/context images | ~0.8 GB | [Download](https://drive.google.com/uc?id=GDRIVE_NATURE_ID&export=download) |
| `opendeepfake_metadata.zip` | prompts.jsonl · prompts.csv · manifest.jsonl · README | ~3 MB | [Download](https://drive.google.com/uc?id=GDRIVE_METADATA_ID&export=download) |

> Metadata files (`prompts.jsonl`, `manifest.jsonl`) are also committed directly to this repository.

---

## Dataset Structure

```
respublica-gpt/
├── images/
│   ├── faces/          # 1,500 face-centered images
│   ├── scene/          # 750 group/context scene images
│   └── nature/         # 750 nature/environmental images
├── prompts.jsonl       # All 3,000 prompts + structured metadata (source of truth)
├── prompts.csv         # Same data, flattened — one column per axis, opens in Excel/Sheets
├── manifest.jsonl      # Per-image generation record (timing, size, cost)
├── download.py         # One-command dataset downloader
├── prompt_builder.py   # TRIED-aligned prompt generator (reproduce prompts)
├── generate_images.py  # Async generation pipeline (reproduce images)
└── config.py           # Generation configuration
```

### File naming

```
{index:05d}_{category}.{format}
# e.g. 00042_face.jpeg, 01337_scene.png, 02500_nature.webp
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
    "category": "face",
    "age": "middle-aged",
    "gender_presentation": "person",
    "ethnicity": "Middle Eastern",
    "skin_tone": "medium-dark skin",
    "lighting": "harsh overhead fluorescent",
    "background": "office interior",
    "photo_type": "security camera CCTV footage",
    "artifact": "heavy JPEG compression",
    "edge_case": "face partially in shadow",
    "platform_degradation": "as if shared on WhatsApp"
  }
}
```

Each line of `manifest.jsonl` additionally includes:

```json
{
  "filename": "00042_face.jpeg",
  "file_size_bytes": 145302,
  "generation_time_s": 84.2,
  "timestamp": "2026-05-01T12:34:56Z"
}
```

---

## Prompt Taxonomy

Prompts are factorized across **11 detection-relevant axes**. Every axis value is recorded in metadata, enabling fine-grained stratified evaluation.

### Face images (1,500)

| Axis | Values | Count |
|------|--------|-------|
| **Ethnicity** | Arab, Bengali, Brazilian, Chinese, East African, Filipino, German, Haitian, Indian, Indonesian, Iranian, Japanese, Korean, Mexican, Nigerian, Pakistani, Peruvian, Russian, Turkish, Vietnamese | 20 |
| **Skin tone** | Fitzpatrick I–VI (very light → very dark) | 7 |
| **Age** | Child, young adult, middle-aged, older adult, elderly | 5 |
| **Gender presentation** | Man, woman, androgynous person | 3 |
| **Camera style** | DSLR, iPhone, CCTV, dashcam, webcam, screen recording, polaroid, film grain... | 14 |
| **Lighting** | Natural, neon, fluorescent, candlelight, screen-lit, golden hour, low ambient... | 14 |
| **Background** | Studio, home interior, office, urban street, rural farmland, place of worship... | 16 |
| **Artifact** | Clean, slight blur, heavy JPEG, rolling shutter, noise/grain, overexposed... | 14 |
| **Edge case** | Occlusion, reflection, crowd, partial shadow, off-angle, extreme close-up... | 22 |
| **Platform degradation** | WhatsApp, Instagram, TikTok, Telegram, Twitter/X, none | 9 |
| **Cultural context** | Traditional attire, hijab, turban, religious garment, military uniform... | 13 |

### Scene & nature images (1,500)

| Axis | Values | Count |
|------|--------|-------|
| **Scene subject** | Political rally, market, classroom, protest, wedding, subway, courtroom... | 25 |
| **Camera style** | Documentary, broadcast news, dashcam, drone, CCTV, HDR, film grain... | 14 |
| **Lighting** | Golden hour, neon, screen-lit, fluorescent, candlelight, overcast... | 14 |
| **Artifact** | JPEG compression, motion blur, overexposure, noise, rolling shutter... | 14 |
| **Platform degradation** | WhatsApp, TikTok, Instagram, Twitter/X, screenshotted, none | 9 |

---

## TRIED Benchmark Alignment

This dataset is designed following the [WITNESS TRIED Benchmark](https://arxiv.org/abs/2504.21489) — a sociotechnical framework for evaluating AI detection tools.

| TRIED Principle | How respublica-gpt Addresses It |
|---|---|
| **§5.4 Fairness** | 20 ethnic groups centering Global Majority; 7 skin tones (Fitzpatrick I–VI); balanced demographic sampling to stress-test bias documented in detection systems that underperform on non-Caucasian faces |
| **§5.1 Real-World Conditions** | Platform degradation simulation (WhatsApp, Instagram, TikTok); diverse compression levels; low-resolution, screen-captured, and heavily formatted variants |
| **§5.1 Diverse Training Data** | 14 camera styles spanning DSLR through dashcam through CCTV; 25 scene subjects from Lagos, Mumbai, Bangkok, Mexico City, Marrakech, Jakarta |
| **§5.2 Transparency** | Full structured metadata per image (prompt, quality, format, compression, all axis values) published in `prompts.jsonl` for complete reproducibility |
| **§5.4 Global Majority** | Scene subjects explicitly include global contexts — not defaulting to Western environments |

---

## Ethical Framework

> **All images are entirely AI-generated.** No real person's likeness, biometric data, or identity is captured, referenced, or approximated.

Demographic descriptors (ethnicity, skin tone, age, gender presentation) are used **solely to ensure balanced visual representation** in training data for detection research — specifically to counteract the documented failure of detectors on underrepresented groups.

**Intended use:** Training and evaluating deepfake / synthetic media detection systems.

**Prohibited use:** Generating deceptive content, surveillance, biometric identification, or any use that infringes on human rights or dignity.

Researchers using this dataset are encouraged to read the [TRIED Benchmark](https://arxiv.org/abs/2504.21489) for a full sociotechnical framing of the detection problem.

---

## Reproducing the Dataset

The full generation pipeline is included. You can reproduce all prompts deterministically and regenerate images with any compatible model.

```bash
# 1. Install
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."

# 2. Regenerate prompts (deterministic)
python prompt_builder.py

# 3. Estimate cost before generating
python generate_images.py --dry-run

# 4. Generate (resumable — safe to interrupt)
python generate_images.py
```

**Approximate cost to reproduce:** ~$490 USD at April 2026 OpenAI pricing (low: $0.011/img · medium: $0.07/img · high: $0.041/img).

---

## Citation

If you use respublica-gpt in your research, please cite both this dataset and the TRIED Benchmark:

```bibtex
@dataset{opendeepfake2026,
  title     = {respublica-gpt: A TRIED-Aligned Synthetic Image Dataset for Deepfake Detection Research},
  author    = {RespublicaData},
  year      = {2026},
  url       = {https://github.com/RespublicaData/respublica-gpt},
  note      = {3,000 images generated with OpenAI gpt-image-2}
}

@article{anlen2025tried,
  title   = {TRIED: Truly Innovative and Effective AI Detection Benchmark},
  author  = {anlen, shirin and Wojciak, Zuzanna},
  journal = {arXiv preprint arXiv:2504.21489},
  year    = {2025}
}
```

---

## License

**Research use only.** See [LICENSE](LICENSE) for full terms.

Permitted: deepfake detection model training and evaluation, academic research, benchmarking.  
Not permitted: generating deceptive content, surveillance, biometric identification, or commercial use without explicit written permission.
# Respublica_GPT
