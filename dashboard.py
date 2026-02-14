import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Steam-BI Analytics", layout="wide")
st.title("🎮 Steam-BI: Predicción y Análisis de Mercado")

# 2. Conexión a la Base de Datos
# Usamos st.secrets para que funcione en la nube sin exponer contraseñas
# Sustituye tu función get_connection actual por esta:
def get_connection():
    try:
        db_url = st.secrets["DB_URI"]
        # Pequeño truco: si la URL empieza con postgres:// lo cambiamos a postgresql://
        # para que SQLAlchemy no se queje
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        # Agregamos connect_args para evitar timeouts
        engine = create_engine(db_url, connect_args={'sslmode':'require'})
        return engine
    except Exception as e:
        st.error(f"Error de configuración: {e}")
        return None

# 3. Carga y Procesamiento de Datos
@st.cache_data
def load_data():
    engine = get_connection()
    if engine is None:
        return pd.DataFrame()

    # Consulta que une tus tablas (ajusta si tus nombres de tabla son diferentes)
    query = """
    SELECT 
        h.cantidad_descargas,
        h.monto_ventas_usd,
        h.votos_positivos,
        h.votos_negativos,
        h.conteo_resenas,
        d.nombre_juego,
        d.genero,
        t.fecha_hoy
    FROM hechos_resenas_steam h
    JOIN dim_juego d ON h.fk_juego = d.id_juego
    JOIN dim_tiempo t ON h.fk_tiempo = t.id_tiempo
    """
    try:
        df = pd.read_sql(query, engine)
        # Crear variable de 'Ratio de Positividad' para el modelo
        df['ratio_positividad'] = df['votos_positivos'] / (df['votos_positivos'] + df['votos_negativos'])
        df = df.fillna(0)
        return df
    except Exception as e:
        st.error(f"Error al leer la base de datos: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No hay datos cargados. Verifica la conexión.")
    st.stop()

# 4. Barra Lateral: Simulador
st.sidebar.header("🔮 Simulador de Predicciones")
st.sidebar.write("Ajusta los valores para predecir ventas futuras:")

# Sliders para que el usuario interactúe
sim_reviews = st.sidebar.slider("Total de Reseñas", 
                                min_value=100, 
                                max_value=int(df['conteo_resenas'].max()*1.5), 
                                value=1000)

sim_ratio = st.sidebar.slider("Ratio de Positividad (%)", 
                              min_value=0.0, 
                              max_value=1.0, 
                              value=0.85)

# 5. Modelo de Machine Learning (Random Forest)
# Entrenamos el modelo EN VIVO con los datos actuales
X = df[['conteo_resenas', 'ratio_positividad']]
y = df['monto_ventas_usd']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
precision = model.score(X_test, y_test)

# Predicción basada en el input del usuario
prediccion_ventas = model.predict([[sim_reviews, sim_ratio]])[0]

# 6. Visualización (KPIs y Gráficos)
col1, col2, col3 = st.columns(3)
col1.metric("Precisión del Modelo (R²)", f"{precision:.2%}")
col2.metric("Ventas Predichas (USD)", f"${prediccion_ventas:,.2f}")
col3.metric("Datos Analizados", f"{len(df)} registros")

st.subheader("📊 Dispersión: Reseñas vs Ventas Reales")
fig = px.scatter(df, x="conteo_resenas", y="monto_ventas_usd", 
                 color="genero", hover_data=["nombre_juego"],
                 title="Comparativa: Mercado Real vs Tu Simulación")

# Agregamos el punto rojo que representa la predicción actual
fig.add_scatter(x=[sim_reviews], y=[prediccion_ventas], mode='markers', 
                marker=dict(size=25, color='red'), name='Tu Predicción')

st.plotly_chart(fig, use_container_width=True)
