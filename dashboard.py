import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Steam-BI Analytics", layout="wide")
st.title("🎮 Steam-BI: Predicción y Análisis de Mercado")

# 2. Conexión a Base de Datos (Configuración definitiva para Transaction Pooler)
def get_connection():
    try:
        db_url = st.secrets["DB_URI"]
        
        # Ajuste de protocolo para SQLAlchemy (psycopg2 es el driver más estable para esto)
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
            
        # CONFIGURACIÓN MAESTRA PARA EVITAR ERRORES DE ENCODING Y PREPARED STATEMENTS
        engine = create_engine(
            db_url, 
            connect_args={
                "sslmode": "require",
                "prepare_threshold": None, # Vital para puerto 6543
                "options": "-c client_encoding=utf8" # Arregla el error de encoding
            },
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True, # Verifica si la conexión está viva
            pool_recycle=300    # Recicla conexiones cada 5 minutos
        )
        return engine
    except Exception as e:
        st.error(f"Error de configuración: {e}")
        return None

# 3. Carga de Datos
@st.cache_data(ttl=600) # Recarga automática cada 10 minutos
def load_data():
    engine = get_connection()
    if engine is None:
        return pd.DataFrame()

    # Consulta optimizada (Asegúrate de que las tablas existan con estos nombres)
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
            # Calcular ratio de positividad para el modelo
            df['ratio_positividad'] = df['votos_positivos'] / (df['votos_positivos'] + df['votos_negativos'])
            df = df.fillna(0)
        return df
    except Exception as e:
        st.error(f"Error SQL al leer datos: {e}")
        return pd.DataFrame()

# Ejecución de carga
df = load_data()

# 4. Verificación de contenido
if df.empty:
    st.warning("⚠️ El Dashboard está conectado, pero no se recuperaron registros. Verifica que el ETL haya cargado datos en 'hechos_resenas_steam'.")
    st.stop()

# 5. Barra Lateral: Simulador de Negocio
st.sidebar.header("🔮 Simulador de Ventas")
st.sidebar.write("Modifica los parámetros para ver la predicción:")

max_reviews = int(df['conteo_resenas'].max()) if not df.empty else 1000
sim_reviews = st.sidebar.slider("Volumen de Reseñas", 100, int(max_reviews * 1.5), 1000)
sim_ratio = st.sidebar.slider("Ratio de Positividad (0 a 1)", 0.0, 1.0, 0.85)

# 6. Modelo Machine Learning (Random Forest)
X = df[['conteo_resenas', 'ratio_positividad']]
y = df['monto_ventas_usd']

if len(df) > 5:
    # Entrenamiento rápido para la simulación
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Predicción basada en sliders
    prediccion = model.predict([[sim_reviews, sim_ratio]])[0]
    
    # Visualización de Métricas Principales
    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos Predichos", f"${prediccion:,.2f} USD")
    c2.metric("Juegos Analizados", len(df))
    c3.metric("Región de Datos", "US-WEST-2")
    
    # 7. Gráfico Interactivo
    st.subheader("📊 Análisis de Correlación: Reseñas vs Ingresos")
    fig = px.scatter(
        df, 
        x="conteo_resenas", 
        y="monto_ventas_usd", 
        color="genero",
        hover_data=["nombre_juego"],
        labels={"conteo_resenas": "Número de Reseñas", "monto_ventas_usd": "Ventas (USD)"},
        title="Mercado Real vs Simulación Actual"
    )
    
    # Añadir el punto de la predicción actual en rojo
    fig.add_scatter(
        x=[sim_reviews], 
        y=[prediccion], 
        mode='markers', 
        marker=dict(size=20, color='red', symbol='star'), 
        name='Tu Simulación'
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("💡 Se necesitan al menos 6 registros históricos para activar las predicciones del modelo.")
