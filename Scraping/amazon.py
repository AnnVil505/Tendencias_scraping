import csv
import argparse
import time
import re
import unicodedata
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Argumentos
parser = argparse.ArgumentParser(description='Scrapea resultados de búsqueda en Amazon')
parser.add_argument('url', help='URL de búsqueda de Amazon')
parser.add_argument('--output', default='amazon_products.csv', help='Archivo CSV de salida')
parser.add_argument('--pages', type=int, default=1, help='Número de páginas a scrapear')
args = parser.parse_args()

base_url = args.url
output_file = args.output
num_pages = args.pages

# Configura Selenium
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--disable-software-rasterizer')

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 15)


def clean_text(text):
    t = unicodedata.normalize('NFKD', text)
    return t.replace('\xa0', ' ').strip()


def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    for item in soup.select('div[data-component-type="s-search-result"]'):
        asin = item.get('data-asin', '')

        # Título con fallback
        title = ''
        tag = item.select_one('h2 a span') or item.select_one('h2 span')
        if tag:
            title = clean_text(tag.get_text())

        # Precio
        price = ''
        pw = item.select_one('span.a-price-whole')
        pf = item.select_one('span.a-price-fraction')
        if pw and pf:
            whole = re.sub(r'[^0-9]', '', pw.get_text())
            frac = re.sub(r'[^0-9]', '', pf.get_text())
            if whole and frac:
                price = f"{whole}.{frac}"

        # Rating
        rating = ''
        rt = item.select_one('i.a-icon-star-small span.a-icon-alt')
        if rt:
            rating = rt.get_text().split()[0]

        # Reviews count
        reviews = ''
        rv = item.select_one('span.a-size-base.s-underline-text')
        if rv:
            reviews = re.sub(r'[^0-9,]', '', rv.get_text())

        # Sales info
        sales = ''
        sl = item.find('span', string=re.compile(r'comprad', re.IGNORECASE))
        if sl:
            sales = clean_text(sl.get_text())

        products.append({
            'asin': asin,
            'title': title,
            'price': price,
            'rating': rating,
            'reviews': reviews,
            'sales': sales
        })
    return products


if __name__ == '__main__':
    all_products = []
    for page in range(1, num_pages + 1):
        url = f"{base_url}&page={page}"
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')))
        time.sleep(2)
        all_products.extend(parse_page(driver.page_source))

    # Guardar CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['asin','title','price','rating','reviews','sales'])
        writer.writeheader()
        for prod in all_products:
            writer.writerow(prod)

    print(f"Scraped {len(all_products)} productos. Guardados en {output_file}")
