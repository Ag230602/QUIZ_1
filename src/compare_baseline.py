from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_png", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    x = range(len(df))

    plt.figure(figsize=(8, 5))
    plt.bar(x, df["num_images"])
    plt.xticks(list(x), df["system"])
    plt.ylabel("Number of images found")
    plt.title("Baseline vs Structured Output Coverage")
    plt.tight_layout()
    plt.savefig(args.output_png, dpi=200)


if __name__ == "__main__":
    main()
