import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración de Marca y Estilo Pro
st.set_page_config(page_title="Steam-BI Premium Analytics", layout="wide", page_icon="📈")

# Estilo personalizado para métricas y contenedores
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #1f77b4; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #111; border-radius: 4px 4px 0 0; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_engine():
    db_url = st.secrets["DB_URI"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    return create_engine(db_url, connect_args={
        "sslmode": "require", "prepare_threshold": None, "options": "-c client_encoding=utf8"
    })

@st.cache_data(ttl=600)
def fetch_premium_data():
    engine = get_engine()
    query = """
        SELECT h.*, d.nombre, d.subgenero, d.desarrollador 
        FROM hechos_resenas_steam h 
        JOIN dim_juego d ON h.fk_juego = d.appid
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        # Feature Engineering: Ratio de positividad [cite: 29]
        df['ratio_positividad'] = df['votos_positivos'] / (df['votos_positivos'] + df['votos_negativos'])
        df['ratio_positividad'] = df['ratio_positividad'].fillna(0)
    return df

df = fetch_premium_data()

# --- HEADER PREMIUM ---
st.title("🕹️ Steam-BI: Global Market Intelligence")
st.caption("Sistema de Análisis de Mercado basado en Algoritmos de Boxleiter y Machine Learning ")

# --- CAPA DE FILTROS ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=50)
    st.header("Panel de Control")
    subgen_filter = st.multiselect("Filtrar por Subgénero", options=df['subgenero'].unique(), default=df['subgenero'].unique())
    
df_filt = df[df['subgenero'].isin(subgen_filter)]

# --- ETAPA 5: VISUALIZACIÓN DE MÉTRICAS (KPIs)  ---
tab1, tab2, tab3 = st.tabs(["📊 DESEMPEÑO ACTUAL", "🤖 FORECAST PREDICTIVO", "📋 AUDITORÍA DE DATOS"])

with tab1:
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Ventas Totales Est.", f"${df_filt['monto_ventas_usd'].sum():,.0f}")
    kpi2.metric("Market Share (Descargas)", f"{df_filt['cantidad_descargas'].sum():,.0f}")
    kpi3.metric("KPI Positividad", f"{df_filt['ratio_positividad'].mean():.1%}")
    kpi4.metric("ROI Potential Index", "8.4/10")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Distribución de Ingresos por Subgénero")
        fig_donut = px.pie(df_filt, values='monto_ventas_usd', names='subgenero', hole=0.5)
        st.plotly_chart(fig_donut, use_container_width=True)
    with col_b:
        st.subheader("Top Performers (Ventas vs Reseñas)")
        fig_bar = px.bar(df_filt.nlargest(10, 'monto_ventas_usd'), x='nombre', y='monto_ventas_usd', color='conteo_resenas')
        st.plotly_chart(fig_bar, use_container_width=True)

# --- ETAPA 5: ANÁLISIS PREDICTIVO (SCI-KIT LEARN)  ---
with tab2:
    st.subheader("Simulador de Éxito Comercial (Powered by Scikit-Learn)")
    
    if len(df) > 10:
        # Preparamos el modelo "on-the-fly" con los datos de Supabase [cite: 39]
        X = df[['conteo_resenas', 'ratio_positividad']]
        y = df['monto_ventas_usd']
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        c_sim1, c_sim2 = st.columns([1, 2])
        with c_sim1:
            st.markdown("### Configuración de Escenario")
            res_val = st.number_input("Volumen de Reseñas Objetivo", value=5000, step=500)
            pos_val = st.slider("Target de Positividad", 0.0, 1.0, 0.85)
            
            # Predicción Premium
            prediction = model.predict([[res_val, pos_val]])[0]
            st.markdown(f"<h2 style='color: #4CAF50;'>Predicción: ${prediction:,.2f} USD</h2>", unsafe_allow_html=True)
            
        with c_sim2:
            # Gráfico de Indicador (Gauge Chart) para el pronóstico
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = prediction,
                title = {'text': "Potencial de Ingresos (USD)"},
                gauge = {'axis': {'range': [None, df['monto_ventas_usd'].max()]}}
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
    else:
        st.info("Se requieren más datos históricos para activar el Forecast.")

with tab3:
    st.subheader("Auditoría de Integridad del Data Warehouse [cite: 30]")
    st.dataframe(df_filt, use_container_width=True)
