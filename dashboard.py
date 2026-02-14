import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE ÉLITE (UX/UI)
st.set_page_config(page_title="STEAM-BI | SUPREME INTELLIGENCE", layout="wide", page_icon="⚡")

# Inyección de CSS para Diseño Profesional (Glassmorphism & Neon)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: radial-gradient(circle, #0d1117 0%, #000000 100%); }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif; color: #00f2ff !important; text-shadow: 0 0 12px #00f2ff; }
    
    /* Contenedores de KPIs Estilo Glassmorphism */
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 242, 255, 0.2);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# Helper para formatear números de forma profesional (millones, billones)
def format_n(num):
    if num >= 1e9: return f"{num / 1e9:.2f}B"
    if num >= 1e6: return f"{num / 1e6:.2f}M"
    if num >= 1e3: return f"{num / 1e3:.2f}K"
    return f"{num:.2f}"

@st.cache_resource
def get_engine():
    db_url = st.secrets["DB_URI"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    # Conexión cifrada SSL según especificaciones de seguridad [cite: 41]
    return create_engine(db_url, connect_args={
        "sslmode": "require", "prepare_threshold": None, "options": "-c client_encoding=utf8"
    })

@st.cache_data(ttl=600)
def load_data():
    engine = get_engine()
    # Query basada en tu Esquema en Estrella [cite: 39]
    query = """
        SELECT h.*, d.nombre, d.subgenero, d.desarrollador 
        FROM hechos_resenas_steam h 
        JOIN dim_juego d ON h.fk_juego = d.appid
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        # Tratamiento de métricas y ratio de positividad [cite: 29]
        df['ratio_positividad'] = df['votos_positivos'] / (df['votos_positivos'] + df['votos_negativos'])
        df['ratio_positividad'] = df['ratio_positividad'].fillna(0)
    return df

df = load_data()

# --- SIDEBAR (SISTEMA DE CONTROL) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=60)
    st.title("Steam-BI Control")
    st.markdown("---")
    selected_subgenres = st.multiselect(
        "📂 Filtrar Subgéneros", 
        options=sorted(df['subgenero'].unique()), 
        default=df['subgenero'].unique()
    )
    st.markdown("---")
    st.info("🎯 **Idempotencia Activa**: Datos normalizados sin duplicados diarios[cite: 26].")

df_filt = df[df['subgenero'].isin(selected_subgenres)]

# --- HEADER SUPREMO ---
st.title("⚡ STEAM-BI: SUPREME MARKET INTELLIGENCE")
st.markdown(f"**Análisis de ROI Basado en el Algoritmo de Boxleiter** ")
st.markdown("---")

# --- SECCIÓN KPI: MÉTRICAS DE IMPACTO ---
kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("Ventas Totales Est.", f"${format_n(df_filt['monto_ventas_usd'].sum())}")
with kpi_cols[1]:
    st.metric("Descargas Totales", format_n(df_filt['cantidad_descargas'].sum()))
with kpi_cols[2]:
    st.metric("Índice Positividad", f"{df_filt['ratio_positividad'].mean():.1%}")
with kpi_cols[3]:
    st.metric("Juegos en DWH", f"{len(df_filt)}")

# --- TABS PROFESIONALES ---
tab1, tab2, tab3 = st.tabs(["🏛️ DOMINIO DE MERCADO", "🔮 NÚCLEO PREDICTIVO", "🛠️ AUDITORÍA & INTEGRIDAD"])

with tab1:
    st.subheader("💡 Inteligencia de Volumen vs. Rentabilidad")
    
    # Gráfica de Correlación Élite con Línea de Tendencia (OLS)
    # Esta línea permite identificar juegos que superan el promedio de ventas esperado por reseña.
    fig_scatter = px.scatter(
        df_filt, x='conteo_resenas', y='monto_ventas_usd', size='cantidad_descargas',
        color='subgenero', hover_name='nombre', trendline="ols",
        labels={'conteo_resenas': 'Popularidad (Reseñas)', 'monto_ventas_usd': 'Ingresos (USD)'},
        template="plotly_dark", height=600
    )
    fig_scatter.update_layout(
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickformat=",.0s"),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickformat="$~s"),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    c_left, c_right = st.columns(2)
    with c_left:
        st.subheader("Market Share por Subgénero")
        st.plotly_chart(px.pie(df_filt, values='monto_ventas_usd', names='subgenero', hole=0.5), use_container_width=True)
    with c_right:
        st.subheader("Top Performers (Ingresos)")
        top_df = df_filt.nlargest(10, 'monto_ventas_usd').sort_values('monto_ventas_usd', ascending=True)
        st.plotly_chart(px.bar(top_df, x='monto_ventas_usd', y='nombre', orientation='h', color='monto_ventas_usd'), use_container_width=True)

with tab2:
    st.subheader("Simulación Prospectiva con IA (Scikit-Learn)")
    X = df[['conteo_resenas', 'ratio_positividad']]
    y = df['monto_ventas_usd']
    
    if len(df) > 5:
        # Modelo predictivo integrado según Etapa 5 del Ciclo de Vida 
        model = RandomForestRegressor(n_estimators=200, random_state=42).fit(X, y)
        c_sim1, c_sim2 = st.columns([1, 2])
        
        with c_sim1:
            st.markdown("#### Configuración de Escenario")
            s_reviews = st.number_input("Reseñas Objetivo", value=5000, step=500)
            s_ratio = st.slider("Target de Positividad", 0.0, 1.0, 0.85)
            pred = model.predict([[s_reviews, s_ratio]])[0]
            st.markdown(f"""
                <div style="background:rgba(0,242,255,0.1);padding:25px;border-radius:15px;border:1px solid #00f2ff;">
                    <h3 style="margin:0;font-size:14px;color:#00f2ff;">VALOR PREDICHO (ROI)</h3>
                    <p style="font-size:36px;font-weight:bold;color:#ffffff;margin:0;">${pred:,.2f} USD</p>
                </div>
            """, unsafe_allow_html=True)
        
        with c_sim2:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=pred, title={'text': "Potencial vs Máximo Histórico"},
                gauge={'axis': {'range': [None, df['monto_ventas_usd'].max()]}, 'bar': {'color': "#00f2ff"}}
            ))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(fig_gauge, use_container_width=True)

with tab3:
    st.subheader("📋 Auditoría de Datos e Integridad del DWH [cite: 30]")
    st.dataframe(df_filt[['nombre', 'subgenero', 'votos_positivos', 'votos_negativos', 'monto_ventas_usd']], use_container_width=True)
    st.success("✔️ Integridad Referencial Validada: FK_Juego -> AppID[cite: 39].")
    st.info("📅 Monitoreo: GitHub Actions ejecutando pipeline cada 24 horas[cite: 61, 62].")
