# Multimodal Demo Results (Actual Run)

Date: 2026-04-20

This file records actual executed outputs for the multimodal extensions.

## 1) Image → Text (BLIP-2)

Command run:

- `/Users/agd9c/.local/bin/python3.14 src/multimodal_pipeline.py image2text --dir sample_outputs --device cpu --save-csv results/auto_captions.csv`

Output artifact:

- `results/auto_captions.csv`

Observed sample caption output:

- `Question: What is this product? Answer: This product is a product`

## 2) Text/Speech → Image (Placeholder Demo)

Command run:

- `/Users/agd9c/.local/bin/python3.14 src/multimodal_pipeline.py speech2image --text "a premium matte black insulated water bottle, minimalist style" --placeholder --out-dir outputs/speech_demo --device cpu`

Output artifact:

- `outputs/speech_demo/text_input_01_placeholder.png`
- tracked copy: `sample_outputs/text_to_image_demo_placeholder.png`

## 3) Image → Video (Demo Animation)

Command run:

- `/Users/agd9c/.local/bin/python3.14 src/multimodal_pipeline.py image2video --image sample_outputs/P001_structured_front.png --demo --out-dir outputs/video_demo --fps 7`

Output artifact:

- `outputs/video_demo/P001_structured_front_demo.gif`
- tracked copy: `sample_outputs/image_to_video_demo.gif`

---

Note:
- BLIP-2 captioning was executed with a full model load on CPU.
- Speech→Image and Image→Video used demo/placeholder modes for reliable execution in the current environment.
