from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

try:
    import imagehash
except Exception:
    imagehash = None
import numpy as np
import pandas as pd
from PIL import Image


COLOR_KEYWORDS = {
    "black": np.array([20, 20, 20], dtype=np.float32),
    "white": np.array([235, 235, 235], dtype=np.float32),
    "gray": np.array([128, 128, 128], dtype=np.float32),
    "grey": np.array([128, 128, 128], dtype=np.float32),
    "blue": np.array([60, 110, 190], dtype=np.float32),
    "red": np.array([200, 55, 55], dtype=np.float32),
    "green": np.array([70, 150, 80], dtype=np.float32),
    "cream": np.array([235, 220, 190], dtype=np.float32),
    "beige": np.array([220, 200, 160], dtype=np.float32),
    "brown": np.array([130, 95, 60], dtype=np.float32),
    "silver": np.array([175, 175, 180], dtype=np.float32),
    "gold": np.array([210, 170, 70], dtype=np.float32),
    "pink": np.array([230, 150, 175], dtype=np.float32),
    "purple": np.array([125, 85, 165], dtype=np.float32),
    "yellow": np.array([220, 200, 80], dtype=np.float32),
    "orange": np.array([220, 140, 60], dtype=np.float32),
}


def _normalize(v: np.ndarray) -> np.ndarray:
    if v.size == 0:
        return v
    vmin = float(np.min(v))
    vmax = float(np.max(v))
    if math.isclose(vmin, vmax):
        return np.ones_like(v, dtype=np.float32)
    return ((v - vmin) / (vmax - vmin)).astype(np.float32)


def _slugify(text: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in text.strip())
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_")


def _build_structured_prompt(row: pd.Series) -> str:
    return (
        f"Commercial e-commerce product photo of {row['title']}, {row['color']}, made of {row['material']}, "
        f"{row['style']} style. Key attributes: {row['attributes']}. View: {row['target_view']}. "
        f"Scene: {row['environment']}. soft professional product lighting. 85mm product photography. "
        f"centered composition, catalog-ready, realistic, high detail. "
        f"Single product only, photorealistic, crisp edges, catalog-ready."
    )


def _collect_images_for_row(system_dir: Path, row: pd.Series) -> list[Path]:
    product_dir = system_dir / str(row["product_id"])
    if not product_dir.exists():
        return []
    view_slug = _slugify(str(row["target_view"]))
    candidates = sorted(product_dir.glob(f"{view_slug}_*.png"))
    if candidates:
        return candidates
    # fallback for ad-hoc naming
    return sorted(product_dir.glob("*.png"))


def _image_quality_raw(path: Path) -> float:
    arr = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
    contrast = float(np.std(arr))
    dx = np.diff(arr, axis=1)
    dy = np.diff(arr, axis=0)
    sharpness = float(np.mean(np.abs(dx)) + np.mean(np.abs(dy)))
    return float(np.log1p(contrast) + np.log1p(sharpness))


def _safe_mean(values: list[float]) -> float:
    valid = [x for x in values if not np.isnan(x)]
    if not valid:
        return float("nan")
    return float(np.mean(valid))


def _dominant_rgb(path: Path) -> np.ndarray:
    arr = np.asarray(Image.open(path).convert("RGB").resize((96, 96)), dtype=np.float32)
    return arr.reshape(-1, 3).mean(axis=0)


def _prompt_color_rgb(prompt: str) -> np.ndarray | None:
    prompt_l = prompt.lower()
    matches = [rgb for word, rgb in COLOR_KEYWORDS.items() if word in prompt_l]
    if not matches:
        return None
    return np.mean(np.stack(matches), axis=0)


def _color_alignment(prompt: str, image_path: Path) -> float:
    p_rgb = _prompt_color_rgb(prompt)
    if p_rgb is None:
        return float("nan")
    i_rgb = _dominant_rgb(image_path)
    dist = np.linalg.norm(p_rgb - i_rgb)
    # max rgb euclidean distance is sqrt(3*255^2)
    max_dist = math.sqrt(3 * (255 ** 2))
    score = 1.0 - float(dist / max_dist)
    return float(np.clip(score, 0.0, 1.0))


