"""
speech_to_image.py
==================
Converts spoken audio → transcribed text → Stable Diffusion product image.

Pipeline
--------
  Audio file (.wav / .mp3 / .m4a)
      │
      ▼  [OpenAI Whisper]
  Transcribed text
      │
      ▼  [PromptEnhancer]
  Refined SD prompt  (e-commerce style)
      │
      ▼  [Stable Diffusion XL]
  Product image(s)

CLI usage
---------
    # Generate from a WAV file
    python speech_to_image.py --audio my_product_description.wav

    # Specify output dir, guidance scale, etc.
    python speech_to_image.py --audio description.wav \\
        --out-dir outputs/speech/ \\
        --steps 30 \\
        --guidance 7.5 \\
        --device cuda

    # Dry-run: transcribe only (no image generation)
    python speech_to_image.py --audio description.wav --transcribe-only

    # Use a text string directly (skip Whisper, go straight to SD)
    python speech_to_image.py --text "a sleek black leather wallet on a white background"
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Step 1 — Speech → Text  (Whisper)
# ---------------------------------------------------------------------------

class SpeechTranscriber:
    """
    Wraps OpenAI Whisper to transcribe an audio file to text.
    Supports: .wav, .mp3, .m4a, .flac, .ogg
    """

    def __init__(self, model_size: str = "base"):
        """
        model_size: 'tiny' | 'base' | 'small' | 'medium' | 'large'
        Larger = more accurate but slower and needs more RAM.
        'base' is a good balance for product descriptions.
        """
        self.model_size = model_size
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import whisper
            print(f"[Whisper] Loading '{self.model_size}' model ...")
            self._model = whisper.load_model(self.model_size)
            print("[Whisper] Model ready.")
        except ImportError:
            raise RuntimeError(
                "[Whisper] openai-whisper not installed.\n"
                "Run: pip install openai-whisper"
            )

    def transcribe(self, audio_path: str | Path, language: Optional[str] = None) -> str:
        """
        Transcribes the audio file and returns the raw text.

        Parameters
        ----------
        audio_path : path to audio file
        language   : ISO-639-1 code e.g. "en" (auto-detect if None)
        """
        self._load()
        audio_path = str(audio_path)
        kwargs = {}
        if language:
            kwargs["language"] = language

        print(f"[Whisper] Transcribing '{Path(audio_path).name}' ...")
        result = self._model.transcribe(audio_path, **kwargs)
        text = result["text"].strip()
        print(f"[Whisper] Transcript: {text}")
        return text


# ---------------------------------------------------------------------------
# Step 2 — Text → Enhanced SD Prompt
# ---------------------------------------------------------------------------

class PromptEnhancer:
    """
    Takes a raw transcription and wraps it with e-commerce photography
    context so Stable Diffusion produces catalog-quality results.
    """

    ECOMMERCE_SUFFIX = (
        "professional product photography, clean white seamless studio background, "
        "soft product lighting, 85mm lens, centered composition, photorealistic, "
        "high detail, catalog-ready, no text, no watermark"
    )

    NEGATIVE_PROMPT = (
        "low quality, blurry, distorted, deformed, cropped, extra objects, "
        "duplicate product, text, watermark, logo, busy background, clutter, "
        "human hands, broken geometry, cartoon, illustration"
    )

    def enhance(self, raw_text: str) -> tuple[str, str]:
        """
        Returns (positive_prompt, negative_prompt).
        """
        # Capitalise + strip filler words
        cleaned = raw_text.strip().rstrip(".")
        positive = f"Commercial e-commerce product photo of {cleaned}, {self.ECOMMERCE_SUFFIX}"
        return positive, self.NEGATIVE_PROMPT


# ---------------------------------------------------------------------------
# Step 3 — Prompt → Image (Stable Diffusion XL)
# ---------------------------------------------------------------------------

class SDImageGenerator:
    """
    Thin wrapper around StableDiffusionXLPipeline for single-prompt generation.
    Reuses the same SDXL model used in generate.py.
    """

    MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._pipe = None

    def _load(self) -> None:
        if self._pipe is not None:
            return
        try:
            import torch
            from diffusers import StableDiffusionXLPipeline

            dtype = torch.float16 if self.device != "cpu" else torch.float32
            print(f"[SDGenerator] Loading {self.MODEL_ID} ...")
            self._pipe = StableDiffusionXLPipeline.from_pretrained(
                self.MODEL_ID,
                torch_dtype=dtype,
                use_safetensors=True,
            )
            self._pipe.enable_model_cpu_offload()
            print("[SDGenerator] Pipeline ready.")
        except Exception as exc:
            raise RuntimeError(f"[SDGenerator] Failed to load SD pipeline: {exc}") from exc

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 30,
        num_images: int = 1,
        seed: int = 42,
    ) -> list[Image.Image]:
        """Returns a list of PIL images."""
        self._load()
        import torch

        generator = torch.Generator(device="cpu").manual_seed(seed)
        with torch.no_grad():
            result = self._pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                num_images_per_prompt=num_images,
                generator=generator,
            )
        return result.images

    @staticmethod
    def make_placeholder(prompt: str, output_path: Path, size=(1024, 1024)) -> Image.Image:
        """Creates a labelled placeholder when SD is not available."""
        img = Image.new("RGB", size, color=(245, 245, 245))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        draw.rectangle((40, 40, size[0]-40, size[1]-40), outline=(100, 100, 100), width=3)
        draw.text((60, 80),  "SPEECH → IMAGE PLACEHOLDER", fill=(30, 30, 30), font=font)
        draw.multiline_text((60, 140), f"Prompt:\n{prompt[:300]}", fill=(60, 60, 60),
                            font=font, spacing=6)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)
        return img


# ---------------------------------------------------------------------------
# Full Pipeline
# ---------------------------------------------------------------------------

class SpeechToImagePipeline:
    """
    Orchestrates the full  Audio → Whisper → PromptEnhancer → SDXL  flow.
    """

    def __init__(
        self,
        whisper_model: str = "base",
        device: str = "cpu",
    ):
        self.transcriber = SpeechTranscriber(model_size=whisper_model)
        self.enhancer    = PromptEnhancer()
        self.generator   = SDImageGenerator(device=device)

    def run(
        self,
        audio_path: Optional[str | Path] = None,
        raw_text: Optional[str] = None,
        output_dir: str | Path = "outputs/speech",
        width: int = 1024,
        height: int = 1024,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 30,
        num_images: int = 1,
        seed: int = 42,
        transcribe_only: bool = False,
        use_placeholder: bool = False,
        language: Optional[str] = None,
    ) -> dict:
        """
        Run the full pipeline.

        Parameters
        ----------
        audio_path       : path to input audio file (WAV / MP3 / M4A)
        raw_text         : if provided, skip Whisper and use this text directly
        output_dir       : where to save generated images
        transcribe_only  : if True, return transcript without generating images
        use_placeholder  : if True, skip SD and save a placeholder image
        language         : Whisper language hint (e.g. "en")

        Returns
        -------
        dict with keys: transcript, prompt, negative_prompt, images (list of paths)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # --- Step 1: transcribe ----------------------------------------
        if raw_text:
            transcript = raw_text
            print(f"[Pipeline] Using provided text: {transcript}")
        elif audio_path:
            transcript = self.transcriber.transcribe(audio_path, language=language)
        else:
            raise ValueError("Provide either --audio or --text")

        if transcribe_only:
            print(f"\n📝 Transcript only mode.\nTranscript: {transcript}")
            return {"transcript": transcript, "prompt": None, "images": []}

        # --- Step 2: enhance prompt ------------------------------------
        positive_prompt, negative_prompt = self.enhancer.enhance(transcript)
        print(f"\n✨ Enhanced prompt:\n   {positive_prompt}\n")

        # --- Step 3: generate images -----------------------------------
        image_paths: list[Path] = []

        if use_placeholder:
            # Offline / demo mode
            for i in range(num_images):
                stem = Path(audio_path).stem if audio_path else "text_input"
                out_path = output_dir / f"{stem}_{i+1:02d}_placeholder.png"
                SDImageGenerator.make_placeholder(positive_prompt, out_path)
                image_paths.append(out_path)
                print(f"[Pipeline] Placeholder saved → {out_path}")
        else:
            images = self.generator.generate(
                prompt=positive_prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                num_images=num_images,
                seed=seed,
            )
            stem = Path(audio_path).stem if audio_path else "text_input"
            for i, img in enumerate(images):
                out_path = output_dir / f"{stem}_{i+1:02d}.png"
                img.save(out_path)
                image_paths.append(out_path)
                print(f"[Pipeline] Image saved → {out_path}")

        return {
            "transcript":      transcript,
            "prompt":          positive_prompt,
            "negative_prompt": negative_prompt,
            "images":          image_paths,
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Speech → Image: describe a product by voice and generate its photo"
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--audio", help="Path to audio file (.wav / .mp3 / .m4a / .flac)")
    source.add_argument("--text",  help="Skip Whisper — provide text prompt directly")

    parser.add_argument("--out-dir",   default="outputs/speech",
                        help="Directory for generated images (default: outputs/speech)")
    parser.add_argument("--whisper",   default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--language",  default=None,
                        help="Audio language ISO code e.g. en, fr (auto-detect if omitted)")
    parser.add_argument("--device",    default="cpu",
                        help="Device for SD: cpu | cuda | mps")
    parser.add_argument("--steps",     type=int,   default=30)
    parser.add_argument("--guidance",  type=float, default=7.5)
    parser.add_argument("--images",    type=int,   default=1,
                        help="Number of images to generate (default: 1)")
    parser.add_argument("--seed",      type=int,   default=42)
    parser.add_argument("--width",     type=int,   default=1024)
    parser.add_argument("--height",    type=int,   default=1024)
    parser.add_argument("--transcribe-only", action="store_true",
                        help="Only transcribe audio, do not generate images")
    parser.add_argument("--placeholder", action="store_true",
                        help="Save placeholder images instead of running SD (offline demo)")
    args = parser.parse_args()

    pipeline = SpeechToImagePipeline(
        whisper_model=args.whisper,
        device=args.device,
    )

    result = pipeline.run(
        audio_path=args.audio,
        raw_text=args.text,
        output_dir=args.out_dir,
        width=args.width,
        height=args.height,
        guidance_scale=args.guidance,
        num_inference_steps=args.steps,
        num_images=args.images,
        seed=args.seed,
        transcribe_only=args.transcribe_only,
        use_placeholder=args.placeholder,
        language=args.language,
    )

    print("\n=== Pipeline Complete ===")
    print(f"  Transcript : {result['transcript']}")
    print(f"  Prompt     : {result.get('prompt', 'N/A')}")
    print(f"  Images     : {[str(p) for p in result.get('images', [])]}")


if __name__ == "__main__":
    main()
