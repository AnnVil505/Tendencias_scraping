from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

# --- CONFIGURACIÓN ---
USUARIO = "d3orj005"  # Cambia por tu usuario de Instagram
CONTRASENA = "D4s5.V10o7"
PERFIL_OBJETIVO = "mercadolibre.co"
NUM_POSTS = 10  # Cantidad de publicaciones a extraer

# --- INICIALIZAR DRIVER ---
options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)
driver.get("https://www.instagram.com/accounts/login/")

# --- LOGIN ---
time.sleep(5)
inputs = driver.find_elements(By.TAG_NAME, "input")
inputs[0].send_keys(USUARIO)
inputs[1].send_keys(CONTRASENA)
inputs[1].send_keys(Keys.RETURN)

time.sleep(7)

# --- IR AL PERFIL ---
driver.get(f"https://www.instagram.com/{PERFIL_OBJETIVO}/")
time.sleep(5)

# --- EXTRAER SEGUIDORES ---
seguidores_texto = driver.find_element(By.XPATH, "//header//ul/li[2]/a/span").get_attribute("title")
seguidores = int(seguidores_texto.replace(".", "").replace(",", ""))
print(f"Seguidores: {seguidores}")

# --- BAJAR Y CLICKEAR POSTS ---
posts = driver.find_elements(By.XPATH, '//article//a')
links_posts = [elem.get_attribute("href") for elem in posts[:NUM_POSTS]]

datos = []

for link in links_posts:
    driver.get(link)
    time.sleep(3)

    try:
        tipo = driver.find_element(By.XPATH, '//article//video')
        tipo_post = "Video"
    except:
        try:
            carrusel = driver.find_element(By.XPATH, '//article//div[contains(@style, "transform")]')
            tipo_post = "Carrusel"
        except:
            tipo_post = "Imagen"

    try:
        likes = driver.find_element(By.XPATH, "//section/span/span").text.replace(",", "")
        likes = int(likes)
    except:
        likes = 0

    try:
        comentarios = driver.find_elements(By.XPATH, "//ul/ul")
        comentarios_count = len(comentarios)
    except:
        comentarios_count = 0

    datos.append({
        "link": link,
        "tipo": tipo_post,
        "likes": likes,
        "comentarios": comentarios_count
    })

# --- CERRAR ---
driver.quit()

# --- GUARDAR DATOS ---
df = pd.DataFrame(datos)
df["seguidores"] = seguidores
df.to_csv("instagram_mascotas.csv", index=False)
print(df.head())
