#!/usr/bin/env python3
"""
Fetch taste (Gust) from wine.md product pages and update `taste` in `wine-data.js`.

Run:
  python scripts/fetch_wine_md_taste.py
"""

import os
import re
import ssl
import time
import urllib.parse
import urllib.request

WINE_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "wine-data.js")

LIMIT = int(os.environ.get("LIMIT", "0") or "0")
DELAY = float(os.environ.get("DELAY", "0.12") or "0.12")
PID_FILTER = (os.environ.get("PID", "") or "").strip()
CHECKPOINT_EVERY = int(os.environ.get("CHECKPOINT_EVERY", "25") or "25")

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def fetch(url: str) -> str:
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
    return " ".join(plain.split())


def is_bottle_product(product_page_url: str) -> bool:
    u = (product_page_url or "").lower()
    if "/accesorii/" in u or "/spirtoase/" in u or "/produse-gourmet/" in u:
        return False
    if "/gifts/" in u or "/suvenire/" in u or "vacuvin" in u:
        return False
    if "chocolate" in u or "/chocolate" in u:
        return False
    return True


def extract_taste_from_product_page(html: str):
    plain = html_to_plain_text(html)
    m = re.search(
        r"Gust\s*:\s*(.+?)(?:\s+(?:Culoare|An|Alcoolul|Volumul|Țara|Struguri|Servind|Compatibilitate)\s*:|\s+Servind\b|\s+Compatibilitate\b|$)",
        plain,
        flags=re.I,
    )
    if not m:
        return None
    val = " ".join(m.group(1).split()).strip(" -;,.")
    if not val or len(val) > 60:
        return None
    return val


def parse_products(lines):
    for i, line in enumerate(lines):
        if "productPageUrl:" not in line:
            continue
        if "wine.md" not in line:
            continue
        pid_m = re.search(r"id:\s*['\"]([^'\"]+)['\"]", line)
        purl_m = re.search(r"productPageUrl:\s*['\"]([^'\"]+)['\"]", line)
        taste_m = re.search(r"taste:\s*['\"]([^'\"]*)['\"]", line)
        if not (pid_m and purl_m):
            continue
        current_taste = taste_m.group(1) if taste_m else ""
        yield (i, pid_m.group(1), purl_m.group(1), current_taste, line, bool(taste_m))


def main():
    if not os.path.isfile(WINE_DATA_PATH):
        raise SystemExit(f"Missing wine-data.js at: {WINE_DATA_PATH}")
    with open(WINE_DATA_PATH, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    updates = 0
    candidates = 0

    for idx, pid, purl, current_taste, line, has_taste_field in parse_products(lines):
        if PID_FILTER and pid != PID_FILTER:
            continue
        if not is_bottle_product(purl):
            continue
        if current_taste and str(current_taste).strip():
            continue
        candidates += 1
        if LIMIT and updates >= LIMIT:
            break
        try:
            print(f"Fetching taste for {pid} ...", flush=True)
            html = fetch(purl)
            taste = extract_taste_from_product_page(html)
            if not taste:
                print("  - No taste found (keeping current).", flush=True)
                continue
            safe_taste = taste.replace("\\", "\\\\").replace("'", "\\'")
            if has_taste_field:
                new_line = re.sub(r"taste:\s*'[^']*'", "taste: '" + safe_taste + "'", line, count=1)
            else:
                new_line = re.sub(r"(grape:\s*'[^']*')", r"\1, taste: '" + safe_taste + "'", line, count=1)
            if new_line == line:
                print("  - Taste pattern mismatch (not updated).", flush=True)
                continue
            lines[idx] = new_line
            updates += 1
            print(f"  - UPDATED taste => {taste}", flush=True)
            if CHECKPOINT_EVERY > 0 and updates % CHECKPOINT_EVERY == 0:
                with open(WINE_DATA_PATH, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
                print(f"  - checkpoint saved at {updates} updates", flush=True)
        except Exception as e:
            print(f"  - ERROR fetching/parsing: {e}", flush=True)
        time.sleep(DELAY)

    with open(WINE_DATA_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Done. Updated taste for {updates} products (candidates: {candidates}).", flush=True)


if __name__ == "__main__":
    main()

