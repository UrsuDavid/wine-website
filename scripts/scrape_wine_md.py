#!/usr/bin/env python3
"""
Scrape all wine products from wine.md catalog and generate wine-data.js.
Uses only stdlib (urllib, re). Run: python scripts/scrape_wine_md.py

By default merges with ../wine-data.js: keeps existing lines (taste, awards, vivino, etc.)
and appends only products missing by productPageUrl. New rows are enriched from each
wine.md product page (volume, vintage, taste, grape) like the rest of the catalog, get
firstSeenAt: 'YYYY-MM-DD' for the 14-day "NEW" badge, and then follow the same site rules
(filters, cards, cart, descriptions.js) as existing products.
Use --full-rebuild to replace the file (does not add firstSeenAt to every product).

Env: VINTAGE_LIMIT (0=all), VINTAGE_DELAY (seconds between product fetches).
"""
import argparse
import urllib.request
import urllib.error
import urllib.parse
import re
import time
import os
import ssl
from datetime import date

BASE = "https://wine.md/"
# Master list (all wines) + sparkling category: many spumante/champagne SKUs appear only on
# vinuri-spumante ("Produse găsite: 164") and are absent from catalog/wine pagination.
CATALOG_LIST_URLS = (
    BASE + "catalog/wine",
    BASE + "catalog/vinuri-spumante",
)
MAX_PAGES = 120  # 21 * 120

# Avoid SSL verify failure on some systems
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    """Request wine.md with a safe ASCII URL (paths may contain „ " etc.)."""
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(urllib.parse.unquote(parts.path), safe="/%:@&=+$,;?#[]!'()*")
    safe = urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))
    req = urllib.request.Request(safe, headers={"User-Agent": "Mozilla/5.0 (compatible; WineCatalog/1.0)"})
    with urllib.request.urlopen(req, timeout=25, context=_ctx) as r:
        return r.read().decode("utf-8", errors="replace")


def normalize_catalog_path(path):
    """Collapse wine.md's occasional catalog/catalog/... paths to catalog/...."""
    p = (path or "").strip().replace("\\", "/").lstrip("/")
    while p.lower().startswith("catalog/catalog/"):
        p = "catalog/" + p[len("catalog/catalog/") :]
    return p


def norm_product_url(url):
    if not url:
        return ""
    u = url.strip().rstrip("/").lower()
    while "/catalog/catalog/" in u:
        u = u.replace("/catalog/catalog/", "/catalog/")
    return u


def extract_products(html):
    products = []
    # Split by product blocks (each card is in a div.product or we match form with pagetitle)
    blocks = re.split(r'<div class="product">', html)
    for block in blocks[1:]:  # skip first (header)
        link_m = re.search(r'href="(catalog/[^"]+)"[^>]*class="product-image', block)
        title_m = re.search(r'class="product-title">([^<]+)</a>', block)
        img_m = re.search(r'src="(/assets/images/products/\d+/[^"]+)"', block)
        price_m = re.search(r'name="price"\s+value="(\d+)"', block)
        if not link_m:
            continue
        path = normalize_catalog_path(link_m.group(1).strip())
        if path.endswith("/") or "/brand/" in path or "collections" in path:
            continue
        slug = path.split("/")[-1] if "/" in path else path
        name = title_m.group(1).strip() if title_m else slug.replace("-", " ").title()
        low = name.lower()
        if slug == "transport" and "achitare" in low:
            continue
        if "achitarea transport" in low or "achitare transport" in low:
            continue
        image_path = img_m.group(1) if img_m else ""
        price = int(price_m.group(1)) if price_m else 0
        if not image_path or "woodbag-logo" in image_path:
            continue
        image_url = (BASE.rstrip("/") + image_path) if image_path.startswith("/") else BASE + image_path
        image_url_full = image_url.replace("/small/", "/") if "/small/" in image_url else image_url
        products.append({
            "path": path,
            "slug": slug,
            "name": name,
            "imageUrl": image_url_full,
            "imageUrlSmall": image_url,
            "price": price,
            "link": path if path.startswith("catalog/") else "catalog/" + path,
        })
    return products

