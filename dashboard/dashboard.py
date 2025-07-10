import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import os
from dotenv import load_dotenv
import datetime

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de la Conexión a la Base de Datos ---
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'mercadoLibre')

# Crear la URL de conexión de SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear el motor de la base de datos
@st.cache_resource # Caché para no reconectar cada vez que Streamlit se actualiza
def get_db_engine():
    """Retorna el motor de conexión a la base de datos."""
    return create_engine(DATABASE_URL)

engine = get_db_engine()

# --- Funciones para Cargar Datos ---
@st.cache_data(ttl=600) # Caché para los datos por 10 minutos (600 segundos)
def load_data(query):
    """Carga datos desde la base de datos usando una consulta SQL."""
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame() # Devuelve un DataFrame vacío en caso de error

# --- Función Auxiliar para Fechas ---
def get_last_n_days(n_days):
    """Calcula la fecha de hace N días desde hoy."""
    today = datetime.date.today()
    past_date = today - datetime.timedelta(days=n_days)
    return past_date.isoformat() # Retorna en formato 'YYYY-MM-DD'

# --- Título y Configuración del Dashboard ---
st.set_page_config(layout="wide") # Configura el layout para usar todo el ancho de la página
st.title("📊 Dashboard de Rendimiento de Mascotas")
st.markdown("Este dashboard proporciona una visión general del rendimiento de ventas en marketplaces y el engagement en redes sociales.")

# --- Métricas Clave (KPIs) ---
st.header("📈 Métricas Clave del Negocio")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Ventas Totales (Mercado Libre)")
    query_total_sales = """
    SELECT SUM(precio) FROM fact_ventas WHERE id_marketplace = (SELECT id_marketplace FROM dim_marketplace WHERE nombre_marketplace = 'Mercado Libre');
    """
    df_total_sales = load_data(query_total_sales)
    total_sales = df_total_sales.iloc[0, 0] if not df_total_sales.empty and df_total_sales.iloc[0, 0] is not None else 0
    st.metric(label="Ingresos Estimados", value=f"${total_sales:,.2f}")

with col2:
    st.subheader("Productos con Descuento")
    query_discounted_products = """
    SELECT COUNT(*) FROM fact_ventas WHERE descuento > 0 AND id_marketplace = (SELECT id_marketplace FROM dim_marketplace WHERE nombre_marketplace = 'Mercado Libre');
    """
    df_discounted_products = load_data(query_discounted_products)
    discounted_count = df_discounted_products.iloc[0, 0] if not df_discounted_products.empty else 0
    st.metric(label="Cantidad", value=f"{int(discounted_count)}")

with col3:
    st.subheader("Rating Promedio (Mercado Libre)")
    query_avg_rating = """
    SELECT AVG(rating) FROM fact_ventas WHERE id_marketplace = (SELECT id_marketplace FROM dim_marketplace WHERE nombre_marketplace = 'Mercado Libre');
    """
    df_avg_rating = load_data(query_avg_rating)
    avg_rating = df_avg_rating.iloc[0, 0] if not df_avg_rating.empty and df_avg_rating.iloc[0, 0] is not None else 0
    st.metric(label="Calificación", value=f"{avg_rating:.2f} ⭐")



## 🛍️ Análisis de Ventas en Marketplaces

st.header("🛍️ Análisis de Ventas en Marketplaces")

# --- Ventas por Categoría Principal (Gráfico de Torta) ---
st.subheader("Distribución de Ventas por Categoría Principal")
query_sales_by_category = """
SELECT dc.nombre_categoria, SUM(fv.precio) AS total_ventas
FROM fact_ventas fv
JOIN dim_subcategoria dsc ON fv.id_subcategoria = dsc.id_subcategoria
JOIN dim_categoria dc ON dsc.id_categoria = dc.id_categoria
GROUP BY dc.nombre_categoria
ORDER BY total_ventas DESC;
"""
df_sales_by_category = load_data(query_sales_by_category)

if not df_sales_by_category.empty:
    fig_sales_category = px.pie(
        df_sales_by_category,
        names='nombre_categoria',
        values='total_ventas',
        title='Distribución de Ventas por Categoría Principal',
        hole=0.3 # Para un gráfico de donut
    )
    st.plotly_chart(fig_sales_category, use_container_width=True)

    with st.expander("Ver Detalles de Ventas por Categoría"):
        st.dataframe(df_sales_by_category, use_container_width=True)
