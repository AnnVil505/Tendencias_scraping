import time
import csv
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Argumentos de línea de comandos
parser = argparse.ArgumentParser(description='Extraer datos de productos de AliExpress')
parser.add_argument('url', help='URL de la página de AliExpress a scrapear')
parser.add_argument('--output', default='aliexpress_products.csv', help='Archivo CSV de salida')
args = parser.parse_args()

target_url = args.url
output_file = args.output

# Configuración de Chrome con Selenium
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--disable-software-rasterizer')

# Inicializar WebDriver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 15)


def fetch_products(url):
    driver.get(url)
    # Esperar a que cargue el contenedor de productos
    container = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'div[data-spm="prodcutlist"]')
    ))

    # Scroll interno del contenedor para cargar todos los productos
    prev_count = 0
    while True:
        cards = container.find_elements(By.CSS_SELECTOR, 'a._3mPKP')
        count_before = len(cards)

        # Scroll dentro del contenedor
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight;",
            container
        )

        # Esperar hasta que aparezca al menos una tarjeta más (o timeout 10 s)
        try:
            wait.until(lambda d: len(container.find_elements(
                By.CSS_SELECTOR, 'a._3mPKP'
            )) > count_before, timeout=10)
        except:
            break

        # Si el número no aumentó, terminamos
        if len(container.find_elements(By.CSS_SELECTOR, 'a._3mPKP')) == count_before:
            break

    # Parsear HTML de la página completa
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    products = []

    # Extraer datos de cada producto
    for a in soup.select('a._3mPKP'):
        name = a.select_one('h3.yB6en').get_text(strip=True) if a.select_one('h3.yB6en') else ''
        price = a.select_one('div._3Mpbo').get_text(strip=True) if a.select_one('div._3Mpbo') else ''
        discount = a.select_one('span.W__kt').get_text(strip=True) if a.select_one('span.W__kt') else ''
        sold = a.select_one('span.DUuR2').get_text(strip=True) if a.select_one('span.DUuR2') else ''
        rating = a.select_one('span._2L2Tc').get_text(strip=True) if a.select_one('span._2L2Tc') else ''
        products.append({
            'name': name,
            'price': price,
            'discount': discount,
            'sold': sold,
            'rating': rating
        })

    return products


if __name__ == '__main__':
    data = fetch_products(target_url)

    # Guardar resultados en CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['name', 'price', 'discount', 'sold', 'rating'])
        writer.writeheader()
        for item in data:
            writer.writerow(item)

    print(f"Scraped {len(data)} products. Datos guardados en {output_file}")
