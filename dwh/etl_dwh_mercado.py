import os
import pandas as pd
import unicodedata # Importar el módulo unicodedata
from sqlalchemy import (
    create_engine, Table, Column, Integer, String, Date, Numeric, MetaData, ForeignKey
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# --- 1. CONFIGURACIÓN MEJORADA ---
# Carga las credenciales de forma segura desde variables de entorno.
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'mercadoLibre')


# --- 2. SOLUCIÓN AL ERROR: Intentar diferentes codificaciones al leer CSV ---
# Si 'utf-8' falla, intentamos con 'latin-1' o 'ISO-8859-1' que son comunes
# para caracteres especiales en español.
def cargar_csv_con_manejo_errores(filepath):
    """
    Intenta cargar un archivo CSV con varias codificaciones comunes.
    Prioriza UTF-8, luego Latin-1, y finalmente CP1252.
    """
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
    df = None
    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            print(f"✔ Archivo '{filepath}' cargado con codificación {encoding.upper()}.")
            return df
        except UnicodeDecodeError:
            print(f"❗ Codificación '{encoding}' falló para '{filepath}'. Intentando la siguiente...")
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo '{filepath}'. Revisa la ruta.")
            raise # Relanzar para que el programa termine si no se encuentra el archivo
        except Exception as e:
            print(f"❌ Ocurrió un error inesperado al cargar '{filepath}' con {encoding}: {e}")
            raise # Relanzar cualquier otra excepción

    if df is None: # Si llegamos aquí, ninguna codificación funcionó
        raise Exception(f"❌ No se pudo cargar el archivo '{filepath}' con ninguna de las codificaciones intentadas.")
    return df # Esto no debería ejecutarse si se lanza una excepción

# Carga de los DataFrames al inicio del script
try:
    df_instagram = cargar_csv_con_manejo_errores("instagram_mascotas.csv")
    df_market = cargar_csv_con_manejo_errores("dataset_competencia_modelo2.csv")
except Exception:
    # Si la carga de los CSV falla, salimos del programa.
    # El mensaje de error ya habrá sido impreso por la función cargar_csv_con_manejo_errores.
    exit()


def crear_schema(engine: Engine):
    """Define y crea el esquema de la base de datos."""
    metadata = MetaData()

    # Definición de las tablas (dimensiones y hechos)
    dim_categoria = Table('dim_categoria', metadata,
        Column('id_categoria', Integer, primary_key=True),
        Column('nombre_categoria', String(100))
    )
    dim_subcategoria = Table('dim_subcategoria', metadata,
        Column('id_subcategoria', Integer, primary_key=True),
        Column('id_categoria', Integer, ForeignKey('dim_categoria.id_categoria')),
        Column('nombre_subcategoria', String(100))
    )
    dim_tipo_publicacion = Table('dim_tipo_publicacion', metadata,
        Column('id_tipo_publicacion', Integer, primary_key=True),
        Column('tipo_publicacion', String(50))
    )
    dim_marketplace = Table('dim_marketplace', metadata,
        Column('id_marketplace', Integer, primary_key=True),
        Column('nombre_marketplace', String(100))
    )
    fact_instagram = Table('fact_instagram', metadata,
        Column('id_fact_instagram', Integer, primary_key=True, autoincrement=True),
        Column('fecha_publicacion', Date),
        Column('id_subcategoria', Integer, ForeignKey('dim_subcategoria.id_subcategoria')),
        Column('id_tipo_publicacion', Integer, ForeignKey('dim_tipo_publicacion.id_tipo_publicacion')),
        Column('likes', Integer),
        Column('comentarios', Integer)
    )
    fact_ventas = Table('fact_ventas', metadata,
        Column('id_fact_venta', Integer, primary_key=True, autoincrement=True),
        Column('id_marketplace', Integer, ForeignKey('dim_marketplace.id_marketplace')),
        Column('id_subcategoria', Integer, ForeignKey('dim_subcategoria.id_subcategoria')),
        Column('precio', Numeric(10, 2)),
        Column('rating', Numeric(3, 2)),
        Column('descuento', Numeric(5, 2)),
        Column('nivel_ventas', String(50))
    )

    # Elimina y crea las tablas.
    # CUIDADO: En un entorno de producción, drop_all() borrará todos los datos.
    # Asegúrate de entender las implicaciones antes de usarlo en producción.
    try:
        metadata.drop_all(engine)
        metadata.create_all(engine)
        print("✔ Esquema de tablas creado en la base de datos.")
    except SQLAlchemyError as e:
        print(f"❌ Error al crear/eliminar tablas en la base de datos: {e}")
        raise # Relanzar la excepción para detener el proceso si hay un error de DB
    
    return metadata.tables

