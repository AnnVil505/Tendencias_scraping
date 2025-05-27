import pandas as pd

# Cargar los datasets
ml = pd.read_csv('./Datos_extraidos/mercado_libre_productos_mas_vendidos.csv')     # Debe tener columna 'category'
amz = pd.read_csv('./Datos_extraidos/amazon_productos_mas_vendidos.csv')           # Tiene 'title'
ali = pd.read_csv('./Datos_extraidos/aliexpress_productos_mas_vendidos.csv')       # Tiene 'name'

# Normaliza los títulos a minúscula para facilitar el análisis
amz['title'] = amz['title'].str.lower()
ali['name'] = ali['name'].str.lower()

# Lista de categorías únicas de Mercado Libre
categorias_ml = ml['category'].dropna().unique()

# Función para asignar categoría según coincidencia de palabras clave
def asignar_categoria(texto, categorias):
    for categoria in categorias:
        if pd.isna(texto):
            continue
        if categoria.lower() in texto:
            return categoria
    return 'otros'

# Aplicar función a títulos de Amazon y AliExpress
#amz['category'] = amz['title'].apply(lambda x: asignar_categoria(x, categorias_ml))
ali['category'] = ali['name'].apply(lambda x: asignar_categoria(x, categorias_ml))

# Resultado: ahora los tres datasets tienen columna 'category'
#amz.to_csv('./Datos_extraidos/Datos_procesados/amazon_con_categorias.csv', index=False)
ali.to_csv('./Datos_extraidos/Datos_procesados/aliexpress_con_categorias.csv', index=False)