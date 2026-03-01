#!/usr/bin/env python3
"""
Convert JPG logos to PNG with artifact cleanup:
- Removes JPEG edge ringing / mosquito noise (non-local means denoising)
- Smooths solid color fills (bilateral filter + color quantization)
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# -----------------------------------------------------------------------------
# Configurable parameters
# -----------------------------------------------------------------------------
INPUT_DIR = Path(__file__).resolve().parent / "input"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Non-local means denoising (reduces edge ringing / JPEG artifacts)
DENOISE_H = 10  # Luminance filter strength (higher = more smoothing)
DENOISE_H_COLOR = 10  # Color component filter strength
DENOISE_TEMPLATE_SIZE = 7
DENOISE_SEARCH_SIZE = 21

# Bilateral filter (smooths flat regions, preserves edges)
BILATERAL_D = 9  # Diameter of pixel neighborhood
BILATERAL_SIGMA_COLOR = 75  # Filter sigma in color space
BILATERAL_SIGMA_SPACE = 75  # Filter sigma in coordinate space

# Color quantization (flattens solid fills to a limited palette)
N_COLORS = 16  # Number of colors in output (suitable for most logos)

# -----------------------------------------------------------------------------
# Processing pipeline
# -----------------------------------------------------------------------------


def load_jpg(path: Path) -> np.ndarray:
    """Load JPG as BGR (OpenCV convention)."""
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Could not load image: {path}")
    return img


def denoise(img: np.ndarray) -> np.ndarray:
    """Remove JPEG compression artifacts (edge ringing, mosquito noise)."""
    return cv2.fastNlMeansDenoisingColored(
        img,
        None,
        h=DENOISE_H,
        hColor=DENOISE_H_COLOR,
        templateWindowSize=DENOISE_TEMPLATE_SIZE,
        searchWindowSize=DENOISE_SEARCH_SIZE,
    )


def bilateral_smooth(img: np.ndarray) -> np.ndarray:
    """Smooth flat regions while preserving sharp edges."""
    return cv2.bilateralFilter(
        img,
        d=BILATERAL_D,
        sigmaColor=BILATERAL_SIGMA_COLOR,
        sigmaSpace=BILATERAL_SIGMA_SPACE,
    )


def quantize_colors(img: np.ndarray, n_colors: int = N_COLORS) -> np.ndarray:
    """Reduce palette to n_colors via K-means; smooths solid fills."""
    h, w, c = img.shape
    pixels = img.astype(np.float32).reshape(-1, c)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, n_colors, None, criteria, 10, cv2.KMEANS_PP_CENTERS
    )
    centers = np.uint8(centers)
    quantized = centers[labels.flatten()].reshape(h, w, c)
    return quantized


def process_image(img: np.ndarray) -> np.ndarray:
    """Run full pipeline: denoise -> bilateral -> color quantization."""
    img = denoise(img)
    img = bilateral_smooth(img)
    img = quantize_colors(img)
    return img


def resize_long_side(img: np.ndarray, n: int) -> np.ndarray:
    """Resize image so the long side is n pixels; aspect ratio preserved."""
    h, w = img.shape[:2]
    long_side = max(h, w)
    if long_side <= n:
        return img
    scale = n / long_side
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def resize_to_square(img: np.ndarray, n: int) -> np.ndarray:
    """Resize so short side is n pixels, then center-crop to n×n."""
    h, w = img.shape[:2]
    short_side = min(h, w)
    if short_side == 0:
        return img
    scale = n / short_side
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    # Center crop to n×n
    x = (new_w - n) // 2
    y = (new_h - n) // 2
    return resized[y : y + n, x : x + n]


def save_png(img_bgr: np.ndarray, path: Path) -> None:
    """Save BGR array as PNG (Pillow for reliable PNG output)."""
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    Image.fromarray(rgb).save(path, "PNG")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert JPG logos to PNG with artifact cleanup."
    )
    parser.add_argument(
        "--max-size",
        type=int,
        metavar="N",
        default=None,
        help="Resize output so the long side is N pixels (keeps aspect ratio)",
    )
    parser.add_argument(
        "--square",
        type=int,
        metavar="N",
        default=None,
        help="Resize so short side is N pixels and center-crop to N×N square",
    )
    args = parser.parse_args()
    if args.max_size is not None and args.square is not None:
        parser.error("--max-size and --square are mutually exclusive")

    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    extensions = (".jpg", ".jpeg")
    paths = [
        p
        for p in INPUT_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    ]

    if not paths:
        print(f"No .jpg/.jpeg files found in {INPUT_DIR}")
        return 0

    print(f"Found {len(paths)} file(s) in {INPUT_DIR}")
    for path in sorted(paths):
        out_path = OUTPUT_DIR / (path.stem + ".png")
        try:
            img = load_jpg(path)
            cleaned = process_image(img)
            if args.square is not None:
                cleaned = resize_to_square(cleaned, args.square)
            elif args.max_size is not None:
                cleaned = resize_long_side(cleaned, args.max_size)
            save_png(cleaned, out_path)
            print(f"  {path.name} -> {out_path.name}")
        except Exception as e:
            print(f"  {path.name}: ERROR - {e}", file=sys.stderr)

    print(f"Done. Output in {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
