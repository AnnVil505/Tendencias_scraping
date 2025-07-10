import os
import pandas as pd
import unicodedata
from sqlalchemy import create_engine, Table, Column, Integer, String, Date, Numeric, MetaData, ForeignKey
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# --- CONFIGURACIÓN DE CONEXIÓN ---
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'mercadoLibre')


def cargar_csv_con_manejo_errores(filepath):
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            return pd.read_csv(filepath, encoding=encoding)
        except:
            continue
    raise Exception(f"No se pudo cargar el archivo {filepath}.")


def crear_schema(engine: Engine):
    metadata = MetaData()

    Table('dim_categoria', metadata,
        Column('id_categoria', Integer, primary_key=True),
        Column('nombre_categoria', String(100))
    )
    Table('dim_subcategoria', metadata,
        Column('id_subcategoria', Integer, primary_key=True),
        Column('id_categoria', Integer, ForeignKey('dim_categoria.id_categoria')),
        Column('nombre_subcategoria', String(100))
    )
    Table('dim_tipo_publicacion', metadata,
        Column('id_tipo_publicacion', Integer, primary_key=True),
        Column('tipo_publicacion', String(50))
    )
    Table('dim_marketplace', metadata,
        Column('id_marketplace', Integer, primary_key=True),
        Column('nombre_marketplace', String(100))
    )
    Table('fact_instagram', metadata,
        Column('id_fact_instagram', Integer, primary_key=True, autoincrement=True),
        Column('fecha_publicacion', Date),
        Column('id_subcategoria', Integer, ForeignKey('dim_subcategoria.id_subcategoria')),
        Column('id_tipo_publicacion', Integer, ForeignKey('dim_tipo_publicacion.id_tipo_publicacion')),
        Column('likes', Integer),
        Column('comentarios', Integer)
    )
    Table('fact_ventas', metadata,
        Column('id_fact_venta', Integer, primary_key=True, autoincrement=True),
        Column('id_marketplace', Integer, ForeignKey('dim_marketplace.id_marketplace')),
        Column('id_subcategoria', Integer, ForeignKey('dim_subcategoria.id_subcategoria')),
        Column('precio', Numeric(10, 2)),
        Column('rating', Numeric(3, 2)),
        Column('descuento', Numeric(5, 2)),
        Column('nivel_ventas', String(50))
    )

    metadata.drop_all(engine)
    metadata.create_all(engine)
    return metadata.tables


