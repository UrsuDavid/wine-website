#!/usr/bin/env python3
"""
Fetch production years from wine.md product pages and update `vintage` in
`wine-data.js`.

Purpose:
  - Currently `wine-data.js` has vintage: '' for all products.
  - UI (wines.js + wine-detail.js) already renders "0.75 l • YEAR an" when
    p.vintage is non-empty.

This script updates only the `vintage` field (does not rebuild the full data
set / does not rescrape catalog).

Run:
  python scripts/fetch_wine_md_years.py

Testing:
  LIMIT=5 python scripts/fetch_wine_md_years.py
  DELAY=0.25 python scripts/fetch_wine_md_years.py
"""

import os
import re
import time
import ssl
import urllib.request
import urllib.parse

BASE = "https://wine.md/"
WINE_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "wine-data.js")

LIMIT = int(os.environ.get("LIMIT", "0") or "0")  # 0 = all
DELAY = float(os.environ.get("DELAY", "0.35") or "0.35")
PID_FILTER = (os.environ.get("PID", "") or "").strip()

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def fetch(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; WineCatalog/1.0)"})
        with urllib.request.urlopen(req, timeout=25, context=_ctx) as r:
            return r.read().decode("utf-8", errors="replace")
    except UnicodeEncodeError:
        # Some product URLs may contain non-ascii characters; percent-encode them.
        safe = ":/?&=%#"
        url2 = urllib.parse.quote(url, safe=safe)
        req = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0 (compatible; WineCatalog/1.0)"})
        with urllib.request.urlopen(req, timeout=25, context=_ctx) as r:
            return r.read().decode("utf-8", errors="replace")


def html_to_plain_text(html: str) -> str:
    # Strip scripts/styles and then remove all tags, leaving only text.
    plain = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"&nbsp;|\u00a0", " ", plain)
    return plain


def extract_vintage_year_from_product_page(html: str):
    """
    Extract Romanian production year from wine.md product pages, e.g.
      "- An: 2025"
    Returns a 4-digit string or None.
    """
    plain = html_to_plain_text(html)

    # Bullet-style match is more specific.
    m = re.search(r"(?:^|\n)\s*-\s*An\s*:\s*(\d{4})\b", plain, flags=re.I | re.M)
    if not m:
        # Word boundaries are unreliable after tag-stripping; match without them.
        m = re.search(r"An\s*:\s*(\d{4})", plain, flags=re.I)
    return m.group(1).strip() if m else None


def is_bottle_product(product_page_url: str) -> bool:
    """
    Filter out accessories/spirits/gifts/chocolates that don't have a vintage year.
    Mirrors the intent of `scripts/fetch_wine_md_images.py` so we don't waste time
    fetching non-wine items.
    """
    u = (product_page_url or "").lower()
    if "/accesorii/" in u or "/spirtoase/" in u or "/produse-gourmet/" in u:
        return False
    if "/gifts/" in u or "/suvenire/" in u or "vacuvin" in u:
        return False
    if "chocolate" in u or "/chocolate" in u:
        return False
    return True


def parse_products(lines):
    """
    Yield tuples (index, pid, productPageUrl, current_vintage, line).
    We rely on wine-data.js formatting where each product is on one line.
    """
    for i, line in enumerate(lines):
        if "productPageUrl:" not in line or "vintage:" not in line:
            continue

        if "wine.md" not in line:
            continue

        pid_m = re.search(r"id:\s*['\"]([^'\"]+)['\"]", line)
        purl_m = re.search(r"productPageUrl:\s*['\"]([^'\"]+)['\"]", line)
        vint_m = re.search(r"vintage:\s*['\"]([^'\"]*)['\"]", line)
        if not (pid_m and purl_m and vint_m):
            continue

        pid = pid_m.group(1)
        purl = purl_m.group(1)
        current_vintage = vint_m.group(1) or ""

        yield (i, pid, purl, current_vintage, line)


def main():
    if not os.path.isfile(WINE_DATA_PATH):
        raise SystemExit(f"Missing wine-data.js at: {WINE_DATA_PATH}")

    with open(WINE_DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    updates = 0
    total_candidates = 0
    processed_candidates = 0

    for j, (idx, pid, purl, current_vintage, line) in enumerate(parse_products(lines)):
        if current_vintage.strip():
            continue
        if PID_FILTER and pid != PID_FILTER:
            continue
        if not is_bottle_product(purl):
            continue

        total_candidates += 1
        if LIMIT and processed_candidates >= LIMIT:
            break
        processed_candidates += 1

        try:
            print(f"[{j+1}] Fetching vintage for {pid} ...", flush=True)
            html = fetch(purl)
            vintage_year = extract_vintage_year_from_product_page(html)
            if not vintage_year:
                print(f"  - No year found (keeping empty).", flush=True)
                continue

            # Replace vintage: '' with vintage: 'YYYY'
            new_line = re.sub(r"vintage:\s*''", f"vintage: '{vintage_year}'", line, count=1)
            if new_line != line:
                lines[idx] = new_line
                updates += 1
                print(f"  - UPDATED vintage => {vintage_year}", flush=True)
            else:
                print("  - Vintage pattern not replaced (format mismatch).", flush=True)
        except Exception as e:
            print(f"  - ERROR fetching/parsing: {e}", flush=True)

        time.sleep(DELAY)

    with open(WINE_DATA_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Done. Updated vintage for {updates} products (candidates: {total_candidates}).", flush=True)


if __name__ == "__main__":
    main()

