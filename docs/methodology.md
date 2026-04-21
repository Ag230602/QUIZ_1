# Methodology

## Problem
Generate controlled product images from structured e-commerce metadata.

## Baseline
Use a naive text prompt directly derived from product title and one or two attributes.

Example:
- "A black water bottle on a white background"

## Improved Method
Map structured metadata to a prompt template with explicit fields:
- product title
- category cues
- material
- color
- style
- functional attributes
- view / camera angle
- scene / background
- lighting
- composition

Example structured template:

```text
Commercial e-commerce product photo of {title}, {color}, made of {material}, {style} style.
Key attributes: {attributes}. View: {target_view}. Background: {environment}.
{lighting}. {composition}. Photorealistic, product-focused.
```

## Control Strategy
Required control is implemented with:
1. **Structured prompt templates**
2. **Negative prompts** to suppress unwanted artifacts
3. **Optional ControlNet** for layout or edge conditioning

## Data-to-Prompt Mapping
Each metadata row becomes:
- a baseline prompt
- a structured prompt
- a negative prompt
- generation parameters such as seed and number of samples

## Evaluation
Measure:
- prompt alignment
- consistency across views for same product
- diversity across multiple outputs
- quality through qualitative review and optional automated proxies

## Comparison Design
Compare at least two settings:
- Baseline: naive prompt only
- Improved: structured prompt + negative prompt

Optional third condition:
- Improved + ControlNet

## Failure Analysis
Document cases such as:
- wrong number of objects
- cluttered background
- incorrect geometry
- color drift
- mismatch with metadata
