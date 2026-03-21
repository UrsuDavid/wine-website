#!/usr/bin/env python3
"""Fetch awards from wine.md filtered catalog pages into `wine-data.js`."""

import os
import re
import ssl
import urllib.parse
import urllib.request

WINE_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "wine-data.js")

PID_FILTER = (os.environ.get("PID", "") or "").strip()

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

AWARDS = [
    "Asia Wine Trophy",
    "Berliner Wine Trophy Spring Tasting",
    "DWWA",
    "Effervescents du Monde",
    "Mundus Vini",
    "Vinarium International Wine Contest",
    "Wine competitions 2017",
]

# Seeded from live wine.md award filter pages (when HTML responses hide product cards).
SEED_SLUG_AWARDS = {
    "crama-tataru-aligote": ["Asia Wine Trophy"],
    "atu-calibru-feteasca-neagra-merlot-cabernet-sauvignon": ["Asia Wine Trophy"],
    "minis-terrios-negru-imparat": ["Asia Wine Trophy"],
    "gogu-instinct-pinot-noir": ["Berliner Wine Trophy Spring Tasting"],
    "atu-saperavicodrinschii-8210": ["Berliner Wine Trophy Spring Tasting"],
    "vinum-estate-cabernet-merlot-saperavi": ["Berliner Wine Trophy Spring Tasting"],
    "fume-blanc-bardul-din-mirce": ["Berliner Wine Trophy Spring Tasting"],
    "crama-mircesti-feteasca-neagra": ["Berliner Wine Trophy Spring Tasting"],
    "crama-tataru-cabernet-merlot": ["Berliner Wine Trophy Spring Tasting"],
    "famber-cabernet-sauvignon": ["Berliner Wine Trophy Spring Tasting"],
    "divus-ornis": ["DWWA"],
    "famber-merlot": ["DWWA"],
    "minis-terrios-rosu-imparat": ["DWWA"],
    "vinum-selection-vladlen-feteasca-neagra-light-barrique": ["DWWA"],
    "vornic-winery-riesling-de-rhein": ["DWWA"],
    "tewa-feteasca-neagra": ["DWWA"],
    "vinum-estate-brut-natur": ["Effervescents du Monde"],
    "et-cetera-cuvee-blanc": ["Wine competitions 2017"],
}


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


def is_bottle_product(product_page_url: str) -> bool:
    u = (product_page_url or "").lower()
    if "/accesorii/" in u or "/spirtoase/" in u or "/produse-gourmet/" in u:
        return False
    if "/gifts/" in u or "/suvenire/" in u or "vacuvin" in u:
        return False
    if "chocolate" in u or "/chocolate" in u:
        return False
    return True


def normalize_product_url(url: str) -> str:
    u = (url or "").strip().split("?", 1)[0].split("#", 1)[0]
    u = u.replace("/catalog/catalog/", "/catalog/")
    return u.rstrip("/")


def extract_product_urls_from_catalog_html(html: str):
    urls = set()
    patterns = [
        r'href=[\'"](https://wine\.md/catalog/(?:catalog/)?(?:wine|vinuri-spumante)/[^\'"]+)[\'"]',
        r'href=[\'"](/catalog/(?:catalog/)?(?:wine|vinuri-spumante)/[^\'"]+)[\'"]',
    ]
    for pat in patterns:
        for m in re.finditer(pat, html, flags=re.I):
            raw = m.group(1)
            if raw.startswith("/"):
                raw = "https://wine.md" + raw
            urls.add(normalize_product_url(raw))
    return urls


def parse_products(lines):
    for i, line in enumerate(lines):
        if "productPageUrl:" not in line:
            continue
        if "wine.md" not in line:
            continue
        pid_m = re.search(r"id:\s*['\"]([^'\"]+)['\"]", line)
        purl_m = re.search(r"productPageUrl:\s*['\"]([^'\"]+)['\"]", line)
        awards_arr_m = re.search(r"awards:\s*\[([^\]]*)\]", line)
        awards_str_m = re.search(r"awards:\s*'([^']*)'", line)
        if not (pid_m and purl_m):
            continue
        current = ""
        if awards_arr_m:
            current = awards_arr_m.group(1)
        elif awards_str_m:
            current = awards_str_m.group(1)
        yield (i, pid_m.group(1), normalize_product_url(purl_m.group(1)), current, line, bool(awards_arr_m or awards_str_m))


def format_awards_array(awards):
    safe = [a.replace("\\", "\\\\").replace("'", "\\'") for a in awards]
    return "[" + ", ".join("'" + a + "'" for a in safe) + "]"


def main():
    if not os.path.isfile(WINE_DATA_PATH):
        raise SystemExit(f"Missing wine-data.js at: {WINE_DATA_PATH}")
    with open(WINE_DATA_PATH, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    award_to_urls = {}
    for award in AWARDS:
        q = urllib.parse.urlencode({"awards": award})
        u = f"https://wine.md/catalog/wine?{q}"
        print(f"Fetching catalog for award: {award}", flush=True)
        try:
            html = fetch(u)
            urls = extract_product_urls_from_catalog_html(html)
            award_to_urls[award] = urls
            print(f"  - found {len(urls)} product links", flush=True)
            if urls:
                print("  - sample:", ", ".join(sorted(urls)[:3]), flush=True)
        except Exception as e:
            award_to_urls[award] = set()
            print(f"  - ERROR: {e}", flush=True)

    updates = 0
    candidates = 0
    for idx, pid, purl, _current_awards, line, has_awards_field in parse_products(lines):
        if PID_FILTER and pid != PID_FILTER:
            continue
        if not is_bottle_product(purl):
            continue
        candidates += 1

        matched = [award for award in AWARDS if purl in award_to_urls.get(award, set())]
        slug_l = purl.lower()
        for seed_slug, seed_awards in SEED_SLUG_AWARDS.items():
            if seed_slug in slug_l:
                for aw in seed_awards:
                    if aw not in matched:
                        matched.append(aw)
        if not matched:
            continue

        awards_lit = format_awards_array(matched)
        if has_awards_field:
            new_line = re.sub(r"awards:\s*\[[^\]]*\]", "awards: " + awards_lit, line, count=1)
            if new_line == line:
                new_line = re.sub(r"awards:\s*'[^']*'", "awards: " + awards_lit, line, count=1)
        else:
            if re.search(r"taste:\s*'[^']*'", line):
                new_line = re.sub(r"(taste:\s*'[^']*')", r"\1, awards: " + awards_lit, line, count=1)
            elif re.search(r"grape:\s*'[^']*'", line):
                new_line = re.sub(r"(grape:\s*'[^']*')", r"\1, awards: " + awards_lit, line, count=1)
            else:
                new_line = re.sub(r"(productPageUrl:\s*'[^']*')", r"\1, awards: " + awards_lit, line, count=1)
        if new_line == line:
            print(f"  - Awards pattern mismatch for {pid} (not updated).", flush=True)
            continue
        lines[idx] = new_line
        updates += 1

    with open(WINE_DATA_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Done. Updated awards for {updates} products (candidates: {candidates}).", flush=True)


if __name__ == "__main__":
    main()
