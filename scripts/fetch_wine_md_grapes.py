#!/usr/bin/env python3
"""
Fetch grapes (Struguri) from wine.md product pages and update `grape` in
`wine-data.js`.

UI already renders `p.grape` in `wine-detail.js`, so once `wine-data.js` is
updated, product pages will show the correct grape.

Run:
  python scripts/fetch_wine_md_grapes.py

Testing:
  PID=<wine-data.js id> LIMIT=1 python scripts/fetch_wine_md_grapes.py
"""

import os
import re
import ssl
import time
import urllib.parse
import urllib.request

BASE = "https://wine.md/"
WINE_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "wine-data.js")

LIMIT = int(os.environ.get("LIMIT", "0") or "0")  # 0 = all candidates
DELAY = float(os.environ.get("DELAY", "0.35") or "0.35")
PID_FILTER = (os.environ.get("PID", "") or "").strip()

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def fetch(url: str) -> str:
    """
    Fetch HTML from wine.md. Some product URLs contain non-ascii chars, so
    percent-encode them if the initial request fails.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; WineCatalog/1.0)"})
        with urllib.request.urlopen(req, timeout=25, context=_ctx) as r:
            return r.read().decode("utf-8", errors="replace")
    except UnicodeEncodeError:
        safe = ":/?&=%#"
        url2 = urllib.parse.quote(url, safe=safe)
        req = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0 (compatible; WineCatalog/1.0)"})
        with urllib.request.urlopen(req, timeout=25, context=_ctx) as r:
            return r.read().decode("utf-8", errors="replace")


def html_to_plain_text(html: str) -> str:
    plain = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"&nbsp;|\u00a0", " ", plain)
    return plain


def is_bottle_product(product_page_url: str) -> bool:
    u = (product_page_url or "").lower()
    if "/accesorii/" in u or "/spirtoase/" in u or "/produse-gourmet/" in u:
        return False
    if "/gifts/" in u or "/suvenire/" in u or "vacuvin" in u:
        return False
    if "chocolate" in u or "/chocolate" in u:
        return False
    return True


def extract_grapes_from_product_page(html: str):
    """
    Extract Romanian grapes value, e.g.:
      - Struguri: Feteasca Neagra
    Returns a string or None.
    """
    plain = html_to_plain_text(html)
    # More specific: bullet list "- Struguri: ...".
    m = re.search(r"(?:^|\n)\s*-\s*Struguri\s*:\s*([^\n]+)", plain, flags=re.I | re.M)
    if not m:
        m = re.search(r"Struguri\s*:\s*([^\n]+)", plain, flags=re.I)
    if not m:
        return None
    val = m.group(1).strip()
    val = " ".join(val.split())
    # Remove trailing "Gust:" section if it accidentally got captured.
    val = re.split(r"\bGust\b\s*:", val, flags=re.I)[0].strip()
    return val or None


def parse_products(lines):
    """
    Yield tuples (line_index, pid, productPageUrl, current_grape, line).
    We rely on wine-data.js formatting where each product is one line.
    """
    for i, line in enumerate(lines):
        if "productPageUrl:" not in line or "grape:" not in line:
            continue
        if "wine.md" not in line:
            continue

        pid_m = re.search(r"id:\s*['\"]([^'\"]+)['\"]", line)
        purl_m = re.search(r"productPageUrl:\s*['\"]([^'\"]+)['\"]", line)
        grape_m = re.search(r"grape:\s*['\"]([^'\"]*)['\"]", line)
        if not (pid_m and purl_m and grape_m):
            continue

        pid = pid_m.group(1)
        purl = purl_m.group(1)
        current_grape = grape_m.group(1) or ""

        yield (i, pid, purl, current_grape, line)


def main():
    if not os.path.isfile(WINE_DATA_PATH):
        raise SystemExit(f"Missing wine-data.js at: {WINE_DATA_PATH}")

    with open(WINE_DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    updates = 0
    candidates = 0

    # `wine-data.js` may be formatted as a single huge line. So we match product
    # object blocks by looking at `id`, `productPageUrl`, and `grape`.
    # Assumption: each product object uses `grape: '...'` and ends at the next `}`.
    product_re = re.compile(
        r"\{\s*id:\s*'(?P<id>[^']+)'.*?productPageUrl:\s*'(?P<purl>[^']+)'.*?grape:\s*'(?P<grape>[^']*)'.*?\}",
        flags=re.DOTALL,
    )
    matches = list(product_re.finditer(content))

    # Replace from the end so earlier spans stay valid.
    for mi in reversed(matches):
        pid = mi.group("id")
        purl = mi.group("purl")
        current_grape = mi.group("grape") or ""

        if PID_FILTER and pid != PID_FILTER:
            continue
        if not is_bottle_product(purl):
            continue
        # Update only when grapes are missing or the generic placeholder.
        if current_grape.strip() and current_grape.strip().lower() != "blend":
            continue

        candidates += 1
        if LIMIT and updates >= LIMIT:
            break

        try:
            print(f"Fetching grapes for {pid} ...", flush=True)
            html = fetch(purl)
            grapes = extract_grapes_from_product_page(html)
            if not grapes:
                print("  - No grapes found (keeping current).", flush=True)
                continue

            new_grapes = grapes.replace("\\\\", "\\\\\\\\").replace("'", "\\\\'")
            block = content[mi.start():mi.end()]
            new_block = re.sub(r"grape:\s*'[^']*'", "grape: '" + new_grapes + "'", block, count=1)
            if new_block == block:
                print("  - Grape pattern mismatch (not updated).", flush=True)
                continue

            content = content[: mi.start()] + new_block + content[mi.end() :]
            updates += 1
            print(f"  - UPDATED grape => {grapes}", flush=True)
        except Exception as e:
            print(f"  - ERROR fetching/parsing: {e}", flush=True)

        time.sleep(DELAY)

    with open(WINE_DATA_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Done. Updated grapes for {updates} products (candidates: {candidates}).", flush=True)


if __name__ == "__main__":
    main()

