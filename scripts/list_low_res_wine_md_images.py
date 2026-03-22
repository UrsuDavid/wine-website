#!/usr/bin/env python3
"""
Fetch product image URLs from wine.md (via imageUrl in wine-data.js) and list
products whose main image is below MIN_MAX_DIMENSION pixels on the longest side.

Uses only the stdlib (no Pillow) — reads PNG/JPEG/WebP headers.

Run from project root:
  python scripts/list_low_res_wine_md_images.py
"""
from __future__ import annotations

import os
import re
import struct
import ssl
import sys
import time
import urllib.request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINE_DATA_PATH = os.path.join(_ROOT, "wine-data.js")
REPORT_PATH = os.path.join(_ROOT, "scripts", "wine_md_low_res_report.txt")
MIN_MAX_DIMENSION = 800
DELAY_SEC = 0.35


def is_bottle_catalog_url(product_page_url: str) -> bool:
    """Same idea as fetch_wine_md_images.is_bottle_product — wine/sparkling only."""
    u = (product_page_url or "").lower()
    if "wine.md" not in u:
        return False
    if "/accesorii/" in u or "/spirtoase/" in u or "/produse-gourmet/" in u:
        return False
    if "/gifts/" in u or "/suvenire/" in u or "vacuvin" in u:
        return False
    return "/catalog/wine/" in u or "/catalog/vinuri-spumante/" in u

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; WineCatalog/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=30, context=_ctx) as r:
        return r.read()


def image_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) from image file header bytes."""
    if len(data) < 24:
        raise ValueError("too short")
    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", data[16:24])
        return (w, h)
    # JPEG
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 8:
            if data[i] != 0xFF:
                i += 1
                continue
            m = data[i + 1]
            if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                return (w, h)
            seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
            i += 2 + seg_len
        raise ValueError("JPEG SOF not found")
    # WebP: RIFF....WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8 ":
            if len(data) < 30:
                raise ValueError("webp vp8 short")
            w, h = struct.unpack("<HH", data[26:30])
            return (w & 0x3FFF, h & 0x3FFF)
        if chunk == b"VP8L":
            if len(data) < 25:
                raise ValueError("webp vp8l short")
            b = data[21:25]
            n = struct.unpack("<I", b)[0]
            w = (n & 0x3FFF) + 1
            h = ((n >> 14) & 0x3FFF) + 1
            return (w, h)
        if chunk == b"VP8X":
            if len(data) < 30:
                raise ValueError("webp vp8x short")
            w = 1 + (data[24] | (data[25] << 8) | (data[26] << 16))
            h = 1 + (data[27] | (data[28] << 8) | (data[29] << 16))
            return (w, h)
    raise ValueError("unsupported or unknown image format")


def parse_products(content: str) -> list[dict]:
    rows = []
    for line in content.split("\n"):
        if "productPageUrl:" not in line:
            continue
        url_m = re.search(
            r"productPageUrl:\s*['\"](https://wine\.md/[^'\"]+)['\"]", line
        )
        if not url_m:
            continue
        product_url = url_m.group(1)
        if not is_bottle_catalog_url(product_url):
            continue
        id_m = re.search(r"id:\s*['\"]([^'\"]+)['\"]", line)
        name_m = re.search(r"name:\s*['\"]([^'\"]+)['\"]", line)
        img_m = re.search(r"imageUrl:\s*['\"]([^'\"]+)['\"]", line)
        if not all([id_m, name_m, img_m]):
            continue
        rows.append(
            {
                "id": id_m.group(1),
                "name": name_m.group(1),
                "imageUrl": img_m.group(1),
                "productPageUrl": product_url,
            }
        )
    return rows


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    with open(WINE_DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    products = parse_products(content)
    low_res: list[tuple[str, str, str, int, int, str]] = []
    broken: list[tuple[str, str, str, str]] = []  # name, page, imageUrl, error

    print(
        "Checking %d wine.md bottle products (max side < %d px => low-res)\n"
        % (len(products), MIN_MAX_DIMENSION),
        flush=True,
    )

    for i, p in enumerate(products):
        url = p["imageUrl"]
        try:
            data = fetch_bytes(url)
            w, h = image_dimensions(data)
            mx = max(w, h)
            status = "OK" if mx >= MIN_MAX_DIMENSION else "LOW"
            print(
                "[%d/%d] %s %dx%d %s"
                % (i + 1, len(products), status, w, h, p["id"][:48]),
                flush=True,
            )
            if mx < MIN_MAX_DIMENSION:
                low_res.append(
                    (p["name"], p["productPageUrl"], url, w, h, p["id"])
                )
        except Exception as e:
            print(
                "[%d/%d] ERR %s (%s)"
                % (i + 1, len(products), p["id"][:48], e),
                flush=True,
            )
            broken.append((p["name"], p["productPageUrl"], url, str(e)))
        time.sleep(DELAY_SEC)

    report_lines = [
        "wine.md — bottle catalog only (/catalog/wine/, /catalog/vinuri-spumante/)",
        "Criterion: longest image side < %d px, or image fetch failed" % MIN_MAX_DIMENSION,
        "",
        "=== Low-resolution (product page URL) ===",
    ]
    for name, page, img, w, h, pid in low_res:
        report_lines.append(page)
    report_lines.extend(
        [
            "",
            "=== Broken / missing image (product page URL) ===",
        ]
    )
    for name, page, img, err in broken:
        report_lines.append(page)
    report_lines.extend(
        [
            "",
            "=== Details: low-res ===",
        ]
    )
    for name, page, img, w, h, pid in low_res:
        report_lines.append("%s | %dx%d" % (name, w, h))
        report_lines.append("  " + page)
        report_lines.append("  " + img)
        report_lines.append("")
    report_lines.extend(["=== Details: broken ===", ""])
    for name, page, img, err in broken:
        report_lines.append(name)
        report_lines.append("  " + page)
        report_lines.append("  " + img)
        report_lines.append("  " + err)
        report_lines.append("")

    report_lines.append(
        "Summary: low-res %d, broken %d, checked %d"
        % (len(low_res), len(broken), len(products))
    )
    report_text = "\n".join(report_lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    print("\n--- Low-res product pages ---\n", flush=True)
    for name, page, img, w, h, pid in low_res:
        print(page, flush=True)
    print("\n--- Broken image product pages ---\n", flush=True)
    for name, page, img, err in broken:
        print(page, flush=True)
    print(
        "\nWrote %s\nTotal low-res: %d, broken: %d / %d"
        % (REPORT_PATH, len(low_res), len(broken), len(products)),
        flush=True,
    )


if __name__ == "__main__":
    main()
