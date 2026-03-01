# JPG-to-PNG Logo Converter

Convert JPG logos to PNG with artifact cleanup: removes JPEG edge ringing and mosquito noise, and smooths solid color fills.

## What it does

- **Non-local means denoising** — reduces edge fringing and compression artifacts typical of JPEG
- **Bilateral filter** — smooths flat regions while keeping sharp edges
- **Color quantization** — flattens subtle color variation in solid fills (default 16 colors, good for logos)

Input images are read from `input/` and written as PNG to `output/`.

## Setup

```bash
python3 -m venv converter
source converter/bin/activate   # Windows: converter\Scripts\activate
pip install -r requirements.txt
```

## Usage

1. Put your `.jpg` or `.jpeg` files in the `input/` folder.
2. Run the script (optionally with resize options).
3. Cleaned PNGs appear in `output/` with the same base filename.

### Basic conversion (no resize)

Process all JPGs in `input/` and save cleaned PNGs at original size:

```bash
python convert.py
```

### Resize by long side

Limit the longest dimension to N pixels; aspect ratio is preserved. Use when you want a max width or height without cropping:

```bash
# Long side 512 pixels (e.g. 512×384 or 400×512)
python convert.py --max-size 512

# Long side 256 pixels
python convert.py --max-size 256
```

### Square output (center crop)

Resize so the **short** side is N pixels, then center-crop to produce an N×N square. Use for avatars, icons, or thumbnails:

```bash
# 256×256 square
python convert.py --square 256

# 512×512 square
python convert.py --square 512
```

**Note:** `--max-size` and `--square` cannot be used together. Use one or the other.

## Options summary

| Option        | Description |
|---------------|-------------|
| `--max-size N` | Resize so the long side is N pixels; aspect ratio preserved. |
| `--square N`   | Resize so the short side is N pixels, then center-crop to N×N. |

## Project layout

```
jpg-png/
  convert.py       # Main script
  requirements.txt # opencv-python, Pillow, numpy
  input/           # Drop JPG files here
  output/          # Cleaned PNGs appear here
```

Denoising, bilateral, and color-quantization parameters can be adjusted at the top of `convert.py` if you need different strength or palette size.
# utils-jpg-png
