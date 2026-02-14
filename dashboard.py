import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Steam-BI Analytics", layout="wide")
st.title("🎮 Steam-BI: Predicción y Análisis de Mercado")

# 2. Conexión a la Base de Datos (VERSIÓN CORREGIDA PARA SUPABASE)
def get_connection():
    try:
        db_url = st.secrets["DB_URI"]
        
        # Aseguramos el driver correcto
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
            
        # CONFIGURACIÓN CRÍTICA:
        # options="-c client_encoding=utf8" es lo que arregla tu error actual.
        engine = create_engine(db_url, 
            connect_args={
                "sslmode": "require",
                "prepare_threshold": None,
                "options": "-c client_encoding=utf8"
            },
            pool_pre_ping=True # Verifica que la conexión siga viva
        )
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
    st.warning("Conexión exitosa pero sin datos, o error de lectura. Verifica que tu tabla 'hechos_resenas_steam' tenga datos.")
    st.stop()

# 4. Dashboard y ML
st.sidebar.header("🔮 Simulador")
st.sidebar.write("Ajusta variables para predecir ventas:")

# Sliders dinámicos
max_reviews = int(df['conteo_resenas'].max()) if not df.empty else 1000
sim_reviews = st.sidebar.slider("Reseñas Totales", 100, int(max_reviews * 1.5), 1000)
sim_ratio = st.sidebar.slider("Positividad (%)", 0.0, 1.0, 0.85)

X = df[['conteo_resenas', 'ratio_positividad']]
y = df['monto_ventas_usd']

# Verificación de datos suficientes
if len(df) > 5:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    prediccion = model.predict([[sim_reviews, sim_ratio]])[0]
    
    col1, col2 = st.columns(2)
    col1.metric("Ventas Predichas", f"${prediccion:,.2f} USD")
    col2.metric("Datos Históricos", f"{len(df)} juegos")
    
    st.subheader("📊 Proyección de Ventas")
    fig = px.scatter(df, x="conteo_resenas", y="monto_ventas_usd", 
                     color="genero", hover_data=["nombre_juego"],
                     title="Mercado Real vs Tu Simulación")
                     
    fig.add_scatter(x=[sim_reviews], y=[prediccion], mode='markers', 
                    marker=dict(size=25, color='red'), name='Tu Predicción')
                    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Necesitas más datos para entrenar el modelo (mínimo 5 registros).")
