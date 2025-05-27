import csv
import argparse
import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Argumentos de línea de comandos
parser = argparse.ArgumentParser(description='Scrapea "Más vendidos" de Mercado Libre por categorías')
parser.add_argument('url', help='URL de la sección "Más vendidos" (ruta principal)')
parser.add_argument('--output', default='ml_best_sellers.csv', help='Archivo CSV de salida')
parser.add_argument('--limit', '--pages', dest='limit', type=int, default=10,
                    help='Número máximo de productos a extraer por categoría (alias --pages)')
args = parser.parse_args()

base_url = args.url
output_file = args.output
max_per_category = args.limit

# Configurar Selenium
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=webdriver.ChromeOptions()
)
wait = WebDriverWait(driver, 15)

# Función para parsear productos de una categoría (HTML)
def parse_products(html, category):
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('div.poly-card--grid-card')
    results = []
    for idx, card in enumerate(cards[:max_per_category], start=1):
        label_tag = card.select_one('span.poly-component__highlight')
        label = label_tag.get_text(strip=True) if label_tag else ''
        title_tag = card.select_one('a.poly-component__title')
        title = title_tag.get_text(strip=True) if title_tag else ''
        rating_tag = card.select_one('span.poly-reviews__rating')
        rating = rating_tag.get_text(strip=True) if rating_tag else ''
        total_tag = card.select_one('span.poly-reviews__total')
        reviews_count = total_tag.get_text(strip=True).strip('()') if total_tag else ''
        price_tag = card.select_one('span.andes-money-amount__fraction')
        price = price_tag.get_text(strip=True) if price_tag else ''
        results.append({
            'category': category,
            'position': idx,
            'label': label,
            'title': title,
            'rating': rating,
            'reviews_count': reviews_count,
            'price': price
        })
    return results

# 1) Cargar página principal y extraer categorías
print(f"Obteniendo categorías desde {base_url}")
driver.get(base_url)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'aside.ui-search-sidebar')))
time.sleep(2)
soup_main = BeautifulSoup(driver.page_source, 'html.parser')
categories = []
for li in soup_main.select('aside.ui-search-sidebar ul li.ui-search-filter-container'):
    link = li.select_one('a.ui-search-link')
    if link:
        name = link.get_text(strip=True)
        href = urljoin(base_url, link['href'])
        categories.append((name, href))

# 2) Iterar cada categoría y extraer productos
all_data = []
for name, href in categories:
    print(f"Procesando categoría: {name}")
    driver.get(href)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.poly-card--grid-card')))
    time.sleep(2)
    all_data.extend(parse_products(driver.page_source, name))

# Guardar CSV
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['category', 'position', 'label', 'title', 'rating', 'reviews_count', 'price']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in all_data:
        writer.writerow(row)

print(f"Scrape completado. {len(all_data)} productos guardados en {output_file}")