def _hist_embedding(path: Path, bins: int = 16) -> np.ndarray:
    arr = np.asarray(Image.open(path).convert("RGB").resize((128, 128)), dtype=np.float32)
    feats: list[np.ndarray] = []
    for ch in range(3):
        hist, _ = np.histogram(arr[:, :, ch], bins=bins, range=(0, 255), density=True)
        feats.append(hist.astype(np.float32))
    v = np.concatenate(feats, axis=0)
    n = np.linalg.norm(v) + 1e-8
    return (v / n).astype(np.float32)


class ClipScorer:
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.available = False
        self._model: Any = None
        self._preprocess: Any = None
        self._tokenizer: Any = None
        self._torch: Any = None

        try:
            import torch
            import open_clip

            model, _, preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32",
                pretrained="laion2b_s34b_b79k",
                device=device,
            )
            tokenizer = open_clip.get_tokenizer("ViT-B-32")
            self._torch = torch
            self._model = model.eval()
            self._preprocess = preprocess
            self._tokenizer = tokenizer
            self.available = True
        except Exception as exc:
            print(f"[WARN] CLIP scorer unavailable: {exc}")

    def encode_text(self, text: str) -> np.ndarray | None:
        if not self.available:
            return None
        with self._torch.no_grad():
            tokens = self._tokenizer([text]).to(self.device)
            emb = self._model.encode_text(tokens)
            emb = emb / emb.norm(dim=-1, keepdim=True)
        return emb[0].detach().cpu().numpy().astype(np.float32)

    def encode_image(self, path: Path) -> np.ndarray | None:
        if not self.available:
            return None
        image = Image.open(path).convert("RGB")
        image_t = self._preprocess(image).unsqueeze(0).to(self.device)
        with self._torch.no_grad():
            emb = self._model.encode_image(image_t)
            emb = emb / emb.norm(dim=-1, keepdim=True)
        return emb[0].detach().cpu().numpy().astype(np.float32)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def _mean_pairwise_cosine(embeddings: list[np.ndarray]) -> float:
    if len(embeddings) < 2:
        return float("nan")
    sims: list[float] = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sims.append(_cosine(embeddings[i], embeddings[j]))
    return float(np.mean(sims)) if sims else float("nan")


RUBRIC_TEMPLATE = [
    "product matches title",
    "correct color/material",
    "background is clean",
    "single product only",
    "catalog-ready composition",
]


def collect_image_paths(root_dir: Path) -> list[Path]:
    return sorted([p for p in root_dir.rglob("*.png") if p.is_file()])


def mean_phash_distance(paths: list[Path]) -> float:
    if len(paths) < 2:
        return 0.0
    if imagehash is not None:
        hashes = [imagehash.phash(Image.open(p)) for p in paths]
        distances = []
        for i in range(len(hashes)):
            for j in range(i + 1, len(hashes)):
                distances.append(hashes[i] - hashes[j])
        return float(np.mean(distances)) if distances else 0.0

    arrays = [np.asarray(Image.open(p).resize((64, 64)).convert("L"), dtype=np.float32) for p in paths]
    distances = []
    for i in range(len(arrays)):
        for j in range(i + 1, len(arrays)):
            distances.append(float(np.mean(np.abs(arrays[i] - arrays[j]))))
    return float(np.mean(distances)) if distances else 0.0


def build_qualitative_template(metadata: pd.DataFrame, output_csv: Path) -> Path:
    rubric_path = output_csv.with_name("qualitative_review_template.csv")
    review_rows = []
    for _, row in metadata.iterrows():
        for criterion in RUBRIC_TEMPLATE:
            review_rows.append(
                {
                    "product_id": row["product_id"],
                    "view": row["target_view"],
                    "criterion": criterion,
                    "baseline_score_1_to_5": "",
                    "structured_score_1_to_5": "",
                    "notes": "",
                }
            )
    pd.DataFrame(review_rows).to_csv(rubric_path, index=False)
    return rubric_path


