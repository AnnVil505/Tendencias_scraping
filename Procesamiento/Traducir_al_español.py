from deep_translator import GoogleTranslator
import pandas as pd

# Cargar tus datasets
aliexpress = pd.read_csv('./Datos_extraidos/aliexpress_productos_mas_vendidos.csv')

# Traducir los títulos al español
aliexpress['name_es'] = aliexpress['name'].astype(str).apply(lambda x: GoogleTranslator(source='auto', target='es').translate(x))

# Guardar el resultado en un nuevo CSV
aliexpress.to_csv('aliexpress_traducido.csv', index=False)