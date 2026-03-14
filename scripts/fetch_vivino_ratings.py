#!/usr/bin/env python3
"""
Fetch wine ratings from Vivino's official website and generate
wine-vivino-ratings.js so the site displays actual Vivino ratings.

Uses the Vivino search page (same as vivino.com/search/wines?q=...) so each
product is matched to its real Vivino listing. Run from repo root:
  python scripts/fetch_vivino_ratings.py

To test with only the first N products: set VIVINO_LIMIT (e.g. VIVINO_LIMIT=50).
Full run (~925 products) takes about 20 min due to rate limiting.

Requires: requests (pip install requests)
"""
import re
import json
import time
import os
import urllib.parse

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    raise SystemExit(1)

VIVINO_ORIGIN = "https://www.vivino.com"
VIVINO_SEARCH_URL = VIVINO_ORIGIN + "/search/wines"
EXPLORE_URL = VIVINO_ORIGIN + "/api/explore/explore"
WINE_DATA_JS = "wine-data.js"
OUTPUT_JS = "wine-vivino-ratings.js"
SEARCH_DELAY = 1.2  # seconds between search requests to avoid rate limit

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": VIVINO_ORIGIN + "/",
    })
    try:
        s.get(VIVINO_ORIGIN, timeout=15)
    except Exception as e:
        print("Warning: could not get Vivino session:", e)
    return s


def fetch_vivino_search(session, query):
    """
    Fetch Vivino search page for a wine name and parse the first result's
    rating from the embedded JSON. Returns None or {"name", "rating", "reviewCount"}.
    """
    url = VIVINO_SEARCH_URL + "?q=" + urllib.parse.quote(query)
    try:
        r = session.get(url, timeout=25)
        if r.status_code != 200:
            return None
        text = r.text
    except requests.RequestException:
        return None
    # Find "matches" array in the page (HTML-escaped)
    start = text.find('"matches"')
    if start == -1:
        start = text.find("matches")
    if start == -1:
        return None
    bracket = text.find("[", start)
    if bracket == -1:
        return None
    depth = 0
    end = bracket
    for i in range(bracket, min(bracket + 150000, len(text))):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    chunk = text[bracket:end]
    chunk = chunk.replace("&quot;", '"').replace("&#39;", "'")
    # First vintage block: "vintage":{..."name":"...","statistics":{..."ratings_average":X,"ratings_count":Y}}
    name_m = re.search(r'"name"\s*:\s*"([^"]+)"', chunk)
    ratings = re.findall(r'"ratings_average"\s*:\s*([\d.]+)', chunk)
    counts = re.findall(r'"ratings_count"\s*:\s*(\d+)', chunk)
    if not name_m or not ratings or not counts:
        return None
    name = name_m.group(1)
    rating_val = float(ratings[0])
    count_val = int(counts[0])
    return {"name": name, "rating": round(rating_val, 1), "reviewCount": count_val}


def get_cache_key(session):
    """Extract vivinoCacheKey from the main page (required for countries API)."""
    try:
        r = session.get(VIVINO_ORIGIN, timeout=15)
        r.raise_for_status()
        m = re.search(r"var vivinoCacheKey\s*=\s*['\"]?([^'\"\s;]+)", r.text)
        if m:
            return m.group(1).strip()
    except Exception as e:
        print("Warning: could not get cache key:", e)
    return None


