import pandas as pd
import matplotlib.pyplot as plt

# Leer los datos
df = pd.read_csv("./Datos_extraidos/Datos_procesados/mercado_libre_con_categorias.csv")

# 1. Limpieza de datos - Convertir precios a numéricos
def limpiar_precio(precio):
    if pd.isna(precio):
        return None
    try:
        # Reemplazar puntos y comas según el formato
        if isinstance(precio, str):
            precio = precio.replace('.', '').replace(',', '.')
        return float(precio)
    except:
        return None

df['price'] = df['price'].apply(limpiar_precio)

# 2. Función mejorada para estimar ventas
def estimar_ventas(row):
    try:
        # Base: inversamente proporcional a la posición
        ventas_base = 1000 / row['position']
        
        # Ajustar por reseñas si están disponibles
        if pd.notna(row['reviews_count']):
            ventas_base *= (1 + row['reviews_count'] / 100)
        else:
            ventas_base *= 0.7  # Factor para productos sin reseñas
        
        return round(ventas_base)
    except:
        return 0  # Valor por defecto si hay error

# Agregar columna de ventas estimadas
df['sold'] = df.apply(estimar_ventas, axis=1)

# Renombrar columnas para coincidir con tu estructura deseada
df = df.rename(columns={
    'reviews_count': 'reviews'
})

# Filtrar y reordenar columnas como lo necesitas
df_transformado = df[["title", "price", "reviews", "sold", "rating", "category"]]

# Exportar a nuevo CSV
df_transformado.to_csv("mercado_libre_con_categorias_y_ventas.csv", index=False)