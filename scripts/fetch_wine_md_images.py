#!/usr/bin/env python3
"""
Fetch product image URLs from wine.md product pages for white and sparkling products,
then update wine-data.js with the correct imageUrl and imageUrlSmall.
Only updates products that have productPageUrl to wine.md (actual wine products).
"""
import urllib.request
import urllib.error
import re
import time
import os
import ssl

BASE = "https://wine.md/"
WINE_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "wine-data.js")
# Set to 0 to process all; set to e.g. 40 for a quick test
LIMIT = 0
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; WineCatalog/1.0)"})
    with urllib.request.urlopen(req, timeout=25, context=_ctx) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_image_from_product_page(html, product_url):
    """Extract main product image URL from wine.md product page HTML."""
    # 1. og:image (often full URL)
    m = re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
    if m:
        url = m.group(1).strip().replace("//assets/", "/assets/").replace("https:/assets", "https://wine.md/assets")
        if "wine.md" in url and "/assets/images/products/" in url:
            return url
    m = re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html)
    if m:
        url = m.group(1).strip().replace("//assets/", "/assets/").replace("https:/assets", "https://wine.md/assets")
        if "wine.md" in url and "/assets/images/products/" in url:
            return url
    # 2. First img src or data-src with /assets/images/products/NUM/
    for pattern in [
        r'src=["\'](https?://wine\.md/assets/images/products/\d+/[^"\']+)["\']',
        r'src=["\'](/assets/images/products/\d+/[^"\']+)["\']',
        r'data-src=["\'](https?://wine\.md/assets/images/products/\d+/[^"\']+)["\']',
        r'data-src=["\'](/assets/images/products/\d+/[^"\']+)["\']',
    ]:
        m = re.search(pattern, html)
        if m:
            url = m.group(1).strip()
            if url.startswith("/"):
                url = BASE.rstrip("/") + url
            if "woodbag-logo" in url or "placeholder" in url.lower():
                continue
            return url
    return None


def normalize_image_urls(img_url):
    """Return (full_url, small_url). wine.md uses /small/ for thumbnails."""
    if not img_url or "wine.md" not in img_url:
        return (img_url, img_url)
    full = img_url.replace("//assets/", "/assets/").replace("https:/assets", "https://wine.md/assets")
    full = full.replace("/small/", "/") if "/small/" in full else full
    # small = insert small/ before filename (after product id)
    if "/small/" in full:
        small = full
    else:
        parts = full.split("/")
        for i, p in enumerate(parts):
            if p.isdigit() and i + 1 < len(parts):
                small = "/".join(parts[: i + 1] + ["small"] + parts[i + 1 :])
                break
        else:
            small = full
    return (full, small)


def is_bottle_product(product_page_url):
    """Exclude accessories, spirits, chocolates, gifts."""
    u = (product_page_url or "").lower()
    if "/accesorii/" in u or "/spirtoase/" in u or "/produse-gourmet/" in u:
        return False
    if "/gifts/" in u or "/suvenire/" in u or "vacuvin" in u:
        return False
    return True


def parse_wine_data_products(content):
    """Parse wine-data.js and yield (line, product_id, type, product_page_url, current_image_url, current_image_small)."""
    for line in content.split("\n"):
        if "type: 'white'" not in line:
            continue
        if "productPageUrl:" not in line or "wine.md" not in line:
            continue
        id_m = re.search(r"id:\s*['\"]([^'\"]+)['\"]", line)
        type_m = re.search(r"type:\s*['\"](\w+)['\"]", line)
        img_m = re.search(r"imageUrl:\s*['\"]([^'\"]*)['\"]", line)
        small_m = re.search(r"imageUrlSmall:\s*['\"]([^'\"]*)['\"]", line)
        url_m = re.search(r"productPageUrl:\s*['\"]([^'\"]*)['\"]", line)
        if not all([id_m, type_m, img_m, small_m, url_m]):
            continue
        pid, ptype, img, small, purl = (
            id_m.group(1),
            type_m.group(1),
            img_m.group(1),
            small_m.group(1),
            url_m.group(1),
        )
        if ptype != "white":
            continue
        if not is_bottle_product(purl):
            continue
        yield (line, pid, ptype, purl, img, small)


def main():
    with open(WINE_DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    products = list(parse_wine_data_products(content))
    if LIMIT:
        products = products[:LIMIT]
        print("Found %d white wine products (limited to %d)." % (len(products), LIMIT))
    else:
        print("Found %d white wine products with wine.md URLs to check." % len(products))

    updates = {}  # product_id -> (imageUrl, imageUrlSmall)
    safe_print = lambda s: print(s.encode("utf-8", errors="replace").decode("ascii"), end="", flush=True)
    for i, (line, pid, ptype, purl, old_img, old_small) in enumerate(products):
        try:
            safe_print("[%d/%d] Fetching ... " % (i + 1, len(products)))
        except Exception:
            print("[%d/%d] ... " % (i + 1, len(products)), end="", flush=True)
        try:
            html = fetch(purl)
            img_url = extract_image_from_product_page(html, purl)
            if img_url:
                full, small = normalize_image_urls(img_url)
                updates[pid] = (full, small)
                if full != old_img or small != old_small:
                    print("UPDATE")
                else:
                    print("OK (synced)")
            else:
                print("NO IMAGE FOUND")
        except Exception as e:
            try:
                msg = str(e).encode("ascii", errors="replace").decode("ascii")
                print("ERROR: %s" % msg)
            except Exception:
                print("ERROR")
        time.sleep(0.4)

    if not updates:
        print("No image URL updates needed.")
        return

    # Replace in content: for each line that has an updated product id, replace imageUrl and imageUrlSmall
    new_lines = []
    for line in content.split("\n"):
        for pid, (new_img, new_small) in updates.items():
            if ("id: '%s'" % pid) in line or ('id: "%s"' % pid) in line:
                # Escape single quotes in URLs for JS
                new_img_esc = new_img.replace("\\", "\\\\").replace("'", "\\'")
                new_small_esc = new_small.replace("\\", "\\\\").replace("'", "\\'")
                line = re.sub(
                    r"imageUrl:\s*['\"][^'\"]*['\"],\s*imageUrlSmall:\s*['\"][^'\"]*['\"]",
                    "imageUrl: '%s', imageUrlSmall: '%s'" % (new_img_esc, new_small_esc),
                    line,
                    count=1,
                )
                break
        new_lines.append(line)

    with open(WINE_DATA_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    print("Updated wine-data.js with %d new image URLs." % len(updates))


if __name__ == "__main__":
    main()