def path_to_type(path):
    path_lower = path.lower()
    if "vinuri-spumante" in path_lower or "spumante" in path_lower:
        return "sparkling"
    if "vinuri-rosii" in path_lower or "vinuri-roșii" in path_lower:
        return "red"
    if "vinuri-roze" in path_lower or "vinuri-roze" in path_lower:
        return "rose"
    if "vinuri-dulci" in path_lower:
        return "white"  # sweet often white
    if "vinuri-albe" in path_lower:
        return "white"
    if "vinuri-de-colectie" in path_lower:
        return "red"  # default
    return "white"

def infer_brand(name):
    # Heuristic: known multi-word brands, then first two title-case words
    known = [
        "Castel Mimi", "Château Purcari", "Château Vartely", "Crama Mircesti", "Domeniile Vorniceni",
        "Et Cetera", "Vera Winery", "Vinaria Din Vale", "Gogu Winery", "Asconi", "Fautor",
        "Cricova", "Radacini", "Divus", "Purcari", "Equinox", "Mezalimpe", "Timbrus",
        "Tomai", "Aurelius", "Domeniile Cuza", "Vinum", "Barza Alba", "Corten",
        "Gitana", "Apriori", "Bardar", "Bostavan", "Academia", "Crama", "Vinaria",
        "Gogu Instinct", "Carpe Diem", "Basavin Optimist", "Basavin Trei", "Radacini",
    ]
    for brand in known:
        if name.startswith(brand):
            return brand
    words = name.split()
    if len(words) >= 2 and words[0][0].isupper() and words[1][0].isupper():
        return words[0] + " " + words[1]
    if words:
        return words[0]
    return "Moldova"

def extract_volume_liters_and_vintage_year(html):
    """
    Parse wine.md product page HTML for:
      - volume in liters (e.g. "Volumul: 0.75 l")
      - production year in Romanian (e.g. "An: 2025")
    Returns (volumeLiters, vintageYear) as strings or (None, None).
    """
    # Strip tags to make regex matching more resilient.
    plain = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"&nbsp;|\u00a0", " ", plain)

    vol_m = re.search(r"Volumul\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*l\b", plain, flags=re.I)

    # Prefer the bullet-style "- An: 2025" match.
    vint_m = re.search(
        r"(?:^|\n)\s*-\s*An\s*:\s*(\d{4})\b",
        plain,
        flags=re.I | re.M,
    )
    if not vint_m:
        vint_m = re.search(r"\bAn\s*:\s*(\d{4})\b", plain, flags=re.I)

    volume_liters = vol_m.group(1).strip() if vol_m else None
    vintage_year = vint_m.group(1).strip() if vint_m else None
    return volume_liters, vintage_year


def _product_page_plain_text(html):
    plain = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"&nbsp;|\u00a0", " ", plain)
    return " ".join(plain.split())


def extract_taste_from_product_html(html):
    """Same rules as scripts/fetch_wine_md_taste.py (wine.md 'Gust:' field)."""
    plain = _product_page_plain_text(html)
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


def extract_grapes_from_product_html(html):
    """Same rules as scripts/fetch_wine_md_grapes.py (wine.md 'Struguri:' field)."""
    plain = _product_page_plain_text(html)
    m = re.search(
        r"Struguri\s*:\s*(.+?)(?:\s+(?:Gust|Culoare|An|Alcoolul|Volumul|Țara|Servind|Compatibilitate)\s*:|\s+Servind\b|\s+Compatibilitate\b|$)",
        plain,
        flags=re.I,
    )
    if not m:
        m = re.search(
            r"Soi(?:ul)?\s+strugurilor?\s*:\s*(.+?)(?:\s+(?:Gust|Culoare|An|Alcoolul|Volumul|Țara)\s*:|$)",
            plain,
            flags=re.I,
        )
    if not m:
        return None
    val = " ".join(m.group(1).split()).strip(" -;,.")
    if not val or len(val) > 120:
        return None
    return val


