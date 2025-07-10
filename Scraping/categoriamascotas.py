import time
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Configuración del navegador
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=chrome_options)

# Diccionario con las categorías y sus URLs
enlaces_categorias = {
    "Comederos y Bebederos": "https://listado.mercadolibre.com.co/animales-mascotas/gatos/comederos-bebederos",
    "Alimento, Premios y Suplemento": "https://listado.mercadolibre.com.co/animales-mascotas/gatos/alimento-premios-suplemento",
    "Estética y Cuidado": "https://listado.mercadolibre.com.co/animales-mascotas/gatos/estetica-cuidado",
    "Viaje y Paseo": "https://listado.mercadolibre.com.co/animales-mascotas/gatos/viaje-paseo",
    "Camas y Casas": "https://listado.mercadolibre.com.co/animales-mascotas/gatos/camas-casas"
}

paginas = 10
productos = []

# Iterar por cada categoría
for nombre_categoria, url_base in enlaces_categorias.items():
    print(f"\n🔎 Procesando categoría: {nombre_categoria}")
    for i in range(paginas):
        offset = i * 50
        url = f"{url_base}_Desde_{offset}" if i > 0 else url_base
        driver.get(url)
        time.sleep(4)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.select("div.ui-search-result__wrapper")

        for item in items:
            try:
                calificacion = item.select_one("span.poly-reviews__rating").get_text(strip=True)
                num_calificaciones = item.select_one("span.poly-reviews__total").get_text(strip=True).strip("()")
            except:
                continue  # Saltar productos sin calificación

            try:
                precio = item.select_one("div.poly-price__current span.andes-money-amount__fraction").get_text(strip=True)
            except:
                precio = ""

            try:
                precio_anterior = item.select_one("s span.andes-money-amount__fraction").get_text(strip=True)
            except:
                precio_anterior = ""

            try:
                descuento = item.select_one("span.andes-money-amount__discount").get_text(strip=True)
            except:
                descuento = ""

            productos.append([
                nombre_categoria, precio, precio_anterior, descuento,
                calificacion, num_calificaciones
            ])
        print(f"  Página {i+1} lista. Productos acumulados: {len(productos)}")

# Guardar en CSV
with open("productos_gatos_por_categoria.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Categoría", "Precio actual", "Precio anterior",
        "Descuento", "Calificación", "N° Calificaciones"
    ])
    writer.writerows(productos)

print("\n✅ Scraping finalizado. Total productos con calificación:", len(productos))
driver.quit()