else:
    st.info("No hay datos de ventas por categoría para mostrar.")

# --- Ventas por Subcategoría y Nivel de Ventas (Gráfico de Barras) ---
st.subheader("Ventas por Subcategoría y Nivel de Ventas")

# Obtener los niveles de ventas únicos para el filtro
query_sold_levels = "SELECT DISTINCT nivel_ventas FROM fact_ventas WHERE nivel_ventas IS NOT NULL ORDER BY nivel_ventas;"
df_sold_levels = load_data(query_sold_levels)
sold_levels = df_sold_levels['nivel_ventas'].tolist() if not df_sold_levels.empty else []

selected_sold_level = st.selectbox(
    "Filtrar por Nivel de Ventas:",
    options=['Todos'] + sold_levels,
    index=0,
    key="sold_level_filter" # Clave única
)

query_sales_by_subcategory = """
SELECT dsc.nombre_subcategoria, SUM(fv.precio) AS total_ventas, COUNT(*) AS num_productos, AVG(fv.rating) AS rating_promedio, fv.nivel_ventas
FROM fact_ventas fv
JOIN dim_subcategoria dsc ON fv.id_subcategoria = dsc.id_subcategoria
"""
if selected_sold_level != 'Todos':
    query_sales_by_subcategory += f"WHERE fv.nivel_ventas = '{selected_sold_level}'"

query_sales_by_subcategory += """
GROUP BY dsc.nombre_subcategoria, fv.nivel_ventas
ORDER BY total_ventas DESC
LIMIT 10;
"""
df_sales_by_subcategory = load_data(query_sales_by_subcategory)

if not df_sales_by_subcategory.empty:
    fig_sales_subcategory = px.bar(
        df_sales_by_subcategory,
        x="nombre_subcategoria",
        y="total_ventas",
        title=f"Top 10 Subcategorías por Ventas (Nivel: {selected_sold_level})",
        labels={"nombre_subcategoria": "Subcategoría", "total_ventas": "Ventas ($)"},
        color="total_ventas",
        hover_data=["num_productos", "rating_promedio"]
    )
    st.plotly_chart(fig_sales_subcategory, use_container_width=True)

    with st.expander("Ver Detalles de Ventas por Subcategoría"):
        st.dataframe(df_sales_by_subcategory, use_container_width=True)
else:
    st.info("No hay datos de ventas por subcategoría para mostrar con el filtro seleccionado.")

# --- Histograma de Distribución de Ratings ---
st.subheader("Distribución de Calificaciones de Productos")
query_rating_distribution = """
SELECT rating FROM fact_ventas WHERE rating IS NOT NULL;
"""
df_rating_distribution = load_data(query_rating_distribution)

if not df_rating_distribution.empty:
    fig_rating_distribution = px.histogram(
        df_rating_distribution,
        x='rating',
        title='Distribución de Calificaciones (Ratings) de Productos',
        nbins=10, # Puedes ajustar el número de bins (barras) del histograma
        labels={'rating': 'Calificación del Producto'}
    )
    st.plotly_chart(fig_rating_distribution, use_container_width=True)

    with st.expander("Ver Datos Crudos de Distribución de Ratings"):
        st.dataframe(df_rating_distribution, use_container_width=True)
else:
    st.info("No hay datos de calificación para mostrar su distribución.")

# --- Comparación de Ratings por Categoría Principal (Box Plot) ---
st.subheader("Comparación de Calificaciones por Categoría Principal")
query_ratings_by_category = """
SELECT dc.nombre_categoria, fv.rating
FROM fact_ventas fv
JOIN dim_subcategoria dsc ON fv.id_subcategoria = dsc.id_subcategoria
JOIN dim_categoria dc ON dsc.id_categoria = dc.id_categoria
WHERE fv.rating IS NOT NULL;
"""
df_ratings_by_category = load_data(query_ratings_by_category)

if not df_ratings_by_category.empty:
    fig_rating_by_category = px.box(
        df_ratings_by_category,
        x='nombre_categoria',
        y='rating',
        title='Distribución de Calificaciones por Categoría Principal',
        labels={'nombre_categoria': 'Categoría', 'rating': 'Calificación del Producto'}
    )
    st.plotly_chart(fig_rating_by_category, use_container_width=True)

    with st.expander("Ver Datos Crudos de Ratings por Categoría"):
        st.dataframe(df_ratings_by_category, use_container_width=True)