def limpiar_texto(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('').astype(str).apply(
                lambda x: unicodedata.normalize('NFKD', x).encode('ascii', errors='ignore').decode('utf-8')
            )
    return df

def cargar_datos(engine: Engine, tablas: dict, df_instagram, df_market):
    with engine.begin() as conn:
        df_instagram = limpiar_texto(df_instagram)
        df_market = limpiar_texto(df_market)

        # Usar "category" como especie
        especies = df_market["category"].unique()
        especie_map = {name: i + 1 for i, name in enumerate(especies)}
        conn.execute(tablas['dim_categoria'].insert(), [
            {"id_categoria": i + 1, "nombre_categoria": especie}
            for i, especie in enumerate(especies)
        ])

        df_market["id_categoria"] = df_market["category"].map(especie_map)

        # La subcategoría ya viene como columna estandarizada
        subcategorias = df_market[["subcategoria", "id_categoria"]].drop_duplicates()
        subcat_map = {row.subcategoria: i + 1 for i, row in subcategorias.iterrows()}
        conn.execute(tablas['dim_subcategoria'].insert(), [
            {
                "id_subcategoria": i + 1,
                "id_categoria": row.id_categoria,
                "nombre_subcategoria": row.subcategoria
            }
            for i, row in subcategorias.iterrows()
        ])

        # Tipo de publicación de Instagram
        tipos = df_instagram["tipo_publicacion"].unique()
        tipo_map = {name: i + 1 for i, name in enumerate(tipos)}
        conn.execute(tablas['dim_tipo_publicacion'].insert(), [
            {"id_tipo_publicacion": i + 1, "tipo_publicacion": tipo}
            for i, tipo in enumerate(tipos)
        ])

        # Marketplaces
        marketplaces = df_market["marketplace"].unique()
        market_map = {name: i + 1 for i, name in enumerate(marketplaces)}
        conn.execute(tablas['dim_marketplace'].insert(), [
            {"id_marketplace": i + 1, "nombre_marketplace": name}
            for i, name in enumerate(marketplaces)
        ])

        # Cargar fact_instagram
        df_instagram["id_subcategoria"] = df_instagram["subcategoria"].map(subcat_map)
        df_instagram["id_tipo_publicacion"] = df_instagram["tipo_publicacion"].map(tipo_map)
        df_instagram["fecha_publicacion"] = pd.to_datetime(df_instagram["fecha_publicacion"])
        df_instagram_final = df_instagram[[
            "fecha_publicacion", "id_subcategoria", "id_tipo_publicacion", "likes", "comentarios"
        ]]
        df_instagram_final.to_sql("fact_instagram", conn, if_exists="append", index=False)

        # Cargar fact_ventas
        column_renames = {"price": "precio", "discount": "descuento", "sold_level": "nivel_ventas"}
        df_market = df_market.rename(columns=column_renames)
        df_market["id_subcategoria"] = df_market["subcategoria"].map(subcat_map)
        df_market["id_marketplace"] = df_market["marketplace"].map(market_map)

        df_market_final = df_market[[
            "id_marketplace", "id_subcategoria", "precio", "rating", "descuento", "nivel_ventas"
        ]]
        df_market_final.to_sql("fact_ventas", conn, if_exists="append", index=False)


def main():
    try:
        # Carga de CSVs
        df_instagram = cargar_csv_con_manejo_errores("instagram_mascotas.csv")
        df_market = cargar_csv_con_manejo_errores("dataset_competencia_modelo2.csv")
        df_perros = cargar_csv_con_manejo_errores("productos_perros_por_categoria.csv")
        df_gatos = cargar_csv_con_manejo_errores("productos_gatos_por_categoria.csv")

        # Estandarización de columnas
        columnas_estandar = {
            "Categoría": "subcategoria",
            "Precio actual": "price",
            "Descuento": "discount",
            "Calificación": "rating"
        }

        df_perros = df_perros.rename(columns=columnas_estandar)
        df_perros["marketplace"] = "Mercado Libre"
        df_perros["sold_level"] = None
        df_perros["category"] = "Perros"

        df_gatos = df_gatos.rename(columns=columnas_estandar)
        df_gatos["marketplace"] = "Mercado Libre"
        df_gatos["sold_level"] = None
        df_gatos["category"] = "Gatos"

        # Limpiar campo 'descuento': quitar % y texto
        df_gatos["discount"] = df_gatos["discount"].replace('', '0')
        df_gatos["discount"] = df_gatos["discount"].astype(str).str.extract(r'(\d+(?:\.\d+)?)')[0]  # extrae solo número
        df_gatos["discount"] = pd.to_numeric(df_gatos["discount"], errors='coerce').fillna(0.0)

        df_perros["discount"] = df_perros["discount"].replace('', '0')
        df_perros["discount"] = df_perros["discount"].astype(str).str.extract(r'(\d+(?:\.\d+)?)')[0]  # extrae solo número
        df_perros["discount"] = pd.to_numeric(df_perros["discount"], errors='coerce').fillna(0.0)



        # Ajustes en df_market
        df_market["subcategoria"] = "General"
        if "category" not in df_market.columns:
            df_market["category"] = "General"
        if "rating" not in df_market.columns:
            df_market["rating"] = None

        # Unificación
        df_market_total = pd.concat([df_perros, df_gatos, df_market], ignore_index=True)

        engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
        tablas = crear_schema(engine)
        cargar_datos(engine, tablas, df_instagram, df_market_total)


        print("\n🚀 Proceso de carga completado exitosamente.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
