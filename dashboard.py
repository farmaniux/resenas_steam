import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import plotly.express as px

# 1. Configuración
st.set_page_config(page_title="Steam-BI Analytics", layout="wide")
st.title("🎮 Steam-BI: Predicción y Análisis de Mercado")

# 2. Conexión a Base de Datos (Optimizada para Supabase Pooler)
def get_connection():
    try:
        db_url = st.secrets["DB_URI"]
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        # Configuración crítica para el puerto 6543
        engine = create_engine(db_url, connect_args={
            'sslmode':'require',
            'prepare_threshold': None 
        })
        return engine
    except Exception as e:
        st.error(f"Error de configuración: {e}")
        return None

# 3. Carga de Datos
@st.cache_data
def load_data():
    engine = get_connection()
    if engine is None:
        return pd.DataFrame()

    query = """
    SELECT 
        h.cantidad_descargas,
        h.monto_ventas_usd,
        h.votos_positivos,
        h.votos_negativos,
        h.conteo_resenas,
        d.nombre_juego,
        d.genero
    FROM hechos_resenas_steam h
    JOIN dim_juego d ON h.fk_juego = d.id_juego
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

if df.empty:
    st.warning("Conexión exitosa pero sin datos, o error de lectura.")
    st.stop()

# 4. Dashboard y ML
st.sidebar.header("🔮 Simulador")
sim_reviews = st.sidebar.slider("Reseñas", 100, int(df['conteo_resenas'].max()*1.5), 1000)
sim_ratio = st.sidebar.slider("Positividad", 0.0, 1.0, 0.85)

X = df[['conteo_resenas', 'ratio_positividad']]
y = df['monto_ventas_usd']

if len(df) > 5:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    prediccion = model.predict([[sim_reviews, sim_ratio]])[0]
    
    col1, col2 = st.columns(2)
    col1.metric("Ventas Predichas", f"${prediccion:,.2f}")
    col2.metric("Datos Reales", len(df))
    
    fig = px.scatter(df, x="conteo_resenas", y="monto_ventas_usd", color="genero", title="Proyección de Ventas")
    fig.add_scatter(x=[sim_reviews], y=[prediccion], mode='markers', marker=dict(size=20, color='red'), name='Simulación')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Necesitas más datos para entrenar el modelo.")
