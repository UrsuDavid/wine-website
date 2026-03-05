#!/usr/bin/env python3
"""
Remove solid white (or near-white) background from PNG images.
Makes pixels with R,G,B above threshold transparent so the subject (e.g. wine bottle) is isolated.
Usage:
  python3 remove_white_bg.py <input.png> [output.png]
  python3 remove_white_bg.py --dir <input_dir> --out <output_dir>
"""
import os
import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Please install Pillow: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)


def rgba_and_white_mask(im, threshold=248, fuzz=8):
    """Convert to RGBA and build mask of white/near-white pixels (to make transparent)."""
    if im.mode != "RGB" and im.mode != "RGBA":
        im = im.convert("RGB")
    if im.mode == "RGB":
        im = im.convert("RGBA")
    data = im.getdata()
    low = max(0, threshold - fuzz)
    new_data = []
    for item in data:
        r, g, b = item[0], item[1], item[2]
        a = item[3] if len(item) == 4 else 255
        if r >= low and g >= low and b >= low:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, a))
    im.putdata(new_data)
    return im


def process_file(in_path, out_path, threshold=248, fuzz=8):
    """Process one image: make white background transparent."""
    with Image.open(in_path) as im:
        im = rgba_and_white_mask(im, threshold=threshold, fuzz=fuzz)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(out_path, "PNG")
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Remove white background from PNG images.")
    ap.add_argument("input", nargs="?", help="Input PNG path")
    ap.add_argument("output", nargs="?", help="Output PNG path (default: input_no_bg.png)")
    ap.add_argument("--dir", help="Process all PNGs in this directory")
    ap.add_argument("--out", help="Output directory when using --dir")
    ap.add_argument("--threshold", type=int, default=248, help="RGB min for white (default 248)")
    ap.add_argument("--fuzz", type=int, default=8, help="Tolerance below threshold (default 8)")
    args = ap.parse_args()

    if args.dir:
        out_dir = Path(args.out or args.dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for p in Path(args.dir).glob("*.png"):
            out_path = out_dir / (p.stem + "_nobg.png")
            try:
                process_file(str(p), str(out_path), threshold=args.threshold, fuzz=args.fuzz)
                count += 1
                print("Processed:", p.name, "->", out_path.name)
            except Exception as e:
                print("Skip", p.name, ":", e, file=sys.stderr)
        print("Done. Processed", count, "images.")
        return

    if not args.input:
        ap.print_help()
        sys.exit(1)
    in_path = Path(args.input)
    if not in_path.exists():
        print("File not found:", in_path, file=sys.stderr)
        sys.exit(1)
    out_path = args.output or (in_path.parent / (in_path.stem + "_nobg.png"))
    process_file(str(in_path), str(out_path), threshold=args.threshold, fuzz=args.fuzz)
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
