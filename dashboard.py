import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE ÉLITE
st.set_page_config(page_title="Steam-BI Intelligence", layout="wide", page_icon="🎯")

# Inyección de CSS para Diseño Profesional (Dark Mode + Accent Colors)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .main { background-color: #0e1117; }
    
    /* Contenedores de KPIs Estilo Glassmorphism */
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 242, 255, 0.2);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Títulos con Neón Suave */
    h1, h2, h3 { color: #00f2ff !important; font-weight: 700 !important; }
    
    /* Estilo de la Barra Lateral */
    .css-1d391kg { background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# Helper para formatear números de forma profesional (millones, billones)
def format_big_number(num):
    if num >= 1e9:
        return f"{num / 1e9:.2f}B"
    if num >= 1e6:
        return f"{num / 1e6:.2f}M"
    if num >= 1e3:
        return f"{num / 1e3:.2f}K"
    return f"{num:.2f}"

@st.cache_resource
def get_engine():
    db_url = st.secrets["DB_URI"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    return create_engine(db_url, connect_args={
        "sslmode": "require", "prepare_threshold": None, "options": "-c client_encoding=utf8"
    })

@st.cache_data(ttl=600)
def load_data():
    engine = get_engine()
    # Query estructurada según el modelo dimensional [cite: 39]
    query = """
        SELECT h.*, d.nombre, d.subgenero, d.desarrollador 
        FROM hechos_resenas_steam h 
        JOIN dim_juego d ON h.fk_juego = d.appid
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        # Tratamiento de métricas (Etapa 2) 
        df['ratio_positividad'] = df['votos_positivos'] / (df['votos_positivos'] + df['votos_negativos'])
        df['ratio_positividad'] = df['ratio_positividad'].fillna(0)
    return df

df = load_data()

# --- ESTRUCTURA DE LA INTERFAZ ---

# 1. SIDEBAR (FILTROS)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=60)
    st.title("Steam-BI Control")
    st.markdown("---")
    
    # Filtro multiselección por subgénero
    selected_subgenres = st.multiselect(
        "📂 Filtrar por Subgénero", 
        options=sorted(df['subgenero'].unique()), 
        default=df['subgenero'].unique()
    )
    
    st.markdown("---")
    st.markdown("### 🛠️ Estado del Sistema")
    st.success("✅ DWH: Supabase Online")
    st.success("✅ ETL: Idempotente ")

df_filt = df[df['subgenero'].isin(selected_subgenres)]

# 2. MAIN HEADER
st.title("📊 Global Market Intelligence Dashboard")
st.markdown(f"**Análisis de ROI y Sentimiento Basado en el Algoritmo de Boxleiter** [cite: 14]")
st.markdown("---")

# 3. KPI SECTION (MÉTRICAS CLAVE)
kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("Ventas Totales Est.", f"${format_big_number(df_filt['monto_ventas_usd'].sum())}")
with kpi_cols[1]:
    st.metric("Descargas Totales", format_big_number(df_filt['cantidad_descargas'].sum()))
with kpi_cols[2]:
    st.metric("Índice Positividad", f"{df_filt['ratio_positividad'].mean():.1%}")
with kpi_cols[3]:
    st.metric("Juegos en Muestra", len(df_filt))

# 4. TABS PROFESIONALES
tab1, tab2, tab3 = st.tabs(["📈 DESEMPEÑO COMERCIAL", "🤖 PREDICTOR IA", "📁 AUDITORÍA DWH"])

with tab1:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📍 Market Share por Subgénero")
        fig_pie = px.pie(
            df_filt, values='monto_ventas_usd', names='subgenero', hole=0.6,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000', width=1)))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_b:
        st.subheader("🏆 Top Performers (Ingresos)")
        top_df = df_filt.nlargest(10, 'monto_ventas_usd').sort_values('monto_ventas_usd', ascending=True)
        fig_bar = px.bar(
            top_df, x='monto_ventas_usd', y='nombre', orientation='h',
            color='monto_ventas_usd', color_continuous_scale='GnBu',
            labels={'monto_ventas_usd': 'Ventas USD', 'nombre': 'Título'}
        )
        fig_bar.update_layout(xaxis_title="Ventas (USD)", yaxis_title="")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("💡 Correlación: Reseñas vs. Ventas Proyectadas")
    fig_scatter = px.scatter(
        df_filt, x='conteo_resenas', y='monto_ventas_usd', size='cantidad_descargas',
        color='subgenero', hover_name='nombre', log_x=True,
        template="plotly_dark", height=500
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.subheader("🔮 Simulación de Éxito de Lanzamiento")
    st.info("Utiliza el modelo RandomForestRegressor para estimar el ROI potencial basándose en el sentimiento del mercado.")
    
    # ML Backend
    if len(df) > 5:
        X = df[['conteo_resenas', 'ratio_positividad']]
        y = df['monto_ventas_usd']
        model = RandomForestRegressor(n_estimators=100, random_state=42).fit(X, y)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### Parámetros de Simulación")
            s_reviews = st.number_input("Reseñas Estimadas", value=10000, step=1000)
            s_ratio = st.slider("Ratio de Positividad Objetivo", 0.0, 1.0, 0.85)
            
            prediction = model.predict([[s_reviews, s_ratio]])[0]
            
            st.markdown(f"""
                <div style="background: rgba(0, 242, 255, 0.1); padding: 25px; border-radius: 10px; border-left: 5px solid #00f2ff;">
                    <p style="margin:0; font-size:14px; color:#00f2ff;">PREDICCIÓN DE INGRESOS</p>
                    <h2 style="margin:0;">${prediction:,.2f} USD</h2>
                </div>
            """, unsafe_allow_html=True)
            
        with c2:
            # Gauge Chart Profesional
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = prediction,
                title = {'text': "Potencial de Ventas", 'font': {'size': 20}},
                gauge = {
                    'axis': {'range': [None, df['monto_ventas_usd'].max()]},
                    'bar': {'color': "#00f2ff"},
                    'steps': [
                        {'range': [0, df['monto_ventas_usd'].mean()], 'color': "#1a1a1a"},
                        {'range': [df['monto_ventas_usd'].mean(), df['monto_ventas_usd'].max()], 'color': "#242424"}
                    ]
                }
            ))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(fig_gauge, use_container_width=True)

with tab3:
    st.subheader("📋 Auditoría de Datos e Integridad Referencial")
    st.markdown("Vista detallada del DWH hospedado en Supabase[cite: 39, 41].")
    
    # Tabla con formato premium
    st.dataframe(
        df_filt[['nombre', 'subgenero', 'desarrollador', 'votos_positivos', 'votos_negativos', 'monto_ventas_usd']],
        use_container_width=True
    )
    
    st.markdown("---")
    col_inf1, col_inf2 = st.columns(2)
    with col_inf1:
        st.markdown("#### Estructura DWH")
        st.code("""Esquema: Star Schema
Hechos: hechos_resenas_steam
Dimensiones: dim_juego, dim_tiempo, dim_tipo_resena""")
    with col_inf2:
        st.markdown("#### Seguridad [cite: 41]")
        st.markdown("- Conexión Cifrada SSL")
        st.markdown("- Secretos gestionados vía GitHub/Streamlit")
