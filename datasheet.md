# Datasheet for respublica-gpt

*Following the format proposed by Gebru et al. (2021), "Datasheets for Datasets."*

---

## Motivation

**For what purpose was the dataset created?**  
respublica-gpt was created to provide a high-quality, demographically balanced, and richly annotated corpus of AI-generated images for training and evaluating deepfake / synthetic media detection systems. Existing datasets in this space are often demographically skewed (overrepresenting Western, light-skinned subjects), lack structured metadata, or were generated with older models that do not reflect current generation capability.

**Who created the dataset and on whose behalf?**  
Created by Respublica as an independent research contribution, with a focus on demographic diversity and Global Majority representation in deepfake detection research.

**Who funded the creation of the dataset?**  
Self-funded. Image generation costs approximately $490 USD at April 2026 OpenAI pricing.

---

## Composition

**What do the instances represent?**  
Each instance is a 1024×1024 AI-generated image paired with full structured metadata. No real person is depicted or referenced.

**How many instances are there?**  
2,797 images: approximately 1,400 face-centered, 700 scene/group, 700 nature/context.

**Does the dataset contain all possible instances or a sample?**  
A sample. The theoretical combinatorial space of the prompt taxonomy exceeds 236 billion unique face prompts. The 2,797 images are drawn to maximize axis coverage and demographic balance.

**What data does each instance consist of?**  
- A synthetic image (JPEG, PNG, or WebP at 1024×1024)
- A structured prompt record (`prompts.jsonl`) with 10+ metadata fields
- A generation record (`manifest.jsonl`) with filename, file size, generation time, and timestamp

**Is there a label or target associated with each instance?**  
All images are AI-generated. The label for detection purposes is uniformly `synthetic = true`. The metadata fields (quality, format, compression, artifact level, platform degradation) serve as fine-grained sub-labels for stratified evaluation.

**Is any information missing from individual instances?**  
Index 1447 and 1636 were rejected by the generation model (likely content policy). These are absent from the dataset; the metadata records are preserved in `prompts.jsonl` with no corresponding image.

**Are there recommended data splits?**  
No official splits are provided. Researchers are encouraged to stratify by category (face/scene/nature), quality (low/medium/high), and demographic axes when constructing train/validation/test splits.

**Are there any errors, sources of noise, or redundancies?**  
- Prompt-level diversity is guaranteed by design; visual-level diversity depends on the generation model's internal sampling.
- Platform degradation artifacts (WhatsApp, TikTok re-encoding simulations) are applied at prompt level, not post-processing. Actual codec behavior may differ from the model's simulation.

**Is the dataset self-contained?**  
Yes. All images, prompts, and generation metadata are included. External dependencies: none beyond standard image libraries.

---

## Collection Process

**How was the data associated with each instance acquired?**  
Each image was generated via the OpenAI Images API (`gpt-image-2`, April 2026) using a structured prompt sampled from the taxonomy defined in `prompt_builder.py`. Prompts are deterministic given the seed in the builder.

**What mechanisms or procedures were used to collect the data?**  
An async Python pipeline (`generate_images.py`) with configurable concurrency (5 parallel requests), exponential backoff on rate limits, and checkpoint-based resumption.

**Over what timeframe was the data collected?**  
April–May 2026.

**Were any ethical review processes conducted?**  
The generation pipeline was designed from the outset with demographic fairness as a primary constraint, with demographic fairness as a primary design constraint. No real biometric data was collected, inferred, or approximated at any point.

---

## Preprocessing / Cleaning / Labeling

**Was any preprocessing or cleaning of the data done?**  
Images are stored as returned by the API (base64-decoded to file). JPEG and WebP images use a compression level sampled per-image and recorded in metadata. No post-processing filters were applied.

**Is the software used to preprocess the data available?**  
Yes — `generate_images.py` and `prompt_builder.py` are included in this repository.

---

## Uses

**Has the dataset been used for any tasks already?**  
No. This is the initial public release.

**What (other) tasks could the dataset be used for?**  
- Training binary synthetic/real classifiers
- Benchmarking detection systems for demographic bias (stratify by ethnicity, skin tone)
- Studying the effect of image quality, compression, and platform degradation on detection accuracy
- Probing detection models for robustness to camera style or lighting variation
- Generating counterfactual evaluation sets (e.g., same subject, different platform degradation)

**Is there anything about the composition of the dataset or the way it was collected and preprocessed that might affect future uses?**  
- All images are from a single generative model (`gpt-image-2`). Detection systems trained exclusively on this data may overfit to artifacts specific to this model.
- The dataset contains no real images. Pairing with a real-image corpus is necessary to train binary detectors.
- Quality levels (low/medium/high) correspond to API quality parameters, not post-hoc resolution reduction. The perceptual difference between quality levels is model-defined.

**Are there tasks for which the dataset should not be used?**  
- Generating or augmenting deceptive media
- Surveillance or biometric identification
- Any use that attributes synthetic images to real individuals
- Commercial use without explicit written permission

---

## Distribution

**How will the dataset be distributed?**  
GitHub repository (metadata + code) + Google Drive (image archives). Both are publicly accessible.

**When will the dataset be distributed?**  
May 2026 (initial release).

**Will the dataset be distributed under a copyright or other intellectual property (IP) license?**  
Research use only — see [LICENSE](LICENSE).

**Have any third parties imposed IP-based or other restrictions on the data?**  
Images are generated via the OpenAI API. Usage is subject to OpenAI's Terms of Service. Researchers should review [OpenAI's usage policies](https://openai.com/policies/usage-policies) before use.

---

## Maintenance

**Who will be maintaining the dataset?**  
Respublica. Issues and corrections can be filed via GitHub Issues.

**How can the owner/curator be contacted?**  
Via GitHub Issues at [github.com/RespublicaData/respublica-gpt](https://github.com/RespublicaData/respublica-gpt).

**Will the dataset be updated?**  
Potentially — additional images with newer generation models, or expanded demographic coverage, may be released as versioned updates.

**Will older versions of the dataset continue to be supported?**  
The initial release (v1.0) will remain available. Newer versions will be tagged separately.

**If others want to extend, augment, build on, or contribute to the dataset, is there a mechanism for them to do so?**  
Yes — contributions via pull request. The full generation pipeline is included to allow reproducible extension.
