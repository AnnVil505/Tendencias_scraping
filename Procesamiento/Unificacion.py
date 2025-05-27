import pandas as pd

df = pd.read_csv("./dataset_competencia.csv")

# --- Limpieza y transformación ---

# 1. Quitar símbolo de moneda y convertir a numérico (COP ya convertido)
df['price'] = df['price'].astype(float)

# 2. Asegurar que las columnas numéricas estén bien formateadas
df['sold'] = df['sold'].astype(int)

# 3. Discretización (crear nuevas columnas categóricas)

# Ventas
df['sold_level'] = pd.cut(df['sold'], 
    bins=[-1, 103, 1000, float('inf')], 
    labels=['Bajo', 'Medio', 'Alto'])


df_modelo = df[['price', 'rating', 'discount', 'category', 'marketplace', 'sold_level']]

# Eliminar filas con valores faltantes (por cortesía de discretización)
df_modelo = df_modelo.dropna()

df_modelo.to_csv("./dataset_competencia_modelo2.csv", index=False)