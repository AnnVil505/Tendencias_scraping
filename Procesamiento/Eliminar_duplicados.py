import pandas as pd

# Carga ambos CSV
df1 = pd.read_csv('./Datos_extraidos/aliexpress_productos.csv')
df2 = pd.read_csv('./Datos_extraidos/merged_unique.csv')

# Concatena
df = pd.concat([df1, df2], ignore_index=True)

# Elimina duplicados. 
# Por defecto comprueba todas las columnas:
df_unique = df.drop_duplicates()

# Si prefieres usar solo ciertas columnas como clave,
# usa e.g. subset=['asin'] o subset=['title', 'price']:
# df_unique = df.drop_duplicates(subset=['asin'])

# Guarda el resultado
df_unique.to_csv('merged_unique.csv', index=False)

print(f"Total original: {len(df)}, tras eliminar duplicados: {len(df_unique)}")