def load_existing_wine_data_js(path):
    """
    Parse wine-data.js into header lines, product lines (full text per row), footer lines,
    and a set of normalized productPageUrls.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    header_end = None
    for i, line in enumerate(lines):
        if "window.WINE_PRODUCTS" in line:
            header_end = i
            break
    if header_end is None:
        return None
    header = lines[: header_end + 1]
    j = header_end + 1
    product_lines = []
    while j < len(lines):
        stripped = lines[j].strip()
        if stripped == "];" or stripped.startswith("];"):
            break
        if lines[j].lstrip().startswith("{"):
            product_lines.append(lines[j])
        j += 1
    footer = lines[j:]
    urls = set()
    for pl in product_lines:
        m = re.search(r"productPageUrl:\s*'([^']*)'", pl)
        if m:
            urls.add(norm_product_url(m.group(1)))
    return {"header": header, "products": product_lines, "footer": footer, "urls": urls}


def js_escape_single(s):
    return (s or "").replace("\\", "\\\\").replace("'", "\\'")


def format_product_js_line(p, rating, review_count, first_seen_iso=None):
    """Single-line object matching existing wine-data.js shape (taste when parsed; awards optional)."""
    desc_esc = (p.get("description") or "").replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    region = p.get("region") or "Moldova"
    grape = p.get("grape") or "Blend"
    abv = p.get("abv") or 12
    volume_liters = p.get("volumeLiters") or "0.75"
    vintage = p.get("vintage") or ""
    img_full = js_escape_single(p["imageUrl"])
    img_small = js_escape_single(p.get("imageUrlSmall", p["imageUrl"]))
    desc = desc_esc[:200] if desc_esc else js_escape_single("Vin " + p["type"] + " – " + p["name"])[:200]
    taste_part = ""
    if p.get("taste"):
        taste_part = " taste: '%s'," % js_escape_single(str(p["taste"]).strip())
    seen_tail = ""
    if first_seen_iso:
        seen_tail = ", firstSeenAt: '%s'" % js_escape_single(first_seen_iso)
    return (
        "  { id: '%s', brand: '%s', name: '%s', type: '%s', imageUrl: '%s', imageUrlSmall: '%s', price: %d, rating: %.1f, reviewCount: %d, volumeLiters: '%s', vintage: '%s', region: '%s', grape: '%s',%s abv: %s, description: '%s', productPageUrl: '%s'%s }"
        % (
            js_escape_single(p["id"]),
            js_escape_single(p["brand"]),
            js_escape_single(p["name"]),
            p["type"],
            img_full,
            img_small,
            p["price"],
            rating,
            review_count,
            js_escape_single(volume_liters),
            js_escape_single(vintage),
            js_escape_single(region),
            js_escape_single(grape),
            taste_part,
            str(abv) if isinstance(abv, (int, float)) else abv,
            desc,
            js_escape_single(p["productPageUrl"]),
            seen_tail,
        )
    )


def crawl_wine_md_products():
    """Paginate all catalog feeds and return product dicts (deduped by productPageUrl)."""
    seen_urls = {}
    all_products = []
    for list_base in CATALOG_LIST_URLS:
        print("Listing feed: %s" % list_base, flush=True)
        for page in range(1, MAX_PAGES + 1):
            url = list_base + ("?page=%d" % page if page > 1 else "")
            print("  Page %d: %s" % (page, url), flush=True)
            try:
                html = fetch(url)
            except Exception as e:
                print("Error:", e, flush=True)
                break
            products = extract_products(html)
            if not products:
                print("  No products on page %d, next feed." % page, flush=True)
                break
            for p in products:
                p["type"] = path_to_type(p["path"])
                p["brand"] = infer_brand(p["name"])
                p["id"] = re.sub(r"[,/]", "-", p["slug"]).replace(" ", "-")
                raw_url = BASE.rstrip("/") + "/" + p["link"].lstrip("/")
                while "/catalog/catalog/" in raw_url:
                    raw_url = raw_url.replace("/catalog/catalog/", "/catalog/")
                p["productPageUrl"] = raw_url
                nu = norm_product_url(raw_url)
                if nu in seen_urls:
                    continue
                seen_urls[nu] = True
                all_products.append(p)
            time.sleep(0.35)
    return all_products


def enrich_vintage_volume(products, vintage_limit, vintage_delay):
    for i, p in enumerate(products):
        if vintage_limit and i >= vintage_limit:
            break
        url = p.get("productPageUrl")
        if not url:
            continue
        try:
            html = fetch(url)
            volume_liters, vintage_year = extract_volume_liters_and_vintage_year(html)
            if volume_liters:
                p["volumeLiters"] = volume_liters
            if vintage_year:
                p["vintage"] = vintage_year
            taste = extract_taste_from_product_html(html)
            if taste:
                p["taste"] = taste
            grapes = extract_grapes_from_product_html(html)
            if grapes:
                p["grape"] = grapes
        except Exception as e:
            print("Warning: vintage parse failed for:", url, "error:", e, flush=True)
        time.sleep(vintage_delay)


def main():
    parser = argparse.ArgumentParser(description="Scrape wine.md catalog into wine-data.js")
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Regenerate the entire WINE_PRODUCTS array (drops manual enrichments in wine-data.js).",
    )
    args = parser.parse_args()

    out_path = os.path.join(os.path.dirname(__file__), "..", "wine-data.js")
    merge = not args.full_rebuild and os.path.isfile(out_path)
    existing = load_existing_wine_data_js(out_path) if merge else None
    if merge and not existing:
        merge = False

    all_products = crawl_wine_md_products()
    print("Total scraped from wine.md: %d" % len(all_products), flush=True)

    vintage_limit = int(os.environ.get("VINTAGE_LIMIT", "0") or "0")
    vintage_delay = float(os.environ.get("VINTAGE_DELAY", "0.35") or "0.35")

    if merge and existing:
        existing_urls = existing["urls"]
        new_products = [
            p for p in all_products if norm_product_url(p["productPageUrl"]) not in existing_urls
        ]
        print("Existing in wine-data.js: %d URLs; new to add: %d" % (len(existing_urls), len(new_products)), flush=True)
        enrich_vintage_volume(new_products, vintage_limit, vintage_delay)
        product_lines = list(existing["products"])
        base_idx = len(product_lines)
        new_lines = []
        merge_date_iso = date.today().isoformat()
        for i, p in enumerate(new_products):
            rating = 4.0 + ((base_idx + i) % 5) * 0.1
            review_count = 10 + ((base_idx + i) % 50)
            new_lines.append(format_product_js_line(p, rating, review_count, merge_date_iso))
        if new_lines:
            if product_lines:
                last = product_lines[-1].rstrip()
                if not last.endswith(","):
                    product_lines[-1] = last + ","
            for k, line in enumerate(new_lines):
                is_last = k == len(new_lines) - 1
                s = line.rstrip().rstrip(",")
                product_lines.append(s + ("" if is_last else ","))
        lines = existing["header"] + product_lines + existing["footer"]
        total_count = len(product_lines)
    else:
        enrich_vintage_volume(all_products, vintage_limit, vintage_delay)
        lines = [
            "// Full catalog from wine.md – all brands and products with images from wine.md. Generated by scripts/scrape_wine_md.py",
            "window.WINE_PRODUCTS = [",
        ]
        for i, p in enumerate(all_products):
            rating = 4.0 + (i % 5) * 0.1
            review_count = 10 + (i % 50)
            obj = format_product_js_line(p, rating, review_count)
            lines.append(obj + ("," if i < len(all_products) - 1 else ""))
        lines.append("];")
        lines.append("")
        lines.append("// wine.md image URLs are kept; no brokenHosts replacement for wine.md.")
        total_count = len(all_products)

    if merge and existing:
        # Preserve original footer comment block if missing
        if not any("// wine.md image" in x for x in existing["footer"]):
            lines.append("")
            lines.append("// wine.md image URLs are kept; no brokenHosts replacement for wine.md.")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        if not lines[-1].endswith("\n"):
            f.write("\n")
    print("Wrote %s with %d product rows." % (out_path, total_count), flush=True)


if __name__ == "__main__":
    main()
