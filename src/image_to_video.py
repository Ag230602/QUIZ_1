"""
image_to_video.py
=================
Converts a product image → short animated video using Stable Video Diffusion (SVD).

Model used: stabilityai/stable-video-diffusion-img2vid-xt
Output:     GIF  (universal, no codec needed)  ← default
            MP4  (requires imageio[ffmpeg])

CLI usage
---------
    # Single image → GIF
    python image_to_video.py --image outputs/structured/P001/image.png

    # Single image → MP4
    python image_to_video.py --image outputs/structured/P001/image.png --format mp4

    # Batch-animate a directory
    python image_to_video.py --dir outputs/structured/ --out-dir outputs/videos/

    # Quick placeholder demo (no GPU needed)
    python image_to_video.py --image outputs/structured/P001/image.png --demo
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from PIL import Image


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SVD_MODEL_ID = "stabilityai/stable-video-diffusion-img2vid-xt"
DEFAULT_FPS = 7          # SVD XT outputs 25 frames → ~3.5 s at 7 fps
DEFAULT_FRAMES = 25      # SVD XT fixed frame count
DEFAULT_DECODE_CHUNK = 8 # how many frames decoded at once (VRAM trade-off)


# ---------------------------------------------------------------------------
# Core: Image → Video
# ---------------------------------------------------------------------------

class ImageToVideoConverter:
    """
    Wraps stabilityai/stable-video-diffusion-img2vid-xt to animate a
    single product image into a short looping video.
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._pipe = None

    # ------------------------------------------------------------------
    # Lazy loader
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self._pipe is not None:
            return

        try:
            import torch
            from diffusers import StableVideoDiffusionPipeline

            print(f"[ImageToVideo] Loading {SVD_MODEL_ID} ...")
            dtype = torch.float16 if self.device != "cpu" else torch.float32

            self._pipe = StableVideoDiffusionPipeline.from_pretrained(
                SVD_MODEL_ID,
                torch_dtype=dtype,
                variant="fp16" if dtype == torch.float16 else None,
            )

            if self.device == "cpu":
                # CPU offload reduces peak VRAM significantly
                self._pipe.enable_model_cpu_offload()
            else:
                self._pipe = self._pipe.to(self.device)

            # Memory optimisations
            self._pipe.unet.enable_forward_chunking()
            print("[ImageToVideo] Pipeline loaded.")

        except Exception as exc:
            raise RuntimeError(
                f"[ImageToVideo] Could not load SVD pipeline: {exc}\n"
                "Make sure diffusers>=0.25 is installed and you have accepted the\n"
                "model licence at https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt"
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def convert(
        self,
        image_path: str | Path,
        output_path: str | Path,
        fps: int = DEFAULT_FPS,
        num_frames: int = DEFAULT_FRAMES,
        decode_chunk_size: int = DEFAULT_DECODE_CHUNK,
        motion_bucket_id: int = 127,   # 1-255, higher = more motion
        noise_aug_strength: float = 0.02,
        seed: int = 42,
        output_format: str = "gif",    # "gif" | "mp4"
    ) -> Path:
        """
        Animates `image_path` and writes video to `output_path`.

        Returns the final output path.
        """
        self._load()

        import torch

        image = Image.open(image_path).convert("RGB")
        # SVD expects 1024×576 (landscape) or 576×1024 (portrait)
        image = _resize_for_svd(image)

        generator = torch.manual_seed(seed)

        print(f"[ImageToVideo] Generating {num_frames} frames from '{Path(image_path).name}' ...")
        with torch.no_grad():
            frames = self._pipe(
                image,
                num_frames=num_frames,
                decode_chunk_size=decode_chunk_size,
                motion_bucket_id=motion_bucket_id,
                noise_aug_strength=noise_aug_strength,
                generator=generator,
            ).frames[0]  # list of PIL Images

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_format.lower() == "mp4":
            _save_mp4(frames, output_path, fps=fps)
        else:
            _save_gif(frames, output_path, fps=fps)

        print(f"[ImageToVideo] Saved → {output_path}")
        return output_path

    def convert_batch(
        self,
        image_dir: str | Path,
        output_dir: str | Path,
        extensions: tuple = (".png", ".jpg", ".jpeg"),
        fps: int = DEFAULT_FPS,
        output_format: str = "gif",
        **kwargs,
    ) -> list[Path]:
        """Animate every image in `image_dir` and write to `output_dir`."""
        image_dir = Path(image_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        image_files = [p for p in sorted(image_dir.rglob("*")) if p.suffix.lower() in extensions]
        print(f"[ImageToVideo] Found {len(image_files)} image(s) in '{image_dir}'")

        results: list[Path] = []
        for img_path in image_files:
            out_name = img_path.stem + f".{output_format}"
            out_path = output_dir / img_path.parent.relative_to(image_dir) / out_name
            try:
                results.append(self.convert(img_path, out_path, fps=fps,
                                            output_format=output_format, **kwargs))
            except Exception as exc:
                print(f"  ✗ {img_path.name}: {exc}")
        return results


# ---------------------------------------------------------------------------
# Demo / placeholder (no GPU required)
# ---------------------------------------------------------------------------

def make_demo_video(image_path: str | Path, output_path: str | Path, fps: int = 7) -> Path:
    """
    Creates a simple animated GIF by applying gentle zoom/pan transforms
    to the source image. No GPU or model download required.
    Great for testing the pipeline end-to-end.
    """
    from PIL import ImageFilter, ImageEnhance
    import math

    image = Image.open(image_path).convert("RGB")
    w, h = image.size
    frames: list[Image.Image] = []
    num_frames = 20

    for i in range(num_frames):
        t = i / num_frames                              # 0 → 1
        scale = 1.0 + 0.06 * math.sin(t * math.pi)    # subtle zoom pulse
        new_w = int(w * scale)
        new_h = int(h * scale)
        frame = image.resize((new_w, new_h), Image.LANCZOS)
        # Crop back to original size (centred)
        left = (new_w - w) // 2
        top  = (new_h - h) // 2
        frame = frame.crop((left, top, left + w, top + h))
        # Slight brightness pulse
        factor = 1.0 + 0.05 * math.sin(t * 2 * math.pi)
        frame = ImageEnhance.Brightness(frame).enhance(factor)
        frames.append(frame)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _save_gif(frames, output_path, fps=fps)
    print(f"[Demo] Placeholder animation saved → {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resize_for_svd(image: Image.Image, target_wh: tuple = (1024, 576)) -> Image.Image:
    """Resize + centre-crop to SVD's expected aspect ratio."""
    tw, th = target_wh
    img_ratio = image.width / image.height
    target_ratio = tw / th

    if img_ratio > target_ratio:
        # Image is wider — fit height, crop width
        new_h = th
        new_w = int(new_h * img_ratio)
    else:
        new_w = tw
        new_h = int(new_w / img_ratio)

    image = image.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - tw) // 2
    top  = (new_h - th) // 2
    return image.crop((left, top, left + tw, top + th))


def _save_gif(frames: List[Image.Image], path: Path, fps: int = 7) -> None:
    duration_ms = int(1000 / fps)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=duration_ms,
        optimize=False,
    )


def _save_mp4(frames: List[Image.Image], path: Path, fps: int = 7) -> None:
    try:
        import imageio
        import numpy as np

        writer = imageio.get_writer(str(path), fps=fps, codec="libx264",
                                    pixelformat="yuv420p", quality=8)
        for frame in frames:
            writer.append_data(np.array(frame))
        writer.close()
    except ImportError:
        # Fallback: save as GIF with .mp4 extension (warn user)
        print("[WARN] imageio/ffmpeg not found. Saving as GIF instead.")
        gif_path = path.with_suffix(".gif")
        _save_gif(frames, gif_path, fps=fps)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Image → Video: animate product images with Stable Video Diffusion"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="Path to a single product image")
    group.add_argument("--dir",   help="Directory of images to batch-animate")
    parser.add_argument("--out-dir", default="outputs/videos",
                        help="Output directory for generated videos")
    parser.add_argument("--format", choices=["gif", "mp4"], default="gif",
                        help="Output video format (default: gif)")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS,
                        help=f"Frames per second (default: {DEFAULT_FPS})")
    parser.add_argument("--motion", type=int, default=127,
                        help="Motion intensity 1-255 (default: 127)")
    parser.add_argument("--device", default="cpu",
                        help="Device: cpu | cuda | mps")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--demo", action="store_true",
                        help="Use lightweight placeholder animation (no GPU/download needed)")
    args = parser.parse_args()

    if args.demo:
        if args.image:
            out = Path(args.out_dir) / (Path(args.image).stem + "_demo.gif")
            make_demo_video(args.image, out, fps=args.fps)
        else:
            from pathlib import Path as P
            images = [p for p in P(args.dir).rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg")]
            for img in images:
                out = Path(args.out_dir) / (img.stem + "_demo.gif")
                make_demo_video(img, out, fps=args.fps)
        return

    converter = ImageToVideoConverter(device=args.device)
    if args.image:
        out_name = Path(args.image).stem + f".{args.format}"
        out_path = Path(args.out_dir) / out_name
        converter.convert(
            args.image, out_path,
            fps=args.fps,
            motion_bucket_id=args.motion,
            seed=args.seed,
            output_format=args.format,
        )
    else:
        converter.convert_batch(
            args.dir, args.out_dir,
            fps=args.fps,
            output_format=args.format,
        )


if __name__ == "__main__":
    main()