else:
    st.info("No hay datos de calificación para mostrar por categoría.")


## ❓ Preguntas de Negocio Clave

st.header("❓ Preguntas de Negocio Clave")

### 1. Productos con Precios Notablemente Superiores al Promedio de su Categoría

st.subheader("Precios de Productos vs. Promedio de Subcategoría")

# Consulta para obtener productos y el promedio de su subcategoría
query_high_price_products = """
WITH SubcategoryAvg AS (
    SELECT
        dsc.id_subcategoria,
        dsc.nombre_subcategoria,
        AVG(fv.precio) AS avg_price_subcategory
    FROM fact_ventas fv
    JOIN dim_subcategoria dsc ON fv.id_subcategoria = dsc.id_subcategoria
    GROUP BY dsc.id_subcategoria, dsc.nombre_subcategoria
)
SELECT
    fv.id_fact_venta,
    dc.nombre_categoria,
    dsc.nombre_subcategoria,
    fv.precio,
    sa.avg_price_subcategory,
    (fv.precio - sa.avg_price_subcategory) AS difference_from_avg,
    ROUND(((fv.precio - sa.avg_price_subcategory) / sa.avg_price_subcategory) * 100, 2) AS percentage_above_avg
FROM fact_ventas fv
JOIN dim_subcategoria dsc ON fv.id_subcategoria = dsc.id_subcategoria
JOIN dim_categoria dc ON dsc.id_categoria = dc.id_categoria
JOIN SubcategoryAvg sa ON fv.id_subcategoria = sa.id_subcategoria
WHERE fv.precio > sa.avg_price_subcategory -- Solo productos por encima del promedio
ORDER BY percentage_above_avg DESC
LIMIT 10;
"""
df_high_price_products = load_data(query_high_price_products)

if not df_high_price_products.empty:
    fig_high_prices = px.bar(
        df_high_price_products,
        x="nombre_subcategoria",
        y="percentage_above_avg",
        color="precio",
        title="Top 10 Productos con Mayor Porcentaje por Encima del Promedio de Subcategoría",
        labels={"nombre_subcategoria": "Subcategoría", "percentage_above_avg": "% Por Encima del Promedio"},
        hover_data=["nombre_categoria", "precio", "avg_price_subcategory", "difference_from_avg"]
    )
    st.plotly_chart(fig_high_prices, use_container_width=True)

    with st.expander("Ver Detalles de Productos con Precios Superiores"):
        st.write("Estos son los productos con precios más altos en comparación con el promedio de su subcategoría:")
        st.dataframe(df_high_price_products, use_container_width=True)
else:
    st.info("No se encontraron productos con precios significativamente superiores al promedio de su subcategoría.")


### 2. Publicaciones de Instagram con Rendimiento Bajo el Promedio

st.subheader("Engagement en Instagram: Rendimiento por Publicación")
# Filtros de fecha para Instagram
days_range = st.slider(
    "Selecciona el rango de días para análisis de Instagram:",
    30, 90, (30, 60),
    key="instagram_days_range" # Clave única
)
start_date_ig = get_last_n_days(days_range[1]) # Hace más días (el inicio del rango)
end_date_ig = get_last_n_days(days_range[0])   # Hace menos días (el fin del rango)

# Consulta para likes/comentarios por debajo del promedio en un rango de fechas
query_low_engagement_ig = f"""
WITH SubcategoryEngagement AS (
    SELECT
        fi.id_subcategoria,
        AVG(fi.likes) AS avg_likes_subcat,
        AVG(fi.comentarios) AS avg_comments_subcat
    FROM fact_instagram fi
    WHERE fi.fecha_publicacion BETWEEN '{start_date_ig}' AND '{end_date_ig}'
    GROUP BY fi.id_subcategoria
)
SELECT
    fi.id_fact_instagram,
    dsc.nombre_subcategoria,
    fi.fecha_publicacion,
    fi.likes,
    se.avg_likes_subcat,
    fi.comentarios,
    se.avg_comments_subcat
FROM fact_instagram fi
JOIN dim_subcategoria dsc ON fi.id_subcategoria = dsc.id_subcategoria
JOIN SubcategoryEngagement se ON fi.id_subcategoria = se.id_subcategoria
WHERE fi.fecha_publicacion BETWEEN '{start_date_ig}' AND '{end_date_ig}'
  AND (fi.likes < se.avg_likes_subcat OR fi.comentarios < se.avg_comments_subcat)
ORDER BY fi.likes ASC, fi.comentarios ASC
LIMIT 10;
"""

