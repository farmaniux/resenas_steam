import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Steam-BI Analytics", layout="wide")
st.title("🎮 Steam-BI: Predicción y Análisis de Mercado")

# 2. Conexión a Base de Datos (Configuración exacta para Supabase Transaction Pooler)
def get_connection():
    try:
        db_url = st.secrets["DB_URI"]
        
        # Ajuste de protocolo para SQLAlchemy
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
            
        # CONFIGURACIÓN CRÍTICA
        engine = create_engine(db_url, 
            connect_args={
                "sslmode": "require",
                # ESTO SOLUCIONA EL "DOES NOT SUPPORT PREPARE STATEMENTS"
                "prepare_threshold": None, 
                # ESTO SOLUCIONA EL "SERVER DIDN'T RETURN CLIENT ENCODING"
                "options": "-c client_encoding=utf8"
            },
            pool_pre_ping=True, 
            pool_recycle=300
        )
        return engine
    except Exception as e:
        st.error(f"Error de configuración: {e}")
        return None

# 3. Carga de Datos
@st.cache_data(ttl=600) # Recarga datos cada 10 mins
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
    st.warning("Conexión exitosa, pero no se encontraron datos en la tabla.")
    st.stop()

# 4. Dashboard y ML
st.sidebar.header("🔮 Simulador de Ventas")
max_reviews = int(df['conteo_resenas'].max()) if not df.empty else 1000
sim_reviews = st.sidebar.slider("Cantidad de Reseñas", 100, int(max_reviews * 1.5), 1000)
sim_ratio = st.sidebar.slider("Calidad de Reseñas (Positividad)", 0.0, 1.0, 0.85)

# Modelo Machine Learning
X = df[['conteo_resenas', 'ratio_positividad']]
y = df['monto_ventas_usd']

if len(df) > 5:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    prediccion = model.predict([[sim_reviews, sim_ratio]])[0]
    
    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventas Predichas", f"${prediccion:,.2f}")
    c2.metric("Datos Históricos", len(df))
    c3.metric("Región BD", "US-WEST-2")
    
    # Gráfico
    fig = px.scatter(df, x="conteo_resenas", y="monto_ventas_usd", 
                     color="genero", title="Proyección de Ingresos vs Reseñas")
    fig.add_scatter(x=[sim_reviews], y=[prediccion], mode='markers', 
                    marker=dict(size=25, color='red'), name='Tu Predicción')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Necesitas más datos para generar predicciones.")