def limpiar_texto(df):
    """
    Normaliza el texto en columnas de tipo 'object' (cadenas) para asegurar que sean
    compatibles con UTF-8 y se manejen correctamente en la base de datos.
    Esto es crucial para evitar errores de codificación al insertar datos.
    Convierte caracteres acentuados a su equivalente ASCII y elimina los no ASCII.
    """
    for col in df.columns:
        if df[col].dtype == 'object':
            # Rellenar NaN/None con una cadena vacía antes de aplicar el método .str
            df[col] = df[col].fillna('')
            # Aplicar normalización NFKD, codificar a ASCII ignorando errores,
            # y luego decodificar a UTF-8. Esto elimina caracteres problemáticos.
            df[col] = df[col].astype(str).apply(
                lambda x: unicodedata.normalize('NFKD', x).encode('ascii', errors='ignore').decode('utf-8')
            )
    return df


def cargar_datos(engine: Engine, tablas: dict):
    """Transforma y carga los datos de los DataFrames en la base de datos."""
    
    # Uso de una única transacción para asegurar la integridad de la carga.
    # Si algo falla, se revierte todo el proceso (atomicidad).
    try:
        with engine.begin() as conn:
            print("Iniciando carga de datos...")
            
            # Aplicar limpieza de texto a los DataFrames antes de usar sus valores
            # para dimensiones y hechos. Esto asegura que los datos estén limpios
            # antes de cualquier manipulación o inserción en la DB.
            df_instagram_limpio = limpiar_texto(df_instagram.copy())
            df_market_limpio = limpiar_texto(df_market.copy())

            # --- DEBUGGING: Imprimir columnas disponibles en df_market_limpio ---
            print("\nDEBUG: Columnas disponibles en df_market_limpio antes de la carga de hechos de ventas:")
            print(df_market_limpio.columns.tolist())
            print("-" * 50)

            # --- Carga de Dimensiones ---
            conn.execute(tablas['dim_categoria'].insert(), [{"id_categoria": 1, "nombre_categoria": "Mascotas"}])

            subcategorias = df_instagram_limpio["subcategoria"].unique()
            subcat_map = {name: i + 1 for i, name in enumerate(subcategorias)}
            conn.execute(tablas['dim_subcategoria'].insert(), [
                {"id_subcategoria": i + 1, "id_categoria": 1, "nombre_subcategoria": sub}
                for i, sub in enumerate(subcategorias)
            ])
            
            tipos = df_instagram_limpio["tipo_publicacion"].unique()
            tipo_map = {name: i + 1 for i, name in enumerate(tipos)}
            conn.execute(tablas['dim_tipo_publicacion'].insert(), [
                {"id_tipo_publicacion": i + 1, "tipo_publicacion": tipo}
                for i, tipo in enumerate(tipos)
            ])

            marketplaces = df_market_limpio["marketplace"].unique()
            market_map = {name: i + 1 for i, name in enumerate(marketplaces)}
            conn.execute(tablas['dim_marketplace'].insert(), [
                {"id_marketplace": i + 1, "nombre_marketplace": name}
                for i, name in enumerate(marketplaces)
            ])
            print("✔ Dimensiones cargadas.")

            # --- Carga de Hechos Instagram ---
            df_instagram_fact = df_instagram_limpio.copy()
            df_instagram_fact["id_subcategoria"] = df_instagram_fact["subcategoria"].map(subcat_map)
            df_instagram_fact["id_tipo_publicacion"] = df_instagram_fact["tipo_publicacion"].map(tipo_map)
            # Conversión explícita a tipo de fecha y hora de Pandas
            df_instagram_fact["fecha_publicacion"] = pd.to_datetime(df_instagram_fact["fecha_publicacion"])
            
            df_instagram_final = df_instagram_fact[[
                "fecha_publicacion", "id_subcategoria", "id_tipo_publicacion", "likes", "comentarios"
            ]]
            
            # Carga los datos al fact_instagram
            df_instagram_final.to_sql("fact_instagram", conn, if_exists="append", index=False)
            print("✔ Hechos de Instagram cargados.")

            # --- Carga de Hechos Ventas ---
            df_market_fact = df_market_limpio.copy()
            df_market_fact["id_subcategoria"] = df_market_fact["category"].map(subcat_map)
            df_market_fact["id_marketplace"] = df_market_fact["marketplace"].map(market_map)

            # Renombra columnas para que coincidan con el esquema de la DB
            # Es crucial que los nombres de las columnas en tu CSV original
            # (dataset_competencia_modelo.csv) coincidan con las claves de este diccionario.
            # Si 'rating' tiene un nombre diferente en tu CSV (ej. 'Product_Rating', 'Stars'),
            # debes añadirlo aquí: "Nombre_Original_Rating": "rating"
            column_renames = {
                "price": "precio",
                "discount": "descuento",
                "sold_level": "nivel_ventas"
            }

            # Aplicar el renombramiento
            df_market_final = df_market_fact.rename(columns=column_renames)
            
            # Verificar si la columna 'rating' existe después del renombramiento
            # Si no existe, significa que el CSV original no tenía una columna llamada 'rating'
            # ni un nombre alternativo mapeado.
            if 'rating' not in df_market_final.columns:
                print("❌ ERROR: La columna 'rating' no se encontró en el DataFrame de ventas después del renombramiento.")
                print("Por favor, verifica el archivo 'dataset_competencia_modelo.csv' y asegúrate de que contenga una columna de calificación (rating).")
                print(f"Columnas disponibles después de renombrar: {df_market_final.columns.tolist()}")
                raise KeyError("Columna 'rating' faltante en el DataFrame de ventas. Revisa el CSV y el mapeo.")

            df_market_carga = df_market_final[[
                "id_marketplace", "id_subcategoria", "precio", "rating", "descuento", "nivel_ventas"
            ]]
            
            # Carga los datos al fact_ventas
            df_market_carga.to_sql("fact_ventas", conn, if_exists="append", index=False)
            print("✔ Hechos de Ventas cargados.")
            
    except SQLAlchemyError as e:
        print(f"❌ Error en la transacción de carga de datos: {e}")
        raise # Relanzar la excepción para que el main() la capture
    except KeyError as e: # Capturar el error específico de columna faltante
        print(f"❌ Error de columna faltante: {e}")
        raise # Relanzar para que el main() lo capture

def main():
    """Función principal para orquestar el proceso de ETL."""
    try:
        connection_url = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        engine = create_engine(connection_url)
        
        # Primero crea el esquema (tablas)
        tablas = crear_schema(engine)
        
        # Luego carga los datos
        cargar_datos(engine, tablas)
        
        print("\n🚀 Proceso de carga completado exitosamente.")
        
    except Exception as e:
        # Captura cualquier excepción no manejada y la imprime.
        print(f"❌ Ocurrió un error en el proceso: {e}")

if __name__ == '__main__':
    main()
