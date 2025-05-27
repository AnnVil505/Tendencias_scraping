import pandas as pd

df_mercado_libre = pd.read_csv("./Datos_extraidos/Datos_procesados/mercado_libre_con_categorias.csv")
df_aliexpress = pd.read_csv("./Datos_extraidos/Datos_procesados/aliexpress_con_categorias.csv")
df_amazon = pd.read_csv("./Datos_extraidos/Datos_procesados/amazon_con_categorias.csv")

# 1. Agregar columna 'marketplace'
df_aliexpress['marketplace'] = 'AliExpress'
df_mercado_libre['marketplace'] = 'Mercado Libre'
df_amazon['marketplace'] = 'Amazon'

# 2. Homogeneizar columnas
# Asegurar que todas tengan las mismas columnas
common_columns = ['title', 'price', 'sold', 'rating', 'category', 'marketplace']

# Rellenar columnas faltantes con valores nulos si es necesario
if 'reviews' not in df_aliexpress.columns:
    df_aliexpress['reviews'] = None
if 'discount' not in df_mercado_libre.columns:
    df_mercado_libre['discount'] = 0
if 'discount' not in df_amazon.columns:
    df_amazon['discount'] = 0

# 3. Reordenar y seleccionar columnas en todos los datasets
df_aliexpress = df_aliexpress[['title', 'price', 'sold', 'rating', 'reviews', 'discount', 'category', 'marketplace']]
df_mercado_libre = df_mercado_libre[['title', 'price', 'sold', 'rating', 'reviews', 'discount', 'category', 'marketplace']]
df_amazon = df_amazon[['title', 'price', 'sold', 'rating', 'reviews', 'discount', 'category', 'marketplace']]

# 4. Unir todos los datasets
df = pd.concat([df_aliexpress, df_mercado_libre, df_amazon], ignore_index=True)

# 5. Limpiar y convertir tipos
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['sold'] = pd.to_numeric(df['sold'], errors='coerce')
df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
df['reviews'] = pd.to_numeric(df['reviews'], errors='coerce')
df['discount'] = pd.to_numeric(df['discount'], errors='coerce')

# 6. Discretizar variables

# a) sold_level
df['sold_level'] = pd.cut(df['sold'], bins=[-1, 100, 500, float('inf')], labels=['bajo', 'medio', 'alto'])

# b) price_level
df['price_level'] = pd.qcut(df['price'], q=3, labels=['bajo', 'medio', 'alto'])

# c) rating_level
df['rating_level'] = pd.cut(df['rating'], bins=[0, 3.5, 4.2, 5], labels=['bajo', 'medio', 'alto'])

# d) reviews_level
df['reviews_level'] = pd.cut(df['reviews'], bins=[-1, 0, 50, float('inf')], labels=['sin', 'pocas', 'muchas'])

# (Opcional) Reemplazar NaN con 'desconocido' si hace falta
df.fillna({'price_level': 'desconocido',
           'rating_level': 'desconocido',
           'reviews_level': 'desconocido',
           'sold_level': 'desconocido'}, inplace=True)

# Mostrar muestra del dataset final
print(df[['title', 'marketplace', 'category', 'price_level', 'rating_level', 'reviews_level', 'sold_level']].head())

# Guardar el resultado
df.to_csv("dataset_competencia.csv", index=False)
