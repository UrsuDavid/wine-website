# aiwine

## Image quality

Product images use full-size URLs when available. The scraper writes `imageUrl` (full-size) and `imageUrlSmall` (fallback) into `wine-data.js`. Re-run it to refresh:

```bash
cd /Users/mariusdavid/Public/wine
python3 scripts/scrape_wine_md.py
```

If you host images on your own upload page, you can add a script that fetches each product image, uploads it to your endpoint, and updates `imageUrl` in the generated data.

---

## Remove white background from product photos

To strip solid white backgrounds from PNGs (e.g. bottle shots):

```bash
cd /Users/mariusdavid/Public/wine
PYTHONPATH=./vendor python3 remove_white_bg.py <input.png> [output.png]
# or batch: python3 remove_white_bg.py --dir <input_dir> --out <output_dir>
```

Requires `pip3 install --target ./vendor Pillow`. Processed images are saved under `assets/` (single file) or `assets/processed/` (batch; each file as `*_nobg.png`).

---

Local preview:

```bash
cd /Users/mariusdavid/Public/wine
chmod +x serve.sh
./serve.sh 8765
```

Then open `http://localhost:8765`.
