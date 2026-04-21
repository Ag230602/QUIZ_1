from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

from prompt_builder import PromptBuilder
from utils import ensure_dir, set_seed, slugify


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_placeholder(prompt: str, output_path: Path, size=(1024, 1024)) -> None:
    """
    Creates a visible placeholder when the diffusion stack is not installed or not executed.
    Replace these files with actual outputs in real experiments.
    """
    img = Image.new("RGB", size, color=(247, 247, 247))
    draw = ImageDraw.Draw(img)
    title = "PLACEHOLDER OUTPUT"
    body = (
        "Run this script on a machine with Stable Diffusion dependencies\n"
        "to replace this file with a real generated image.\n\n"
        f"Prompt:\n{prompt[:220]}"
    )
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.rectangle((60, 60, size[0]-60, size[1]-60), outline=(80, 80, 80), width=4)
    draw.text((90, 120), title, fill=(20, 20, 20), font=font)
    draw.multiline_text((90, 190), body, fill=(40, 40, 40), font=font, spacing=8)
    img.save(output_path)


def load_pipeline(config: dict):
    try:
        import torch
        from diffusers import StableDiffusionXLPipeline

        model_cfg = config["model"]
        dtype = torch.float16 if model_cfg.get("torch_dtype", "float16") == "float16" else torch.float32
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model_cfg["model_id"],
            torch_dtype=dtype,
            use_safetensors=model_cfg.get("use_safetensors", True),
        )
        if model_cfg.get("enable_cpu_offload", False):
            pipe.enable_model_cpu_offload()
        else:
            pipe = pipe.to(model_cfg.get("device", "cuda"))
        return pipe
    except Exception as exc:
        print(f"[WARN] Could not load diffusion pipeline: {exc}")
        return None


def generate_images(pipe, prompt: str, negative_prompt: str, cfg: dict):
    import torch

    gen_cfg = cfg["generation"]
    generator = torch.Generator(device="cpu").manual_seed(int(gen_cfg["seed"]))
    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt if cfg["control"].get("use_negative_prompt", True) else None,
        width=int(gen_cfg["image_width"]),
        height=int(gen_cfg["image_height"]),
        guidance_scale=float(gen_cfg["guidance_scale"]),
        num_inference_steps=int(gen_cfg["num_inference_steps"]),
        num_images_per_prompt=int(gen_cfg["num_images_per_prompt"]),
        generator=generator,
    )
    return result.images


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=["baseline", "structured"], default="structured")
    args = parser.parse_args()

    config = load_config(args.config)
    set_seed(int(config["generation"]["seed"]))

    df = pd.read_csv(config["data"]["metadata_csv"])
    prompt_builder = PromptBuilder(config)
    output_root = ensure_dir(Path(config["generation"]["output_root"]) / args.mode)
    pipe = load_pipeline(config)

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Generating ({args.mode})"):
        row = row.to_dict()
        prompts = prompt_builder.build(row)
        prompt = prompts.baseline_prompt if args.mode == "baseline" else prompts.structured_prompt
        negative_prompt = prompts.negative_prompt

        product_dir = ensure_dir(output_root / row["product_id"])
        view_slug = slugify(row["target_view"])

        if pipe is None:
            placeholder_path = product_dir / f"{view_slug}_placeholder.png"
            make_placeholder(prompt, placeholder_path)
            continue

        images = generate_images(pipe, prompt, negative_prompt, config)
        for i, image in enumerate(images, start=1):
            image.save(product_dir / f"{view_slug}_{i}.png")


if __name__ == "__main__":
    main()
