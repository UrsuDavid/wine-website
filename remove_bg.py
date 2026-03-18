#!/usr/bin/env python3
"""
Remove background from an image using rembg (AI-based).
Output is PNG with transparency. Use for hero/photo images (non-solid backgrounds).
Usage: python remove_bg.py <input.png> [output.png]
Requires: pip install rembg[gpu]  or  pip install rembg
"""
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python remove_bg.py <input.png> [output.png]", file=sys.stderr)
        sys.exit(1)
    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else in_path.parent / (in_path.stem + "_nobg.png")
    if not in_path.exists():
        print("File not found:", in_path, file=sys.stderr)
        sys.exit(1)
    try:
        from rembg import remove
        from PIL import Image
    except ImportError as e:
        print("Install rembg and Pillow: pip install rembg Pillow", file=sys.stderr)
        sys.exit(1)
    with Image.open(in_path) as im:
        out = remove(im)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path, "PNG")
    print("Saved:", out_path)

if __name__ == "__main__":
    main()
