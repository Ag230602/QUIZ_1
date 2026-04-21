# Controlled Stable Diffusion for E-Commerce Product Image Generation

Final submission for **Option 1: E-Commerce Product Image Generation**.

This repository implements a controlled Stable Diffusion pipeline that maps structured product metadata to prompts, compares baseline vs improved prompting, and evaluates outputs with required metrics and failure analysis.

## Final Links

- GitHub Repository URL: **https://github.com/Ag230602/QUIZ_1**
- Demo Video URL (1–2 min): **https://youtu.be/-A7iRCGIlCc**

---

## Project Innovation

The core innovation is a **data-driven control framework** for diffusion-based e-commerce generation:
- structured metadata → structured prompt mapping
- explicit control using negative prompts
- baseline vs improved evaluation with measurable trade-offs

This moves the project from “image generation demo” to an auditable system with analysis.

---

## Requirement Coverage (Quick Matrix)

| Requirement | Status | Evidence |
|---|---|---|
| Stable Diffusion pipeline | ✅ | `src/generate.py`, `configs/default.yaml` |
| Control mechanism | ✅ | structured prompts + negative prompt in `src/prompt_builder.py` and `configs/default.yaml` |
| Data-to-prompt mapping | ✅ | `data/sample_products.csv`, `src/prompt_builder.py` |
| Multiple images per product | ✅ | `generation.num_images_per_prompt` in `configs/default.yaml` |
| Baseline vs improved comparison | ✅ | `src/evaluate.py`, `results/evaluation_summary.csv` |
| Prompt alignment metric | ✅ | `results/evaluation_summary.csv` |
| Consistency metric | ✅ | `results/evaluation_summary.csv` |
| Diversity metric | ✅ | `results/evaluation_summary.csv` |
| Quality metric (proxy + qualitative template) | ✅ | `results/evaluation_summary.csv`, `results/qualitative_review_template.csv` |
| Failure cases and analysis | ✅ | `results/failure_cases.csv` |
| PPT (10+ slides) | ✅ | `slides/Stable_Diffusion_Ecommerce_Starter.pptx` |
| AI tools disclosure | ✅ | `docs/ai_tool_disclosure.md` |
| Demo video | ✅ | `docs/demo_video_script.md` + final video link in this README |
| Bonus multimodal extension | ✅ | `src/multimodal_pipeline.py`, `src/speech_to_image.py`, `src/image_to_text.py`, `src/image_to_video.py` |

---

## Repository Structure

```text
sd_ecommerce_submission/
├── README.md
├── requirements.txt
├── configs/
│   └── default.yaml
├── data/
│   └── sample_products.csv
├── docs/
│   ├── methodology.md
│   ├── submission_slide_outline.md
│   ├── ultimate_submission_package.md
│   ├── final_readiness_checklist.md
│   ├── ai_tool_disclosure.md
│   └── demo_video_script.md
├── outputs/
│   ├── baseline/
│   └── structured/
├── results/
│   ├── evaluation_summary.csv
│   ├── evaluation_details.csv
│   ├── failure_cases.csv
│   ├── qualitative_review_template.csv
│   ├── baseline_vs_structured.png
│   └── all_prompts_and_outputs.md
├── sample_outputs/
├── slides/
│   ├── Stable_Diffusion_Ecommerce_Starter.pptx
│   └── make_deck.js
└── src/
    ├── generate.py
    ├── prompt_builder.py
    ├── evaluate.py
    ├── compare_baseline.py
    ├── export_prompts_outputs.py
    ├── multimodal_pipeline.py
    ├── speech_to_image.py
    ├── image_to_text.py
    ├── image_to_video.py
    └── utils.py
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Run Commands

### 1) Generate Baseline

```bash
python src/generate.py --config configs/default.yaml --mode baseline
```

### 2) Generate Structured (Improved)

```bash
python src/generate.py --config configs/default.yaml --mode structured
```

### 3) Evaluate Baseline vs Structured

```bash
python src/evaluate.py \
  --metadata data/sample_products.csv \
  --baseline_dir outputs/baseline \
  --improved_dir outputs/structured \
  --output_csv results/evaluation_summary.csv \
  --device cpu
