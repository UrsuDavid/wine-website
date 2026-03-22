#!/usr/bin/env python3
"""
Re-fetch main product images from wine.md for URLs listed in wine_md_low_res_report.txt
(low-resolution + broken sections), then update imageUrl / imageUrlSmall in wine-data.js.

Run from project root:
  python scripts/refresh_bad_wine_md_images.py
"""
from __future__ import annotations

import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINE_DATA_PATH = os.path.join(_ROOT, "wine-data.js")
REPORT_PATH = os.path.join(_ROOT, "scripts", "wine_md_low_res_report.txt")
BASE = "https://wine.md/"
DELAY_SEC = 0.35

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def iri_to_uri(iri: str) -> str:
    """Percent-encode path so urllib can request URLs with Unicode (e.g. „ … », ș, ’)."""
    p = urllib.parse.urlsplit(iri)
    path = urllib.parse.quote(p.path, safe="/%")
    q = (
        urllib.parse.quote(p.query, safe="=&%-._~!$'()*+,;:@/?")
        if p.query
        else ""
    )
    return urllib.parse.urlunsplit((p.scheme, p.netloc, path, q, p.fragment))


def fetch(url: str) -> str:
    uri = iri_to_uri(url)
    req = urllib.request.Request(
        uri, headers={"User-Agent": "Mozilla/5.0 (compatible; WineCatalog/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=30, context=_ctx) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_image_from_product_page(html: str) -> str | None:
    m = re.search(
        r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html
    )
    if m:
        url = m.group(1).strip().replace("//assets/", "/assets/").replace(
            "https:/assets", "https://wine.md/assets"
        )
        if "wine.md" in url and "/assets/images/products/" in url:
            return url
    m = re.search(
        r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html
    )
    if m:
        url = m.group(1).strip().replace("//assets/", "/assets/").replace(
            "https:/assets", "https://wine.md/assets"
        )
        if "wine.md" in url and "/assets/images/products/" in url:
            return url
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


def normalize_image_urls(img_url: str) -> tuple[str, str]:
    if not img_url or "wine.md" not in img_url:
        return (img_url, img_url)
    full = img_url.replace("//assets/", "/assets/").replace(
        "https:/assets", "https://wine.md/assets"
    )
    full = full.replace("/small/", "/") if "/small/" in full else full
    if "/small/" in full:
        small = full
    else:
        parts = full.split("/")
        small = full
        for i, p in enumerate(parts):
            if p.isdigit() and i + 1 < len(parts):
                small = "/".join(parts[: i + 1] + ["small"] + parts[i + 1 :])
                break
    return (full, small)


def parse_bad_page_urls_from_report(text: str) -> list[str]:
    out: list[str] = []
    mode: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line == "=== Low-resolution (product page URL) ===":
            mode = "collect"
            continue
        if line == "=== Broken / missing image (product page URL) ===":
            mode = "collect"
            continue
        if line.startswith("===") and "Details" in line:
            mode = None
            continue
        if mode == "collect" and line.startswith("https://wine.md/"):
            out.append(line)
    # dedupe, preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not os.path.isfile(REPORT_PATH):
        print("Missing %s — run scripts/list_low_res_wine_md_images.py first." % REPORT_PATH)
        return 1

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report = f.read()
    targets = set(parse_bad_page_urls_from_report(report))
    print("Loaded %d unique product page URLs from report." % len(targets), flush=True)

    with open(WINE_DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    to_refresh: list[tuple[str, str, str, str]] = []
    for line in content.split("\n"):
        if "productPageUrl:" not in line or "wine.md" not in line:
            continue
        url_m = re.search(r"productPageUrl:\s*['\"]([^'\"]+)['\"]", line)
        id_m = re.search(r"id:\s*['\"]([^'\"]+)['\"]", line)
        img_m = re.search(r"imageUrl:\s*['\"]([^'\"]*)['\"]", line)
        small_m = re.search(r"imageUrlSmall:\s*['\"]([^'\"]*)['\"]", line)
        if not all([url_m, id_m, img_m, small_m]):
            continue
        purl = url_m.group(1)
        if purl not in targets:
            continue
        to_refresh.append(
            (id_m.group(1), purl, img_m.group(1), small_m.group(1))
        )

    print("Matched %d products in wine-data.js to refresh." % len(to_refresh), flush=True)

    # Key by productPageUrl so duplicate `id` values do not overwrite each other.
    updates: dict[str, tuple[str, str]] = {}
    missing_in_data = targets - {t[1] for t in to_refresh}
    if missing_in_data:
        print(
            "Note: %d report URLs have no matching productPageUrl in wine-data.js (skipped)."
            % len(missing_in_data),
            flush=True,
        )

    for i, (pid, purl, old_img, old_small) in enumerate(to_refresh):
        print("[%d/%d] %s ... " % (i + 1, len(to_refresh), pid[:50]), end="", flush=True)
        try:
            html = fetch(purl)
            img_url = extract_image_from_product_page(html)
            if not img_url:
                print("NO IMAGE", flush=True)
                continue
            full, small = normalize_image_urls(img_url)
            updates[purl] = (full, small)
            if full != old_img or small != old_small:
                print("UPDATE", flush=True)
            else:
                print("unchanged", flush=True)
        except Exception as e:
            print("ERR %s" % e, flush=True)
        time.sleep(DELAY_SEC)

    if not updates:
        print("No updates applied.")
        return 0

    new_lines = []
    for line in content.split("\n"):
        url_m = re.search(r"productPageUrl:\s*['\"]([^'\"]+)['\"]", line)
        if url_m and url_m.group(1) in updates:
            new_img, new_small = updates[url_m.group(1)]
            new_img_esc = new_img.replace("\\", "\\\\").replace("'", "\\'")
            new_small_esc = new_small.replace("\\", "\\\\").replace("'", "\\'")
            line = re.sub(
                r"imageUrl:\s*['\"][^'\"]*['\"],\s*imageUrlSmall:\s*['\"][^'\"]*['\"]",
                "imageUrl: '%s', imageUrlSmall: '%s'" % (new_img_esc, new_small_esc),
                line,
                count=1,
            )
        new_lines.append(line)

    with open(WINE_DATA_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    print("Updated wine-data.js for %d product pages." % len(updates), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
