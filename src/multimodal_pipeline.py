"""
multimodal_pipeline.py
======================
Unified command-line runner for all three multimodal capabilities:

    Mode 1 — image2text  : Caption product images with BLIP-2
    Mode 2 — image2video : Animate product images with Stable Video Diffusion
    Mode 3 — speech2image: Voice → Whisper → SDXL product photo

Usage
-----
    # Caption all images in structured output folder
    python multimodal_pipeline.py image2text \\
        --dir outputs/structured/ \\
        --save-csv results/auto_captions.csv

    # Animate a single product image (demo mode — no GPU)
    python multimodal_pipeline.py image2video \\
        --image outputs/structured/P001/image_01.png \\
        --demo

    # Animate with Stable Video Diffusion (GPU required)
    python multimodal_pipeline.py image2video \\
        --image outputs/structured/P001/image_01.png \\
        --device cuda --format gif

    # Generate image from a voice recording
    python multimodal_pipeline.py speech2image \\
        --audio my_description.wav

    # Generate image from text directly (no microphone)
    python multimodal_pipeline.py speech2image \\
        --text "a sleek black leather wallet" \\
        --placeholder

    # Run the full chain: speech → image → caption → video
    python multimodal_pipeline.py full-chain \\
        --audio my_description.wav \\
        --device cuda
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_banner(title: str) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def _check_outputs_exist(paths: list, label: str) -> bool:
    if not paths:
        print(f"[WARN] No {label} were produced.")
        return False
    return True


# ---------------------------------------------------------------------------
# Mode 1: image2text
# ---------------------------------------------------------------------------

def run_image2text(args: argparse.Namespace) -> None:
    _print_banner("Mode: Image → Text  (BLIP-2 Captioning)")

    # Import here so the module is only loaded when needed
    from image_to_text import ImageCaptioner, save_captions_csv, ocr_image

    captioner = ImageCaptioner(device=args.device)

    if args.image:
        caption = captioner.caption(args.image, prompt=args.prompt)
        print(f"\n📝 Caption:\n   {caption}")
        if args.ocr:
            print(f"🔤 OCR: {ocr_image(args.image)}")
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


# ---------------------------------------------------------------------------
# Mode 2: image2video
# ---------------------------------------------------------------------------

def run_image2video(args: argparse.Namespace) -> None:
    _print_banner("Mode: Image → Video  (Stable Video Diffusion)")

    from image_to_video import ImageToVideoConverter, make_demo_video

    out_dir = Path(args.out_dir)

    if args.demo:
        # Lightweight demo — no model download required
        images = (
            [Path(args.image)]
            if args.image
            else [p for p in Path(args.dir).rglob("*")
                  if p.suffix.lower() in (".png", ".jpg", ".jpeg")]
        )
        for img in images:
            out = out_dir / (img.stem + "_demo.gif")
            make_demo_video(img, out, fps=args.fps)
        return

    converter = ImageToVideoConverter(device=args.device)

    if args.image:
        out_name = Path(args.image).stem + f".{args.format}"
        converter.convert(
            args.image,
            out_dir / out_name,
            fps=args.fps,
            motion_bucket_id=args.motion,
            seed=args.seed,
            output_format=args.format,
        )
    else:
        converter.convert_batch(
            args.dir,
            out_dir,
            fps=args.fps,
            output_format=args.format,
        )


# ---------------------------------------------------------------------------
# Mode 3: speech2image
# ---------------------------------------------------------------------------

def run_speech2image(args: argparse.Namespace) -> dict:
    _print_banner("Mode: Speech → Image  (Whisper + SDXL)")

    from speech_to_image import SpeechToImagePipeline

    pipeline = SpeechToImagePipeline(
        whisper_model=args.whisper,
        device=args.device,
    )
    result = pipeline.run(
        audio_path=getattr(args, "audio", None),
        raw_text=getattr(args, "text", None),
        output_dir=args.out_dir,
        width=args.width,
        height=args.height,
        guidance_scale=args.guidance,
        num_inference_steps=args.steps,
        num_images=args.images,
        seed=args.seed,
        transcribe_only=getattr(args, "transcribe_only", False),
        use_placeholder=getattr(args, "placeholder", False),
        language=getattr(args, "language", None),
    )
    return result


# ---------------------------------------------------------------------------
# Mode 4: full-chain  (speech → image → caption → video)
# ---------------------------------------------------------------------------

def run_full_chain(args: argparse.Namespace) -> None:
    _print_banner("Mode: Full Chain  (Speech → Image → Caption → Video)")

    # ---------- Step 1: speech → image ----------
    print("\n[Step 1/3]  Speech → Image")
    from speech_to_image import SpeechToImagePipeline

    s2i = SpeechToImagePipeline(whisper_model=args.whisper, device=args.device)
    s2i_result = s2i.run(
        audio_path=getattr(args, "audio", None),
        raw_text=getattr(args, "text", None),
        output_dir=Path(args.out_dir) / "images",
        num_images=1,
        seed=args.seed,
        use_placeholder=getattr(args, "placeholder", False),
    )
    generated_images = s2i_result.get("images", [])
    if not _check_outputs_exist(generated_images, "images"):
        return

    # ---------- Step 2: image → caption ----------
    print("\n[Step 2/3]  Image → Caption")
    from image_to_text import ImageCaptioner

    captioner = ImageCaptioner(device=args.device)
    captions: dict[str, str] = {}
    for img_path in generated_images:
        cap = captioner.caption(
            img_path,
            prompt="Describe this product for an e-commerce listing:"
        )
        captions[str(img_path)] = cap
        print(f"  📝 {Path(img_path).name}: {cap}")

    # ---------- Step 3: image → video ----------
    print("\n[Step 3/3]  Image → Video")
    from image_to_video import ImageToVideoConverter, make_demo_video

    video_dir = Path(args.out_dir) / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)

    for img_path in generated_images:
        out_video = video_dir / (Path(img_path).stem + ".gif")
        if getattr(args, "demo", False) or getattr(args, "placeholder", False):
            make_demo_video(img_path, out_video, fps=7)
        else:
            converter = ImageToVideoConverter(device=args.device)
            converter.convert(img_path, out_video, output_format="gif")

    # ---------- Summary ----------
    print("\n" + "=" * 60)
    print("✅  Full Chain Complete!")
    print(f"   Transcript : {s2i_result['transcript']}")
    print(f"   SD Prompt  : {s2i_result.get('prompt', 'N/A')}")
    print(f"   Images     : {[str(p) for p in generated_images]}")
    print(f"   Captions   : {list(captions.values())}")
    print(f"   Videos     : {[str(video_dir / (Path(p).stem + '.gif')) for p in generated_images]}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multimodal_pipeline",
        description=(
            "Multimodal AI Pipeline for E-Commerce\n"
            "  image2text  — Caption images with BLIP-2\n"
            "  image2video — Animate images with Stable Video Diffusion\n"
            "  speech2image — Voice/text → SDXL product photo\n"
            "  full-chain  — Speech → Image → Caption → Video"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    # ---- Shared arguments ----
    def add_shared(p: argparse.ArgumentParser) -> None:
        p.add_argument("--device", default="cpu", help="cpu | cuda | mps")
        p.add_argument("--seed",   type=int, default=42)

    # ---- image2text ----
    p1 = sub.add_parser("image2text", help="Caption product images with BLIP-2")
    g1 = p1.add_mutually_exclusive_group(required=True)
    g1.add_argument("--image", help="Single image path")
    g1.add_argument("--dir",   help="Directory to batch-caption")
    p1.add_argument("--prompt",    default=None, help="Optional guiding text prompt")
    p1.add_argument("--save-csv",  default=None, dest="save_csv",
                    help="Save captions to this CSV")
    p1.add_argument("--ocr",  action="store_true", help="Also run Tesseract OCR")
    add_shared(p1)

    # ---- image2video ----
    p2 = sub.add_parser("image2video", help="Animate images with Stable Video Diffusion")
    g2 = p2.add_mutually_exclusive_group(required=True)
    g2.add_argument("--image", help="Single image path")
    g2.add_argument("--dir",   help="Directory to batch-animate")
    p2.add_argument("--out-dir", default="outputs/videos", dest="out_dir")
    p2.add_argument("--format",  choices=["gif", "mp4"], default="gif")
    p2.add_argument("--fps",     type=int, default=7)
    p2.add_argument("--motion",  type=int, default=127,
                    help="Motion intensity 1-255 (SVD only)")
    p2.add_argument("--demo", action="store_true",
                    help="Lightweight placeholder animation (no GPU needed)")
    add_shared(p2)

    # ---- speech2image ----
    p3 = sub.add_parser("speech2image", help="Voice/text → SDXL product photo")
    g3 = p3.add_mutually_exclusive_group(required=True)
    g3.add_argument("--audio", help="Path to audio file (.wav/.mp3/.m4a)")
    g3.add_argument("--text",  help="Provide text directly (skip Whisper)")
    p3.add_argument("--out-dir",  default="outputs/speech", dest="out_dir")
    p3.add_argument("--whisper",  default="base",
                    choices=["tiny", "base", "small", "medium", "large"])
    p3.add_argument("--language", default=None)
    p3.add_argument("--steps",    type=int,   default=30)
    p3.add_argument("--guidance", type=float, default=7.5)
    p3.add_argument("--images",   type=int,   default=1)
    p3.add_argument("--width",    type=int,   default=1024)
    p3.add_argument("--height",   type=int,   default=1024)
    p3.add_argument("--transcribe-only", action="store_true", dest="transcribe_only")
    p3.add_argument("--placeholder",     action="store_true",
                    help="Skip SD, save placeholder image (offline demo)")
    add_shared(p3)

    # ---- full-chain ----
    p4 = sub.add_parser("full-chain", help="Speech → Image → Caption → Video")
    g4 = p4.add_mutually_exclusive_group(required=True)
    g4.add_argument("--audio", help="Path to audio file")
    g4.add_argument("--text",  help="Text prompt (skip Whisper)")
    p4.add_argument("--out-dir",    default="outputs/full_chain", dest="out_dir")
    p4.add_argument("--whisper",    default="base",
                    choices=["tiny", "base", "small", "medium", "large"])
    p4.add_argument("--demo",       action="store_true",
                    help="Demo mode: placeholder images + lightweight animation")
    p4.add_argument("--placeholder", action="store_true")
    add_shared(p4)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    if args.mode == "image2text":
        run_image2text(args)
    elif args.mode == "image2video":
        run_image2video(args)
    elif args.mode == "speech2image":
        run_speech2image(args)
    elif args.mode == "full-chain":
        run_full_chain(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
