import pandas as pd
import re

df_mercado_libre = pd.read_csv("./Datos_extraidos/Datos_procesados/mercado_libre_con_categorias.csv")
df_aliexpress = pd.read_csv("./Datos_extraidos/Datos_procesados/aliexpress_con_categorias.csv")
df_amazon = pd.read_csv("./Datos_extraidos/Datos_procesados/amazon_con_categorias.csv")

# Función para limpiar precios en formato "COP13.350,84"
def clean_price(price_str):
    if isinstance(price_str, str):
        price_str = price_str.replace("COP", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(price_str)
    except:
        return None

# Función para limpiar descuentos "-25%"
def clean_discount(discount_str):
    if isinstance(discount_str, str):
        match = re.search(r"-?(\d+)", discount_str)
        return int(match.group(1)) if match else 0
    return 0

# Función para limpiar campo 'sold'
def clean_sold(sold_str):
    if isinstance(sold_str, str):
        sold_str = sold_str.lower()
        if 'k' in sold_str:
            match = re.search(r"([\d,.]+)", sold_str)
            if match:
                return int(float(match.group(1).replace(",", "").replace(".", "")) * 1000)
        match = re.search(r"(\d+)", sold_str)
        if match:
            return int(match.group(1))
    try:
        return int(sold_str)
    except:
        return 0

# Limpieza de AliExpress
def clean_aliexpress(df):
    df['marketplace'] = 'AliExpress'
    df['price'] = df['price'].apply(clean_price)
    df['discount'] = df['discount'].apply(clean_discount)
    df['sold'] = df['sold'].apply(clean_sold)
    df = df[['title', 'price', 'discount', 'sold', 'rating', 'category', 'marketplace']]
    return df

# Limpieza de Amazon
def clean_amazon(df):
    df['marketplace'] = 'Amazon'
    df['discount'] = 0
    df['sold'] = df['sold'].apply(clean_sold)
    df['price'] = df['price'] * 4000  # Conversión a COP
    df = df[['title', 'price', 'discount', 'sold', 'rating', 'category', 'marketplace']]
    return df

# Limpieza de Mercado Libre
def clean_mercado_libre(df):
    df['marketplace'] = 'Mercado Libre'
    df['discount'] = 0  # No hay descuento explícito
    df['sold'] = df['sold'].apply(clean_sold)
    df = df[['title', 'price', 'discount', 'sold', 'rating', 'category', 'marketplace']]
    return df


# Aplicar las funciones a cada dataframe
df_aliexpress_clean = clean_aliexpress(df_aliexpress)
df_amazon_clean = clean_amazon(df_amazon)
df_mercado_clean = clean_mercado_libre(df_mercado_libre)

df_all = pd.concat([df_aliexpress_clean, df_amazon_clean, df_mercado_clean], ignore_index=True)

# Ver una muestra final
print(df_all.head())

# Guardar el resultado
df_all.to_csv("dataset_competencia.csv", index=False)