df_low_engagement_ig = load_data(query_low_engagement_ig)

if not df_low_engagement_ig.empty:
    col_ig1, col_ig2 = st.columns(2)
    with col_ig1:
        # Gráfico de Torta para Likes de bajo rendimiento por subcategoría
        fig_likes = px.pie(
            df_low_engagement_ig.groupby('nombre_subcategoria')['likes'].sum().reset_index(),
            values="likes",
            names="nombre_subcategoria",
            title="Likes por Subcategoría (Bajo Rendimiento)",
            hole=0.3
        )
        st.plotly_chart(fig_likes, use_container_width=True)
    with col_ig2:
        # Gráfico de Barras para Comentarios de bajo rendimiento por subcategoría
        fig_comments = px.bar(
            df_low_engagement_ig.groupby('nombre_subcategoria')['comentarios'].sum().reset_index(),
            x="nombre_subcategoria",
            y="comentarios",
            title="Comentarios por Subcategoría (Bajo Rendimiento)",
            labels={"nombre_subcategoria": "Subcategoría", "comentarios": "Total Comentarios"},
            color="comentarios"
        )
        st.plotly_chart(fig_comments, use_container_width=True)

    with st.expander("Ver Detalles de Publicaciones de Instagram con Bajo Rendimiento"):
        st.write("Estas son las publicaciones con likes/comentarios por debajo del promedio para el rango seleccionado:")
        st.dataframe(df_low_engagement_ig, use_container_width=True)
else:
    st.info("No se encontraron publicaciones de Instagram con rendimiento por debajo del promedio para el rango de fechas seleccionado, o no hay datos de Instagram.")


### 3. Subcategorías con Mejores Calificaciones (Perros y Gatos)

st.subheader("Calificaciones Promedio por Subcategoría")

# Filtro por categoría principal
selected_main_category = st.selectbox(
    "Selecciona la Categoría Principal para ver Ratings:",
    options=['Todos', 'Perros', 'Gatos'],
    index=0,
    key="best_ratings_category_filter" # Clave única
)

query_best_ratings = """
SELECT
    dc.nombre_categoria,
    dsc.nombre_subcategoria,
    AVG(fv.rating) AS promedio_rating,
    COUNT(fv.id_fact_venta) AS num_productos_vendidos
FROM fact_ventas fv
JOIN dim_subcategoria dsc ON fv.id_subcategoria = dsc.id_subcategoria
JOIN dim_categoria dc ON dsc.id_categoria = dc.id_categoria
WHERE fv.rating IS NOT NULL
"""

if selected_main_category != 'Todos':
    query_best_ratings += f"AND dc.nombre_categoria = '{selected_main_category}'"

query_best_ratings += """
GROUP BY dc.nombre_categoria, dsc.nombre_subcategoria
ORDER BY promedio_rating DESC, num_productos_vendidos DESC
LIMIT 10;
"""

df_best_ratings = load_data(query_best_ratings)

if not df_best_ratings.empty:
    fig_best_ratings = px.bar(
        df_best_ratings,
        x="nombre_subcategoria",
        y="promedio_rating",
        color="nombre_categoria",
        title=f"Top 10 Subcategorías con Mayor Rating Promedio ({selected_main_category})",
        labels={"nombre_subcategoria": "Subcategoría", "promedio_rating": "Rating Promedio"},
        hover_data=["num_productos_vendidos"]
    )
    st.plotly_chart(fig_best_ratings, use_container_width=True)

    with st.expander("Ver Detalles de Subcategorías con Mejores Calificaciones"):
        st.write("Estas son las subcategorías con las calificaciones más altas:")
        st.dataframe(df_best_ratings, use_container_width=True)
else:
    st.info("No hay datos de calificaciones para las subcategorías de la categoría seleccionada.")



st.info("Dashboard desarrollado con Streamlit y datos de PostgreSQL.")