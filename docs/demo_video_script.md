# Demo Video Script (1–2 Minutes)

## 0:00–0:15 — Problem
"This project generates e-commerce product images from structured metadata using Stable Diffusion. The main goal is to improve control and consistency compared with naive prompting."

## 0:15–0:35 — Input
Show the CSV row or JSON metadata.
"Each product includes fields like title, color, material, style, attributes, and target view. The system converts that data into prompts automatically."

## 0:35–0:55 — Pipeline
Show the architecture slide or code.
"We compare a baseline naive prompt against a structured template with negative prompts, and optionally ControlNet for stronger conditioning."

## 0:55–1:20 — Results
Show 2–4 generated examples.
"Here are the baseline and improved outputs. The structured prompts are more consistent, cleaner, and closer to product metadata."

## 1:20–1:40 — Evaluation
Show a metric table.
"We evaluate prompt alignment, consistency, diversity, and qualitative image quality. We also show failure cases where the model adds clutter or misses attributes."

## 1:40–2:00 — Takeaway
"The main insight is that stronger control improves alignment and reliability, although it can reduce diversity. This makes the system more useful for real-world catalog image generation."
