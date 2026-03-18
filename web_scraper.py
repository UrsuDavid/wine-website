import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin

BASE_URL = "https://books.toscrape.com/"
OUTPUT_FILE = "products.json"


def get_star_rating_value(rating_class):
    rating_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    match = re.search(r'star-rating\s(One|Two|Three|Four|Five)', rating_class)
    if match:
        star_word = match.group(1)
        return rating_map.get(star_word, 0)
    return 0


def scrape_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'lxml')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def fetch_product_description(product_url):
    """Fetch the product description from the product's individual page."""
    soup = scrape_page(product_url)
    if not soup:
        return "N/A"
    # Product description is in a <p> that follows the div#product_description heading
    desc_el = soup.select_one('#product_description + p')
    if desc_el:
        return desc_el.get_text(strip=True)
    return "N/A"


def parse_product(product_soup, base_url):
    product_data = {}
    try:
        # Product Link and Name
        title_element = product_soup.select_one('h3 a')
        if title_element:
            product_data['product_name'] = title_element.get_text(strip=True)
            product_data['product_link'] = urljoin(base_url, title_element['href'])
        else:
            product_data['product_name'] = "N/A"
            product_data['product_link'] = "N/A"

        # Product Price
        price_element = product_soup.select_one('.price_color')
        product_data['product_price'] = price_element.get_text(strip=True) if price_element else "N/A"

        # Product Rating
        rating_element = product_soup.select_one('p.star-rating')
        if rating_element and 'class' in rating_element.attrs:
            rating_classes = " ".join(rating_element['class'])
            product_data['product_rating'] = get_star_rating_value(rating_classes)
        else:
            product_data['product_rating'] = 0

        # Product Description: fetch from product detail page
        if product_data.get('product_link') and product_data['product_link'] != "N/A":
            product_data['product_description'] = fetch_product_description(product_data['product_link'])
        else:
            product_data['product_description'] = "N/A"

    except Exception as e:
        print(f"Error parsing product: {e}")
        print(f"Problematic product soup:\n{product_soup}")
    return product_data


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {filename}")


def main():
    all_products = []
    current_url = BASE_URL

    while current_url:
        print(f"Scraping {current_url}...")
        soup = scrape_page(current_url)
        if not soup:
            break

        products = soup.select('.product_pod')
        if not products:
            print("No products found on current page.")
            break

        for i, product in enumerate(products):
            product_data = parse_product(product, BASE_URL)
            if product_data:
                all_products.append(product_data)
                print(f"  [{len(all_products)}] {product_data.get('product_name', 'N/A')} (description fetched)")

        next_page_element = soup.select_one('.next a')
        if next_page_element:
            current_url = urljoin(BASE_URL, next_page_element['href'])
        else:
            current_url = None

    save_to_json(all_products, OUTPUT_FILE)
    print(f"Scraping complete. Total products: {len(all_products)}")


if __name__ == "__main__":
    main()