def get_countries(session, cache_key):
    """Fetch valid country/currency list from Vivino API."""
    try:
        r = session.get(
            VIVINO_ORIGIN + "/api/countries",
            params={"cache_key": cache_key} if cache_key else {},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("countries") or []
    except Exception as e:
        print("Warning: could not get countries:", e)
    return []


def find_country_code(countries, preferred=["MD", "RO", "US"]):
    """Return (country_code, currency_code) for explore API."""
    by_code = {c.get("code", "").upper(): c for c in countries if c.get("code")}
    for code in preferred:
        c = by_code.get(code.upper())
        if c:
            cur = c.get("currency") or {}
            curr_code = cur.get("code") or "USD"
            return code.upper(), curr_code
    if countries:
        c = countries[0]
        return (c.get("code") or "US").upper(), (c.get("currency") or {}).get("code") or "USD"
    return "US", "USD"


def fetch_explore(session, params):
    try:
        r = session.get(EXPLORE_URL, params=params, timeout=20)
        if r.status_code != 200:
            print("Request error:", r.status_code, r.text[:200] if r.text else "")
            return None
        return r.json()
    except requests.RequestException as e:
        print("Request error:", e)
        return None


def normalize_name(s):
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def name_tokens(s):
    return set(re.sub(r"[^\w\s]", " ", normalize_name(s)).split()) - {""}


def match_score(our_name, vivino_name, brand=""):
    """
    Only return a score if this Vivino wine is likely the same product.
    Require brand to appear in Vivino name and strong token overlap so we
    don't match e.g. 'Vera Winery Sauvignon Blanc' to a different Sauvignon Blanc.
    """
    our_n = normalize_name(our_name)
    viv_n = normalize_name(vivino_name)
    if our_n == viv_n:
        return 100
    if our_n in viv_n or viv_n in our_n:
        return 90
    our_t = name_tokens(our_name)
    viv_t = name_tokens(vivino_name)
    if not our_t:
        return 0
    # Brand must appear in Vivino name (avoid wrong producer)
    brand_tokens = name_tokens(brand) if brand else set()
    if brand_tokens and not (brand_tokens & viv_t):
        return 0
    # At least 60% of our product name tokens must appear in Vivino name
    overlap_ratio = len(our_t & viv_t) / len(our_t)
    if overlap_ratio < 0.6:
        return 0
    return 50 + overlap_ratio * 40  # 50–90 range


def extract_products_from_js(path):
    """Parse wine-data.js and return list of {id, brand, name}."""
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    products = []
    # Match each product object: { id: '...', brand: '...', name: '...', ... }
    block = re.search(r"window\.WINE_PRODUCTS\s*=\s*\[(.*)\];", content, re.DOTALL)
    if not block:
        return products
    inner = block.group(1)
    # Each product is one line: { id: '...', brand: '...', name: '...', ... }
    for line in inner.split("\n"):
        line = line.strip().rstrip(",").strip()
        if not line.startswith("{"):
            continue
        id_m = re.search(r"id:\s*['\"]([^'\"]+)['\"]", line)
        brand_m = re.search(r"brand:\s*['\"]((?:[^'\"]|\\.)*)['\"]", line)
        name_m = re.search(r"name:\s*['\"]((?:[^'\\]|\\.)*)['\"]", line)
        if id_m and brand_m and name_m:
            name = name_m.group(1).replace("\\'", "'").replace('\\"', '"')
            products.append({
                "id": id_m.group(1),
                "brand": brand_m.group(1).replace("\\'", "'"),
                "name": name,
            })
    return products


def fetch_all_country_wines(session, country_code, currency_code):
    """Fetch explore results for a country."""
    all_records = []
    page = 1
    per_page = 50  # API max is 50
    # Vivino explore API (official website). Use US/USD for broad catalog; price_range required.
    params = {
        "country_code": country_code,
        "currency_code": currency_code,
        "min_rating": "1",
        "order_by": "ratings_count",
        "order": "desc",
        "page": str(page),
        "per_page": str(per_page),
        "price_range_min": "5",
        "price_range_max": "1000",
    }
    total_matched = None
    while True:
        params["page"] = str(page)
        data = fetch_explore(session, params)
        if not data:
            break
        try:
            ev = data.get("explore_vintage") or {}
            records = ev.get("records") or ev.get("matches") or []
            if total_matched is None:
                total_matched = ev.get("records_matched") or 0
            all_records.extend(records)
            if len(records) < per_page or len(all_records) >= total_matched:
                break
            page += 1
            time.sleep(0.4)
        except Exception as e:
            print("Parse error:", e)
            break
    return all_records


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    wine_data_path = os.path.join(repo_root, WINE_DATA_JS)
    output_path = os.path.join(repo_root, OUTPUT_JS)

    products = extract_products_from_js(wine_data_path)
    if not products:
        print("No products found in", wine_data_path)
        return

    print("Found", len(products), "products in wine-data.js")

    session = get_session()
    ratings_by_id = {}

    # Primary: search Vivino by name for each product (correct wine each time)
    print("Searching Vivino by product name (this may take a while)...")
    limit = None
    if os.environ.get("VIVINO_LIMIT"):
        try:
            limit = int(os.environ.get("VIVINO_LIMIT"))
        except ValueError:
            pass
    to_fetch = products[:limit] if limit else products
    for i, p in enumerate(to_fetch):
        query = ((p.get("brand") or "") + " " + (p.get("name") or "")).strip()
        if not query:
            continue
        result = fetch_vivino_search(session, query)
        if result:
            brand = (p.get("brand") or "").strip()
            # Only accept if the search result is clearly the same wine (brand in name)
            if brand and brand.lower() not in result["name"].lower():
                brand_first = (brand.split()[0] or "").lower()
                if brand_first and brand_first not in result["name"].lower():
                    result = None
            if result:
                # Store rating only when Vivino shows it (avoid wrong 0 from BelowThreshold)
                entry = {"reviewCount": result["reviewCount"]}
                if result["rating"] > 0:
                    entry["rating"] = result["rating"]
                ratings_by_id[p["id"]] = entry
        if (i + 1) % 50 == 0:
            print("  %d/%d searched, %d with ratings" % (i + 1, len(to_fetch), len(ratings_by_id)))
        time.sleep(SEARCH_DELAY)

    print("Matched", len(ratings_by_id), "products to Vivino ratings (from search)")

    # Generate wine-vivino-ratings.js
    lines = [
        "// Vivino ratings from official website API. Generated by scripts/fetch_vivino_ratings.py",
        "window.WINE_VIVINO_RATINGS = " + json.dumps(ratings_by_id, indent=2) + ";",
        "(function(){ var W = window.WINE_PRODUCTS; var V = window.WINE_VIVINO_RATINGS; if (W && V) { for (var i = 0; i < W.length; i++) { var p = W[i]; var v = V[p.id]; if (v) { if (v.rating != null) p.vivinoRating = v.rating; if (v.reviewCount != null) p.vivinoReviewCount = v.reviewCount; } } } })();",
    ]
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Wrote", output_path)


if __name__ == "__main__":
    main()
