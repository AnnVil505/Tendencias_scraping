import pandas as pd

# Cargar el dataset (ajusta el nombre del archivo según corresponda)
df = pd.read_csv("./Datos_extraidos\Datos_procesados\mercado_libre_con_categorias.csv")

# Eliminar la columna original 'name' y renombrar 'name_es' como 'name'
df = df.drop(columns=['category']).rename(columns={'categoria_ml': 'category'})
df = df.drop(columns={'asin'})
df = df.rename(columns={'sales': 'sold'})

# Reordenar columnas si lo deseas
df = df[['title', 'price', 'reviews', 'sold', 'rating', 'category']]

# Guardar el resultado
df.to_csv("aliexpress_con_categorias.csv", index=False)