def evaluate_system(
    metadata: pd.DataFrame,
    system_label: str,
    system_dir: Path,
    clip: ClipScorer,
    prompt_mode: str,
) -> tuple[dict, pd.DataFrame]:
    all_paths = collect_image_paths(system_dir)
    phash = mean_phash_distance(all_paths)

    rows: list[dict] = []
    image_embed_cache: dict[Path, np.ndarray | None] = {}
    hist_embed_cache: dict[Path, np.ndarray] = {}
    quality_raw_values: list[float] = []

    for _, row in metadata.iterrows():
        product_id = str(row["product_id"])
        prompt = str(row["baseline_prompt"]) if prompt_mode == "baseline" else _build_structured_prompt(row)
        prompt_emb = clip.encode_text(prompt) if clip.available else None

        image_paths = _collect_images_for_row(system_dir, row)
        if not image_paths:
            rows.append(
                {
                    "system": system_label,
                    "product_id": product_id,
                    "target_view": row["target_view"],
                    "image_path": "",
                    "prompt_alignment": np.nan,
                    "quality_raw": np.nan,
                }
            )
            continue

        for img_path in image_paths:
            quality_raw = _image_quality_raw(img_path)
            quality_raw_values.append(quality_raw)
            if img_path not in image_embed_cache:
                image_embed_cache[img_path] = clip.encode_image(img_path) if clip.available else None
            if img_path not in hist_embed_cache:
                hist_embed_cache[img_path] = _hist_embedding(img_path)

            alignment = np.nan
            img_emb = image_embed_cache[img_path]
            if prompt_emb is not None and img_emb is not None:
                alignment = _cosine(prompt_emb, img_emb)
            elif not clip.available:
                alignment = _color_alignment(prompt, img_path)

            rows.append(
                {
                    "system": system_label,
                    "product_id": product_id,
                    "target_view": row["target_view"],
                    "image_path": str(img_path),
                    "prompt_alignment": alignment,
                    "quality_raw": quality_raw,
                }
            )

    details = pd.DataFrame(rows)

    quality_norm = np.array([], dtype=np.float32)
    if quality_raw_values:
        quality_norm = _normalize(np.array(quality_raw_values, dtype=np.float32))

    quality_map: dict[str, float] = {}
    for pos, (_, drow) in enumerate(details.dropna(subset=["quality_raw"]).iterrows()):
        quality_map[str(drow["image_path"])] = float(quality_norm[pos]) if pos < len(quality_norm) else float("nan")
    details["quality_proxy"] = details["image_path"].map(quality_map)

    # Consistency: mean pairwise cosine embeddings within each product
    consistency_per_product: list[float] = []
    for product_id in sorted(metadata["product_id"].astype(str).unique()):
        product_paths = [p for p in all_paths if p.parent.name == product_id]
        if clip.available:
            embs = [image_embed_cache[p] for p in product_paths if image_embed_cache.get(p) is not None]
        else:
            embs = [hist_embed_cache[p] for p in product_paths if p in hist_embed_cache]
        if embs:
            consistency_per_product.append(_mean_pairwise_cosine(embs))

    # Diversity: pairwise pHash distance within each product (higher = more diverse)
    diversity_per_product: list[float] = []
    for product_id in sorted(metadata["product_id"].astype(str).unique()):
        product_paths = [p for p in all_paths if p.parent.name == product_id]
        diversity_per_product.append(mean_phash_distance(product_paths))

    summary = {
        "system": system_label,
        "num_images": int(len(all_paths)),
        "prompt_alignment": _safe_mean(details["prompt_alignment"].tolist()),
        "consistency": _safe_mean(consistency_per_product),
        "diversity": _safe_mean(diversity_per_product),
        "quality_proxy": _safe_mean(details["quality_proxy"].dropna().tolist()),
        "mean_phash_distance": phash,
        "clip_available": bool(clip.available),
        "alignment_mode": "clip" if clip.available else "color_fallback",
        "consistency_mode": "clip" if clip.available else "histogram_fallback",
    }
    return summary, details


