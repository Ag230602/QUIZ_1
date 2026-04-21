"""
image_to_text.py
================
Converts product images → descriptive text captions using BLIP-2.

Capabilities
------------
* Caption a single image file
* Batch-caption a directory of images
* OCR fallback using pytesseract (optional)
* CLI usage:
    python image_to_text.py --image outputs/structured/P001/image.png
    python image_to_text.py --dir   outputs/structured/ --save-csv results/captions.csv
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Optional

from PIL import Image


# ---------------------------------------------------------------------------
# Core captioner (BLIP-2)
# ---------------------------------------------------------------------------

class ImageCaptioner:
    """
    Wraps Salesforce/BLIP-2 (or blip-image-captioning-large as fallback)
    for automatic image captioning.
    """

    BLIP2_MODEL = "Salesforce/blip2-opt-2.7b"
    BLIP_FALLBACK = "Salesforce/blip-image-captioning-large"

    def __init__(self, device: str = "cpu", use_blip2: bool = True):
        self.device = device
        self._processor = None
        self._model = None
        self._use_blip2 = use_blip2
        self._loaded = False

    # ------------------------------------------------------------------
    # Lazy load — avoids importing heavy libs until actually needed
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self._loaded:
            return

        try:
            import torch
            from transformers import Blip2Processor, Blip2ForConditionalGeneration

            print(f"[ImageCaptioner] Loading BLIP-2 model: {self.BLIP2_MODEL} ...")
            self._processor = Blip2Processor.from_pretrained(self.BLIP2_MODEL)
            self._model = Blip2ForConditionalGeneration.from_pretrained(
                self.BLIP2_MODEL,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            ).to(self.device)
            self._use_blip2 = True
            print("[ImageCaptioner] BLIP-2 loaded successfully.")

        except Exception as exc:
            print(f"[ImageCaptioner] BLIP-2 failed ({exc}). Falling back to BLIP-large ...")
            try:
                from transformers import BlipProcessor, BlipForConditionalGeneration

                self._processor = BlipProcessor.from_pretrained(self.BLIP_FALLBACK)
                self._model = BlipForConditionalGeneration.from_pretrained(
                    self.BLIP_FALLBACK
                ).to(self.device)
                self._use_blip2 = False
                print("[ImageCaptioner] BLIP-large loaded successfully.")
            except Exception as exc2:
                raise RuntimeError(
                    f"[ImageCaptioner] Could not load any captioning model: {exc2}"
                ) from exc2

        self._loaded = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def caption(self, image_path: str | Path, prompt: Optional[str] = None) -> str:
        """
        Returns a natural-language caption for the given image.

        Parameters
        ----------
        image_path : path to a PNG / JPEG image
        prompt     : optional text prompt to guide the caption
                     e.g. "Describe this product for an e-commerce listing:"
        """
        self._load()
        import torch

        image = Image.open(image_path).convert("RGB")

        if self._use_blip2:
            # BLIP-2 supports conditional generation with a text prompt
            text_input = prompt or "Question: What is this product? Answer:"
            inputs = self._processor(images=image, text=text_input, return_tensors="pt").to(
                self.device, torch.float16 if self.device != "cpu" else torch.float32
            )
            with torch.no_grad():
                out = self._model.generate(**inputs, max_new_tokens=80)
            caption = self._processor.decode(out[0], skip_special_tokens=True).strip()
        else:
            # BLIP fallback — unconditional or conditional
            inputs = self._processor(image, text=prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                out = self._model.generate(**inputs, max_new_tokens=80)
            caption = self._processor.decode(out[0], skip_special_tokens=True).strip()

        return caption

    def caption_batch(
        self,
        image_dir: str | Path,
        extensions: tuple = (".png", ".jpg", ".jpeg", ".webp"),
        prompt: Optional[str] = None,
    ) -> dict[str, str]:
        """
        Captions every image in a directory (non-recursive).
        Returns {filename: caption}.
        """
        image_dir = Path(image_dir)
        results: dict[str, str] = {}

        image_files = [p for p in sorted(image_dir.rglob("*")) if p.suffix.lower() in extensions]
        print(f"[ImageCaptioner] Found {len(image_files)} image(s) in '{image_dir}'")

        for img_path in image_files:
            try:
                cap = self.caption(img_path, prompt=prompt)
                results[str(img_path)] = cap
                print(f"  ✓ {img_path.name}: {cap[:80]}...")
            except Exception as exc:
                results[str(img_path)] = f"ERROR: {exc}"
                print(f"  ✗ {img_path.name}: {exc}")

        return results


# ---------------------------------------------------------------------------
# OCR helper (optional — needs: pip install pytesseract tesseract-ocr)
# ---------------------------------------------------------------------------

def ocr_image(image_path: str | Path) -> str:
    """
    Extracts raw text from an image using Tesseract OCR.
    Useful for product labels, price tags, or packaging text.
    """
    try:
        import pytesseract
        image = Image.open(image_path).convert("RGB")
        text = pytesseract.image_to_string(image).strip()
        return text if text else "[No text detected by OCR]"
    except ImportError:
        return "[pytesseract not installed — run: pip install pytesseract]"
    except Exception as exc:
        return f"[OCR error: {exc}]"


# ---------------------------------------------------------------------------
# Save results to CSV
# ---------------------------------------------------------------------------

def save_captions_csv(captions: dict[str, str], output_csv: str | Path) -> None:
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_path", "caption"])
        for path, caption in captions.items():
            writer.writerow([path, caption])
    print(f"[ImageCaptioner] Captions saved → {output_csv}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Image → Text: caption product images using BLIP-2"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="Path to a single image file")
    group.add_argument("--dir", help="Directory to batch-caption all images")
    parser.add_argument("--prompt", default=None, help="Optional text prompt to guide the caption")
    parser.add_argument("--device", default="cpu", help="Device: cpu | cuda | mps")
    parser.add_argument("--save-csv", default=None, help="Save batch results to this CSV path")
    parser.add_argument("--ocr", action="store_true", help="Also run OCR on the image(s)")
    args = parser.parse_args()

    captioner = ImageCaptioner(device=args.device)

    if args.image:
        caption = captioner.caption(args.image, prompt=args.prompt)
        print(f"\n📝 Caption: {caption}")
        if args.ocr:
            text = ocr_image(args.image)
            print(f"🔤 OCR Text: {text}")
    else:
        captions = captioner.caption_batch(args.dir, prompt=args.prompt)
        if args.ocr:
            for img_path in captions:
                print(f"🔤 OCR [{Path(img_path).name}]: {ocr_image(img_path)}")
        if args.save_csv:
            save_captions_csv(captions, args.save_csv)
        else:
            print("\n--- All Captions ---")
            for path, cap in captions.items():
                print(f"  {Path(path).name}: {cap}")


if __name__ == "__main__":
    main()