```

### 4) Export Prompts + Outputs (for report traceability)

```bash
python src/export_prompts_outputs.py
```

### 5) Optional Bonus Multimodal Demo Chain

```bash
python src/multimodal_pipeline.py full-chain --text "premium matte black water bottle" --demo
```

---

## Methodology (All-in-One Summary)

### 1) Problem Setup
Given structured product metadata (`title`, `category`, `color`, `material`, `style`, `attributes`, `target_view`, `environment`), generate e-commerce product images suitable for catalog use.

### 2) Baseline System
Use short naive prompts from metadata (`baseline_prompt` in CSV).

### 3) Improved System
Use structured prompt templates + negative prompts:
- structured prompt generated in `src/prompt_builder.py`
- negative prompt configured in `configs/default.yaml`

### 4) Control Strategy
Required control is implemented through:
- structured prompt templates
- negative prompt suppression

Optional extension hooks for conditioning are retained in config (`use_controlnet`, model id).

### 5) Evaluation Strategy
Evaluate baseline vs structured with four dimensions:
- prompt alignment
- consistency
- diversity
- quality proxy (+ qualitative rubric template)

### 6) Analysis Requirement Coverage
Includes both successful and failure examples:
- detailed per-image evaluation
- failure case extraction and analysis file

---

## Evaluation Design

Required dimensions implemented:
- **Prompt alignment**
- **Consistency**
- **Diversity**
- **Quality** (proxy + qualitative review template)

Primary result artifacts:
- `results/evaluation_summary.csv`
- `results/evaluation_details.csv`
- `results/failure_cases.csv`
- `results/qualitative_review_template.csv`
- `results/baseline_vs_structured.png`

## Key Quantitative Results

From `results/evaluation_summary.csv`:

| System | Prompt Alignment | Consistency | Diversity | Quality Proxy |
|---|---:|---:|---:|---:|
| Baseline | 0.4929 | 1.0000 | 0.0339 | 0.4837 |
| Structured | 0.5613 | 1.0000 | 0.0013 | 0.5131 |
| Delta (Structured - Baseline) | +0.0684 | +0.0000 | -0.0326 | +0.0294 |

Interpretation:
- Structured prompting improved alignment and quality.
- Consistency stayed high in both settings.
- Diversity dropped under stronger control, showing the expected control/diversity trade-off.

---

## Failure Cases and Insights

Failure analysis is documented in `results/failure_cases.csv`.
Common issues observed:
- metadata mismatch on some examples
- weak sharpness/contrast in lower-quality cases
- reduced variation under stronger control

These findings are consistent with diffusion trade-offs between strict control and output diversity.

---

## Submission Deliverables Included

- Full codebase and configs
- README with instructions
- Sample outputs
- Dataset and metadata schema
- Evaluation artifacts and failure analysis
- 10+ slide deck package
- AI tool disclosure
- Demo video script

---

## Multimodal Extension: Actual Run Artifacts

Executed demo artifacts are available here:
- `results/multimodal_demo_results.md`
- `results/auto_captions.csv` (image-to-text captions)
- `sample_outputs/text_to_image_demo_placeholder.png` (text/speech-to-image demo output)
- `sample_outputs/image_to_video_demo.gif` (image-to-video demo output)

This demonstrates bonus multimodal support:
- image → text captioning
- text/speech → image generation flow
- image → video conversion demo

---

## AI Tools Disclosure

See `docs/ai_tool_disclosure.md` for:
- which tools were used
- how they were used
- what was generated vs assisted

---

## Final Submission Checklist

- [x] Stable Diffusion pipeline implemented
- [x] Control mechanism implemented
- [x] Data-to-prompt strategy documented
- [x] Baseline vs improved comparison completed
- [x] Evaluation metrics and analysis completed
- [x] Failure cases documented
- [x] PPT package prepared (10+ slides)
- [x] AI tools disclosure included
- [x] Demo video uploaded and link added
- [x] GitHub and video links filled at top of README

For detailed handoff notes, see `docs/ultimate_submission_package.md` and `docs/final_readiness_checklist.md`.