def build_failure_cases(all_details: pd.DataFrame, output_csv: Path, top_k: int = 10) -> Path:
    failure_path = output_csv.with_name("failure_cases.csv")
    df = all_details.copy()
    if df.empty:
        pd.DataFrame(columns=["system", "product_id", "target_view", "image_path", "failure_score", "failure_reason"]).to_csv(
            failure_path, index=False
        )
        return failure_path

    # lower alignment and lower quality -> higher failure score
    align = df["prompt_alignment"].fillna(df["prompt_alignment"].mean(skipna=True))
    align = align.fillna(0.0)
    q = df["quality_proxy"].fillna(df["quality_proxy"].mean(skipna=True))
    q = q.fillna(0.0)

    df["failure_score"] = (1.0 - align) * 0.7 + (1.0 - q) * 0.3

    reasons = []
    for _, row in df.iterrows():
        align_val = float(row["prompt_alignment"]) if not pd.isna(row["prompt_alignment"]) else 0.0
        quality_val = float(row["quality_proxy"]) if not pd.isna(row["quality_proxy"]) else 0.0
        if align_val < 0.20:
            reasons.append("Low prompt alignment (image does not match metadata prompt well)")
        elif quality_val < 0.35:
            reasons.append("Low quality proxy (weak sharpness/contrast)")
        else:
            reasons.append("Potential consistency/diversity trade-off case")
    df["failure_reason"] = reasons

    keep_cols = [
        "system",
        "product_id",
        "target_view",
        "image_path",
        "prompt_alignment",
        "quality_proxy",
        "failure_score",
        "failure_reason",
    ]
    worst = df.sort_values("failure_score", ascending=False).head(top_k)[keep_cols]
    worst.to_csv(failure_path, index=False)
    return failure_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--baseline_dir", required=True)
    parser.add_argument("--improved_dir", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--device", default="cpu", help="Device for CLIP embedding model: cpu|cuda|mps")
    args = parser.parse_args()

    metadata = pd.read_csv(args.metadata)
    clip = ClipScorer(device=args.device)

    baseline, baseline_details = evaluate_system(
        metadata=metadata,
        system_label="baseline",
        system_dir=Path(args.baseline_dir),
        clip=clip,
        prompt_mode="baseline",
    )
    improved, improved_details = evaluate_system(
        metadata=metadata,
        system_label="structured",
        system_dir=Path(args.improved_dir),
        clip=clip,
        prompt_mode="structured",
    )

    summary = pd.DataFrame([baseline, improved])

    # Explicit baseline-vs-improved delta row
    delta = {"system": "delta_structured_minus_baseline"}
    metric_cols = [
        "num_images",
        "prompt_alignment",
        "consistency",
        "diversity",
        "quality_proxy",
        "mean_phash_distance",
    ]
    for col in metric_cols:
        delta[col] = float(summary.loc[summary["system"] == "structured", col].values[0]) - float(
            summary.loc[summary["system"] == "baseline", col].values[0]
        )
    delta["clip_available"] = baseline["clip_available"] and improved["clip_available"]
    summary = pd.concat([summary, pd.DataFrame([delta])], ignore_index=True)

    summary.to_csv(args.output_csv, index=False)

    all_details = pd.concat([baseline_details, improved_details], ignore_index=True)
    details_path = Path(args.output_csv).with_name("evaluation_details.csv")
    all_details.to_csv(details_path, index=False)

    rubric_path = build_qualitative_template(metadata, Path(args.output_csv))
    failure_path = build_failure_cases(all_details, Path(args.output_csv), top_k=10)

    print(summary)
    print(f"Saved summary to {args.output_csv}")
    print(f"Saved per-image metrics to {details_path}")
    print(f"Saved qualitative template to {rubric_path}")
    print(f"Saved failure cases to {failure_path}")


if __name__ == "__main__":
    main()
