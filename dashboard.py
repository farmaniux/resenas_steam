import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración Pro
st.set_page_config(page_title="Steam-BI Analytics", layout="wide", page_icon="🎮")

# CSS personalizado para mejorar el diseño
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e445e; }
    </style>
    """, unsafe_allow_html=True)

def get_connection():
    try:
        db_url = st.secrets["DB_URI"]
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        return create_engine(db_url, connect_args={
            "sslmode": "require", "prepare_threshold": None, "options": "-c client_encoding=utf8"
        })
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

@st.cache_data(ttl=600)
def load_data():
    engine = get_connection()
    if not engine: return pd.DataFrame()
    query = """
        SELECT h.*, d.nombre, d.subgenero, d.desarrollador 
        FROM hechos_resenas_steam h 
        JOIN dim_juego d ON h.fk_juego = d.appid
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        df['ratio_positividad'] = df['votos_positivos'] / (df['votos_positivos'] + df['votos_negativos'])
        df['ratio_positividad'] = df['ratio_positividad'].fillna(0)
    return df

df = load_data()

if df.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

# --- INTERFAZ ---
st.title("📊 Steam-BI: Intelligence Dashboard")
st.markdown("---")

# Fila 1: KPIs Principales
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Juegos Analizados", len(df['nombre'].unique()))
with c2: st.metric("Ventas Totales Est.", f"${df['monto_ventas_usd'].sum():,.0f}")
with c3: st.metric("Promedio Positividad", f"{df['ratio_positividad'].mean():.1%}")
with c4: st.metric("Total Reseñas", f"{df['conteo_resenas'].sum():,.0f}")

# Separación por Pestañas (Tabs)
tab1, tab2, tab3 = st.tabs(["📈 Análisis de Mercado", "🔮 Simulador IA", "📁 Datos Crudos"])

with tab1:
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("Ventas por Subgénero")
        fig_pie = px.pie(df, values='monto_ventas_usd', names='subgenero', hole=0.4,
                         color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_right:
        st.subheader("Top 10 Juegos por Ingresos")
        top_10 = df.nlargest(10, 'monto_ventas_usd')
        fig_bar = px.bar(top_10, x='monto_ventas_usd', y='nombre', orientation='h',
                         color='monto_ventas_usd', color_continuous_scale='Viridis')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Correlación: Reseñas vs Ingresos")
    fig_scatter = px.scatter(df, x="conteo_resenas", y="monto_ventas_usd", 
                             size="cantidad_descargas", color="subgenero",
                             hover_name="nombre", log_x=True, template="plotly_dark")
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.subheader("Predicción de Éxito Comercial")
    col_sim1, col_sim2 = st.columns([1, 2])
    
    with col_sim1:
        st.info("Ajusta los parámetros para que la IA prediga las ventas.")
        s_reviews = st.number_input("Expectativa de Reseñas", value=5000)
        s_ratio = st.slider("Ratio de Positividad esperado", 0.0, 1.0, 0.8)
        
        # Entrenamiento rápido
        X = df[['conteo_resenas', 'ratio_positividad']]
        y = df['monto_ventas_usd']
        model = RandomForestRegressor(n_estimators=100).fit(X, y)
        pred = model.predict([[s_reviews, s_ratio]])[0]
        
        st.success(f"### Predicción: ${pred:,.2f} USD")

    with col_sim2:
        # Gráfico Comparativo de Predicción
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Bar(name='Promedio Mercado', x=['Ventas'], y=[df['monto_ventas_usd'].mean()]))
        fig_sim.add_trace(go.Bar(name='Tu Proyecto', x=['Ventas'], y=[pred], marker_color='red'))
        fig_sim.update_layout(title="Comparativa: Tu Idea vs Promedio de Mercado")
        st.plotly_chart(fig_sim, use_container_width=True)

with tab3:
    st.subheader("Explorador de Datos")
    st.dataframe(df, use_container_width=True)
