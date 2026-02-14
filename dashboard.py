import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Steam-BI Analytics", layout="wide")
st.title("🎮 Steam-BI: Predicción y Análisis de Mercado")

# 2. Conexión a Base de Datos (Configuración para Transaction Pooler)
def get_connection():
    try:
        db_url = st.secrets["DB_URI"]
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
            
        engine = create_engine(
            db_url, 
            connect_args={
                "sslmode": "require",
                "prepare_threshold": None,
                "options": "-c client_encoding=utf8"
            },
            pool_pre_ping=True
        )
        return engine
    except Exception as e:
        st.error(f"Error de configuración: {e}")
        return None

# 3. Carga de Datos con Nombres Reales de tu Esquema
@st.cache_data(ttl=600)
def load_data():
    engine = get_connection()
    if engine is None:
        return pd.DataFrame()

    # AJUSTE SEGÚN TU IMAGEN: appid y nombre
    query = """
    SELECT 
        h.cantidad_descargas,
        h.monto_ventas_usd,
        h.votos_positivos,
        h.votos_negativos,
        h.conteo_resenas,
        d.nombre,
        d.subgenero
    FROM hechos_resenas_steam h
    JOIN dim_juego d ON h.fk_juego = d.appid
    """
    try:
        df = pd.read_sql(query, engine)
        if not df.empty:
            df['ratio_positividad'] = df['votos_positivos'] / (df['votos_positivos'] + df['votos_negativos'])
            df = df.fillna(0)
        return df
    except Exception as e:
        st.error(f"Error SQL: {e}")
        return pd.DataFrame()

df = load_data()

# 4. Verificación y Dashboard
if df.empty:
    st.warning("⚠️ No se encontraron datos. Verifica que el ETL haya cargado la tabla 'hechos_resenas_steam'.")
    st.stop()

st.sidebar.header("🔮 Simulador de Ventas")
max_reviews = int(df['conteo_resenas'].max()) if not df.empty else 1000
sim_reviews = st.sidebar.slider("Volumen de Reseñas", 100, int(max_reviews * 1.5), 1000)
sim_ratio = st.sidebar.slider("Ratio de Positividad", 0.0, 1.0, 0.85)

X = df[['conteo_resenas', 'ratio_positividad']]
y = df['monto_ventas_usd']

if len(df) > 5:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    prediccion = model.predict([[sim_reviews, sim_ratio]])[0]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos Predichos", f"${prediccion:,.2f} USD")
    c2.metric("Juegos en BD", len(df))
    c3.metric("Región", "US-WEST-2")
    
    st.subheader("📊 Análisis: Reseñas vs Ingresos")
    fig = px.scatter(
        df, x="conteo_resenas", y="monto_ventas_usd", 
        color="subgenero", hover_data=["nombre"],
        title="Mercado Real vs Simulación"
    )
    fig.add_scatter(x=[sim_reviews], y=[prediccion], mode='markers', 
                    marker=dict(size=20, color='red', symbol='star'), name='Tu Predicción')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Se necesitan más registros para activar el modelo.")
