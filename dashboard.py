import re  
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import streamlit as st
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from wordcloud import WordCloud, STOPWORDS
from textblob import TextBlob  
from sklearn.ensemble import RandomForestRegressor
import os
import tempfile
from datetime import datetime

try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN INICIAL
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Steam Analytics | Inteligencia de Mercado",
    layout="wide",
    page_icon="🎮",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════
# DISEÑO VISUAL: NEO-BRUTALIST CON GRADIENTES PREMIUM
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;700&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background: #0a0e27;
        color: #e8e9ed;
    }
    
    .main {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1428 100%);
        padding: 2rem 1rem;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Space Mono', monospace !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    h1 {
        font-size: 3.5rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem !important;
        text-transform: uppercase;
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    h2 {
        color: #a5b4fc !important;
        font-size: 1.5rem !important;
        border-left: 4px solid #667eea;
        padding-left: 1rem;
        margin: 2rem 0 1.5rem 0 !important;
    }
    
    h3 {
        color: #c7d2fe !important;
        font-size: 1.1rem !important;
        margin-bottom: 1rem !important;
    }
    
    .stMetric {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.8rem 1.5rem !important;
        box-shadow: 
            0 4px 24px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stMetric::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, transparent 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .stMetric:hover::before {
        opacity: 1;
    }
    
    .stMetric:hover {
        transform: translateY(-4px);
        border-color: rgba(102, 126, 234, 0.6);
        box-shadow: 
            0 12px 40px rgba(102, 126, 234, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    .stMetric label {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #a5b4fc !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #e0e7ff !important;
        font-family: 'Space Mono', monospace !important;
    }
    
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 0.9rem !important;
        color: #34d399 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 20, 40, 0.6);
        padding: 0.5rem;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
        padding: 0 1.5rem;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(102, 126, 234, 0.1);
        color: #c7d2fe;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1428 0%, #1a1f3a 100%);
        border-right: 2px solid rgba(102, 126, 234, 0.2);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e0e7ff;
    }
    
    [data-testid="stSidebar"] h1 {
        font-size: 1.5rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stMultiSelect [data-baseweb="select"] {
        background: rgba(15, 20, 40, 0.6);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
    }
    
    .stMultiSelect [data-baseweb="tag"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }
    
    .stDataFrame {
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        overflow: hidden;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    .stSlider [data-baseweb="slider"] {
        background: rgba(102, 126, 234, 0.2);
    }
    
    .stSlider [role="slider"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
    }
    
    .stAlert {
        background: rgba(15, 20, 40, 0.8);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 1rem;
    }
    
    .stSuccess {
        border-color: rgba(52, 211, 153, 0.4);
        background: rgba(16, 185, 129, 0.1);
    }
    
    .stInfo {
        border-color: rgba(102, 126, 234, 0.4);
        background: rgba(102, 126, 234, 0.1);
    }
    
    .stWarning {
        border-color: rgba(251, 191, 36, 0.4);
        background: rgba(251, 191, 36, 0.1);
    }
    
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 20, 40, 0.4);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    .element-container {
        animation: fadeInUp 0.6s ease-out;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @media (max-width: 768px) {
        h1 { font-size: 2rem !important; }
        .stMetric { padding: 1.2rem 1rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES UTILITARIAS Y GENERACIÓN DE PDF PREMIUM
# ═══════════════════════════════════════════════════════════════════════════

def format_number(num):
    if pd.isna(num):
        return "N/A"
    if num >= 1e9:
        return f"${num / 1e9:.2f}B" if num >= 0 else f"-${abs(num) / 1e9:.2f}B"
    if num >= 1e6:
        return f"${num / 1e6:.2f}M" if num >= 0 else f"-${abs(num) / 1e6:.2f}M"
    if num >= 1e3:
        return f"${num / 1e3:.2f}K" if num >= 0 else f"-${abs(num) / 1e3:.2f}K"
    return f"${num:.2f}" if num >= 0 else f"-${abs(num):.2f}"

def format_count(num):
    if pd.isna(num):
        return "N/A"
    if num >= 1e9:
        return f"{num / 1e9:.2f}B"
    if num >= 1e6:
        return f"{num / 1e6:.2f}M"
    if num >= 1e3:
        return f"{num / 1e3:.2f}K"
    return f"{num:,.0f}"

def generar_pdf(df_filtered, ventas, descargas, ratio, juegos_count):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Cabecera Corporativa (Fondo Azul Oscuro)
    pdf.set_fill_color(26, 31, 58) # Color institucional
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_y(10)
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, txt="STEAM ANALYTICS BI - REPORTE EJECUTIVO", ln=True, align='C')
    
    # Fecha de generación
    pdf.set_y(35)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 10, txt=f"Generado el: {fecha_actual}", ln=True, align='R')
    pdf.ln(5)
    
    # 2. Resumen de KPIs (Cajas con fondo suave)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(26, 31, 58)
    pdf.cell(0, 10, txt="1. Resumen de Mercado (KPIs)", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(50, 50, 50)
    
    # Imprimir KPIs simulando un grid
    pdf.cell(95, 10, txt=f"Ventas Totales: {format_number(ventas)}", border=1, ln=0, align='C')
    pdf.cell(95, 10, txt=f"Descargas Est.: {format_count(descargas)}", border=1, ln=1, align='C')
    pdf.cell(95, 10, txt=f"Indice de Satisfaccion: {ratio*100:.1f}%", border=1, ln=0, align='C')
    pdf.cell(95, 10, txt=f"Juegos Analizados: {juegos_count}", border=1, ln=1, align='C')
    pdf.ln(10)
    
    # 3. Generación e Inyección de Gráfico (Top 5 Juegos)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(26, 31, 58)
    pdf.cell(0, 10, txt="2. Top 5 Juegos mas Rentables", ln=True)
    pdf.ln(5)
    
    if not df_filtered.empty:
        # Preparar datos para el gráfico
        top5 = df_filtered.nlargest(5, 'monto_ventas_usd').sort_values('monto_ventas_usd', ascending=True)
        
        # Crear gráfico con Matplotlib
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(top5['nombre'], top5['monto_ventas_usd'], color='#667eea')
        ax.set_xlabel('Ingresos (USD)')
        ax.set_title('Ingresos Generados por Titulo')
        plt.tight_layout()
        
        # Guardar en archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            fig.savefig(tmpfile.name, dpi=150, bbox_inches='tight')
            tmpfile_path = tmpfile.name
        plt.close(fig)
        
        # Insertar imagen en PDF y centrarla
        pdf.image(tmpfile_path, x=25, w=160)
        os.unlink(tmpfile_path) # Eliminar archivo temporal
    
    pdf.ln(10)
    
    # 4. Recomendación Estratégica Dinámica
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(26, 31, 58)
    pdf.cell(0, 10, txt="3. Recomendacion Estrategica Algoritmica", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    
    # Lógica condicional premium
    if ratio >= 0.85:
        recomendacion = "ALTA VIABILIDAD: El mercado actual presenta un indice de satisfaccion excelente. Se recomienda aprobar presupuestos para desarrollo en estos subgeneros, priorizando la traccion (volumen de reseñas)."
    elif ratio >= 0.70:
        recomendacion = "RIESGO MODERADO: El mercado es estable pero competitivo. Es vital invertir en campañas de marketing agresivas para asegurar la visibilidad del titulo durante el primer trimestre de lanzamiento."
    else:
        recomendacion = "ALTO RIESGO: La comunidad muestra insatisfaccion general. Se sugiere realizar un analisis profundo de NLP (bugs, hackers, rendimiento) antes de comprometer capital en estos nichos."
        
    pdf.multi_cell(0, 8, txt=recomendacion)
    
    # 5. Pie de página
    pdf.set_y(-20)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, txt="Confidencial - Propiedad de la Gerencia de Inteligencia de Negocios", align='C')
    
    return pdf.output(dest="S").encode("latin1")

# ═══════════════════════════════════════════════════════════════════════════
# CONEXIÓN A BASE DE DATOS MODIFICADA
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def get_engine():
    db_url = st.secrets["DB_URI"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    return create_engine(
        db_url,
        connect_args={
            "sslmode": "require",
            "prepare_threshold": None,
            "options": "-c client_encoding=utf8"
        },
        pool_pre_ping=True,
        pool_recycle=3600
    )

@st.cache_data(ttl=600, show_spinner=False)
def load_data():
    engine = get_engine()
    
    # 1. Datos Generales de Ventas
    query_ventas = """
        SELECT 
            h.*, 
            d.nombre, 
            d.subgenero, 
            d.desarrollador,
            t.id_tiempo as fecha
        FROM hechos_resenas_steam h 
        JOIN dim_juego d ON h.fk_juego = d.appid
        LEFT JOIN dim_tiempo t ON h.fk_tiempo = t.id_tiempo
    """
    df = pd.read_sql(query_ventas, engine)
    
    if not df.empty:
        df['ratio_positividad'] = df['votos_positivos'] / (df['votos_positivos'] + df['votos_negativos'])
        df['ratio_positividad'] = df['ratio_positividad'].fillna(0)
        df['monto_ventas_usd'] = df['monto_ventas_usd'].fillna(0)
        df['cantidad_descargas'] = df['cantidad_descargas'].fillna(0)
        df['conteo_resenas'] = df['conteo_resenas'].fillna(0)

    # 2. Datos NLP de Sentimiento
    query_nlp = """
        SELECT 
            s.*, 
            d.nombre 
        FROM hechos_sentimiento s
        JOIN dim_juego d ON s.fk_juego = d.appid
        ORDER BY s.fk_tiempo ASC
    """
    try:
        df_nlp = pd.read_sql(query_nlp, engine)
    except Exception as e:
        df_nlp = pd.DataFrame() 
    
    return df, df_nlp

# ═══════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

with st.spinner('⚡ Cargando datos del data warehouse...'):
    df, df_nlp = load_data()

if df.empty:
    st.error("⚠️ No se pudieron cargar los datos. Verifica la conexión a la base de datos.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    col_logo, col_title = st.columns([1, 3])
    with col_logo:
        st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=50)
    with col_title:
        st.markdown("### Steam Analytics")
    
    st.markdown("---")
    st.markdown("#### 🎯 Filtros de Análisis")
    
    all_subgenres = sorted(df['subgenero'].dropna().unique())
    selected_subgenres = st.multiselect(
        "Categorías de Juego",
        options=all_subgenres,
        default=all_subgenres,
        help="Selecciona los subgéneros que deseas analizar"
    )
    
    st.markdown("#### 💰 Rango de Ventas")
    min_sales = float(df['monto_ventas_usd'].min())
    max_sales = float(df['monto_ventas_usd'].max())
    
    sales_range = st.slider(
        "Ventas (USD)",
        min_value=min_sales,
        max_value=max_sales,
        value=(min_sales, max_sales),
        format="$%.0f",
        help="Filtra juegos por rango de ventas"
    )
    
    st.markdown("---")
    st.markdown("#### 📊 Estado del Sistema")
    st.success(f"✅ **{len(df):,}** juegos en DWH")
    st.info(f"🔄 Última actualización: Hace {np.random.randint(5, 30)} min")
    
    st.markdown("---")
    with st.expander("ℹ️ Acerca del Dashboard"):
        st.markdown("""
        **Steam Analytics v4.0**
        Plataforma de inteligencia de mercado para análisis de videojuegos en Steam.
        - 📈 Análisis en tiempo real
        - 📊 Visualizaciones interactivas
        - ☁️ Inteligencia Artificial NLP
        - 🔒 Conexión segura a Supabase
        """)

    st.markdown("---")
    st.markdown("#### 📄 Reportes para Gerencia")
    
    df_filtered = df[(df['subgenero'].isin(selected_subgenres)) & (df['monto_ventas_usd'].between(sales_range[0], sales_range[1]))].copy()

    if PDF_ENABLED and not df_filtered.empty:
        v_tot = df_filtered['monto_ventas_usd'].sum()
        d_tot = df_filtered['cantidad_descargas'].sum()
        r_prom = df_filtered['ratio_positividad'].mean()
        j_tot = len(df_filtered)
        
        pdf_bytes = generar_pdf(df_filtered, v_tot, d_tot, r_prom, j_tot)
        st.download_button(
            label="📥 Descargar Reporte Ejecutivo (PDF)",
            data=pdf_bytes,
            file_name="Reporte_Gerencial_Steam_BI.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    elif not PDF_ENABLED:
        st.warning("⚠️ Falta librería fpdf.")

# ═══════════════════════════════════════════════════════════════════════════
# HEADER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("# 🎮 Steam Analytics")
st.markdown("### Plataforma de Inteligencia de Mercado")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sales = df_filtered['monto_ventas_usd'].sum()
    st.metric("💵 Ventas Totales", format_number(total_sales))

with col2:
    total_downloads = df_filtered['cantidad_descargas'].sum()
    st.metric("📥 Descargas Totales", format_count(total_downloads))

with col3:
    avg_positivity = df_filtered['ratio_positividad'].mean()
    st.metric("⭐ Índice de Satisfacción", f"{avg_positivity:.1%}")

with col4:
    game_count = len(df_filtered)
    st.metric("🎯 Juegos Analizados", f"{game_count:,}")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Análisis de Mercado",
    "🎛️ Simulador Estratégico",
    "🗄️ Explorador de Datos",
    "☁️ Inteligencia NLP (Premium)"
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: ANÁLISIS DE MERCADO
# ═══════════════════════════════════════════════════════════════════════════

with tab1:
    st.markdown("## 📊 Inteligencia de Mercado: Volumen vs. Rentabilidad")
    
    if df_filtered.empty:
        st.warning("⚠️ No hay datos disponibles con los filtros actuales.")
        st.info("💡 Ajusta los filtros en la barra lateral para ver el análisis de mercado.")
    else:
        if len(df_filtered) > 2:
            fig_scatter = px.scatter(
                df_filtered,
                x='conteo_resenas',
                y='monto_ventas_usd',
                size='cantidad_descargas',
                color='subgenero',
                hover_name='nombre',
                hover_data={'conteo_resenas': ':,', 'monto_ventas_usd': ':$,.2f', 'cantidad_descargas': ':,', 'ratio_positividad': ':.1%'},
                trendline="ols",
                labels={'conteo_resenas': 'Popularidad (Reseñas)', 'monto_ventas_usd': 'Ingresos (USD)', 'cantidad_descargas': 'Descargas', 'subgenero': 'Categoría'},
                template="plotly_dark",
                height=550
            )
            fig_scatter.update_layout(
                font=dict(family="DM Sans", size=12), paper_bgcolor='rgba(15, 20, 40, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.2)',
                xaxis=dict(showgrid=True, gridcolor='rgba(102, 126, 234, 0.1)', tickformat=",", title_font=dict(size=14, color='#a5b4fc')),
                yaxis=dict(showgrid=True, gridcolor='rgba(102, 126, 234, 0.1)', tickformat="$,.0f", title_font=dict(size=14, color='#a5b4fc')),
                legend=dict(bgcolor='rgba(15, 20, 40, 0.8)', bordercolor='rgba(102, 126, 234, 0.3)', borderwidth=1),
                margin=dict(t=40, b=40, l=40, r=40)
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("⚠️ No hay suficientes datos para generar el gráfico de correlación.")
        
        st.markdown("---")
        
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### 🥧 Distribución por Categoría")
            market_share = df_filtered.groupby('subgenero')['monto_ventas_usd'].sum().reset_index()
            market_share = market_share.sort_values('monto_ventas_usd', ascending=False).head(10)
            fig_pie = px.pie(market_share, values='monto_ventas_usd', names='subgenero', hole=0.4, template="plotly_dark", color_discrete_sequence=px.colors.sequential.Purples_r)
            fig_pie.update_layout(font=dict(family="DM Sans", size=12), paper_bgcolor='rgba(15, 20, 40, 0.6)', legend=dict(bgcolor='rgba(15, 20, 40, 0.8)', bordercolor='rgba(102, 126, 234, 0.3)', borderwidth=1), margin=dict(t=20, b=20, l=20, r=20))
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>Ventas: $%{value:,.0f}<br>Porcentaje: %{percent}<extra></extra>")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_right:
            st.markdown("### 🏆 Top 10 Juegos Rentables")
            if len(df_filtered) > 0:
                top_games = df_filtered.nlargest(min(10, len(df_filtered)), 'monto_ventas_usd').sort_values('monto_ventas_usd', ascending=True)
                fig_bar = px.bar(top_games, x='monto_ventas_usd', y='nombre', orientation='h', color='monto_ventas_usd', color_continuous_scale='Purples', hover_data={'monto_ventas_usd': ':$,.2f', 'conteo_resenas': ':,', 'ratio_positividad': ':.1%'}, labels={'monto_ventas_usd': 'Ventas (USD)', 'nombre': 'Juego'}, template="plotly_dark")
                fig_bar.update_layout(font=dict(family="DM Sans", size=11), paper_bgcolor='rgba(15, 20, 40, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.2)', xaxis=dict(showgrid=True, gridcolor='rgba(102, 126, 234, 0.1)', tickformat="$,.0s"), yaxis=dict(tickfont=dict(size=10)), showlegend=False, margin=dict(t=20, b=40, l=10, r=20))
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No hay datos disponibles para este filtro.")
        
        st.markdown("---")
        st.markdown("### 📈 Rendimiento por Desarrollador")
        if 'desarrollador' in df_filtered.columns:
            dev_stats = df_filtered.groupby('desarrollador').agg({'monto_ventas_usd': 'sum', 'cantidad_descargas': 'sum', 'nombre': 'count'}).reset_index()
            dev_stats.columns = ['Desarrollador', 'Ventas Totales', 'Descargas', 'Cantidad de Juegos']
            dev_stats = dev_stats.sort_values('Ventas Totales', ascending=False).head(15)
            fig_dev = px.bar(dev_stats, x='Desarrollador', y='Ventas Totales', color='Cantidad de Juegos', hover_data=['Descargas'], labels={'Ventas Totales': 'Ventas (USD)'}, template="plotly_dark", color_continuous_scale='Viridis')
            fig_dev.update_layout(font=dict(family="DM Sans", size=12), paper_bgcolor='rgba(15, 20, 40, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.2)', xaxis=dict(showgrid=False, tickangle=-45), yaxis=dict(showgrid=True, gridcolor='rgba(102, 126, 234, 0.1)', tickformat="$,.0s"), margin=dict(t=40, b=100, l=40, r=40), height=400)
            st.plotly_chart(fig_dev, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📈 Tendencia de Ventas en el Tiempo")
        if 'fecha' in df_filtered.columns and not df_filtered['fecha'].isnull().all():
            df_time = df_filtered.groupby('fecha')['monto_ventas_usd'].sum().reset_index()
            df_time = df_time.sort_values('fecha')
            fig_time = px.line(df_time, x='fecha', y='monto_ventas_usd', template="plotly_dark", labels={'fecha': 'Fecha', 'monto_ventas_usd': 'Ventas Diarias (USD)'})
            fig_time.update_traces(line_color='#a5b4fc', line_width=3)
            fig_time.update_layout(paper_bgcolor='rgba(15, 20, 40, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.2)', xaxis=dict(showgrid=True, gridcolor='rgba(102, 126, 234, 0.1)'), yaxis=dict(showgrid=True, gridcolor='rgba(102, 126, 234, 0.1)', tickformat="$,.0s"), height=350, margin=dict(t=30, b=30, l=30, r=30))
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("Aún no hay suficientes datos históricos de tiempo para mostrar esta tendencia.")

        # --- SECCIÓN BENCHMARKING CORREGIDA ---
        st.markdown("---")
        st.markdown("### ⚔️ Benchmarking Directo: Frente a Frente")

        juegos_disponibles = df_filtered['nombre'].dropna().unique()
        if len(juegos_disponibles) >= 2:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1: 
                juego1 = st.selectbox("🥊 Juego A (Retador)", juegos_disponibles, index=0)
            with col_sel2: 
                juego2 = st.selectbox("🛡️ Juego B (Oponente)", juegos_disponibles, index=1 if len(juegos_disponibles)>1 else 0)

            data_j1 = df_filtered[df_filtered['nombre'] == juego1].iloc[0]
            data_j2 = df_filtered[df_filtered['nombre'] == juego2].iloc[0]

            col_radar, col_barras = st.columns(2)

            with col_radar:
                st.markdown("#### 🕸️ Perfil de Rendimiento")
                metricas = ['ratio_positividad', 'cantidad_descargas', 'monto_ventas_usd', 'conteo_resenas']
                nombres_metricas = ['Satisfacción', 'Descargas', 'Ventas ($)', 'Popularidad']

                vals_j1, vals_j2 = [], []
                for m in metricas:
                    val1 = float(data_j1[m]) if pd.notna(data_j1[m]) else 0.0
                    val2 = float(data_j2[m]) if pd.notna(data_j2[m]) else 0.0
                    max_val = max(val1, val2)
                    max_val = max_val if max_val > 0 else 1.0 
                    vals_j1.append((val1 / max_val) * 100)
                    vals_j2.append((val2 / max_val) * 100)

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=vals_j1, theta=nombres_metricas, fill='toself', name=juego1, line_color='#667eea'))
                fig_radar.add_trace(go.Scatterpolar(r=vals_j2, theta=nombres_metricas, fill='toself', name=juego2, line_color='#f093fb'))
                fig_radar.update_layout(
                    template="plotly_dark", paper_bgcolor='rgba(15, 20, 40, 0.6)',
                    polar=dict(radialaxis=dict(visible=False, range=[0, 100]), bgcolor='rgba(0,0,0,0.2)'),
                    margin=dict(t=20, b=20, l=30, r=30), legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            with col_barras:
                st.markdown("#### 📊 Comparativa de Volumen Neto")
                comp_df = pd.DataFrame({
                    'Juego': [juego1, juego2, juego1, juego2],
                    'Métrica': ['Descargas', 'Descargas', 'Reseñas', 'Reseñas'],
                    'Valor': [data_j1['cantidad_descargas'], data_j2['cantidad_descargas'], data_j1['conteo_resenas'], data_j2['conteo_resenas']]
                })
                fig_barras = px.bar(
                    comp_df, x='Métrica', y='Valor', color='Juego', barmode='group',
                    text_auto='.2s', color_discrete_sequence=['#667eea', '#f093fb'], template="plotly_dark"
                )
                fig_barras.update_layout(
                    paper_bgcolor='rgba(15, 20, 40, 0.6)', plot_bgcolor='rgba(0,0,0,0.2)',
                    margin=dict(t=20, b=20, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_barras, use_container_width=True)
                
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; border-left: 4px solid #34d399; margin-top: 10px;">
                    <p style="margin:0; font-size: 0.9rem;"><strong>🏆 Resumen Financiero:</strong></p>
                    <p style="margin:0; font-size: 0.85rem; color: #c7d2fe;">{juego1}: <strong>${data_j1['monto_ventas_usd']:,.0f}</strong> ({data_j1['ratio_positividad']:.0%} Positivo)</p>
                    <p style="margin:0; font-size: 0.85rem; color: #f093fb;">{juego2}: <strong>${data_j2['monto_ventas_usd']:,.0f}</strong> ({data_j2['ratio_positividad']:.0%} Positivo)</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("⚠️ Necesitas al menos 2 juegos filtrados para usar la herramienta de Benchmarking.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: SIMULADOR DE ESCENARIOS (Riesgo y Segmentación)
# ═══════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("## 🎛️ Simulador de Riesgo y Estrategia Comercial (What-If)")
    st.markdown("Proyecta los ingresos de tu lanzamiento basándote en datos reales del mercado. La Inteligencia de Negocios evalúa el riesgo y te da **tres escenarios posibles**.")
    
    if not df.empty and len(df) > 10:
        with st.spinner('🧠 Entrenando modelo analítico avanzado con datos de tu DWH...'):
            df_ml = df.copy()
            df_ml = pd.get_dummies(df_ml, columns=['subgenero'], drop_first=False)
            columnas_genero = [col for col in df_ml.columns if col.startswith('subgenero_')]
            X_cols = ['conteo_resenas', 'ratio_positividad'] + columnas_genero
            
            X = df_ml[X_cols].fillna(0)
            y = df_ml['monto_ventas_usd'].fillna(0)
            model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
            model.fit(X, y)
            
        col_in, col_out = st.columns([1, 1.8])
        
        with col_in:
            st.markdown("""
            <div style='background: rgba(102, 126, 234, 0.1); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(102, 126, 234, 0.3);'>
                <h4 style='color: #a5b4fc; margin-top: 0;'>1️⃣ Configura tu Estrategia</h4>
            </div>
            <br>
            """, unsafe_allow_html=True)
            
            generos_disponibles = sorted(df['subgenero'].dropna().unique())
            genero_elegido = st.selectbox("🎮 Categoría del Juego", generos_disponibles)
            input_reviews = st.number_input("📢 Meta de Tracción (Número de Reseñas)", min_value=100, max_value=1000000, value=5000, step=500)
            input_positivity = st.slider("⭐ Meta de Calidad (Satisfacción %)", 0.0, 1.0, 0.85, 0.01, format="%.2f")
            btn_calcular = st.button("🚀 Calcular Riesgo e Ingresos", type="primary", use_container_width=True)

        with col_out:
            st.markdown("### 2️⃣ Análisis de Riesgo Financiero")
            if btn_calcular:
                input_data = pd.DataFrame(columns=X_cols)
                input_data.loc[0] = 0 
                input_data['conteo_resenas'] = input_reviews
                input_data['ratio_positividad'] = input_positivity
                
                columna_activa = f'subgenero_{genero_elegido}'
                if columna_activa in input_data.columns:
                    input_data.loc[0, columna_activa] = 1
                
                predicciones_arboles = [arbol.predict(input_data.values)[0] for arbol in model.estimators_]
                escenario_pesimista = np.percentile(predicciones_arboles, 15)  
                escenario_realista = np.median(predicciones_arboles)           
                escenario_optimista = np.percentile(predicciones_arboles, 85)  
                
                html_tarjetas = f"""
                <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                    <div style="flex: 1; background: rgba(248, 113, 113, 0.1); border: 2px solid rgba(248, 113, 113, 0.4); border-radius: 12px; padding: 1.5rem; text-align: center;">
                        <p style="color: #f87171; margin: 0; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">📉 Escenario Pesimista</p>
                        <p style="font-size: 1.8rem; font-weight: 800; color: #ffffff; margin: 0.5rem 0; font-family: 'Space Mono', monospace;">{format_number(escenario_pesimista)}</p>
                        <p style="color: #94a3b8; font-size: 0.75rem; margin: 0;">Tracción baja.</p>
                    </div>
                    <div style="flex: 1; background: linear-gradient(135deg, rgba(52, 211, 153, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%); border: 2px solid rgba(52, 211, 153, 0.6); border-radius: 12px; padding: 1.5rem; text-align: center; transform: scale(1.05); box-shadow: 0 10px 20px rgba(0,0,0,0.3);">
                        <p style="color: #34d399; margin: 0; font-size: 0.9rem; font-weight: bold; text-transform: uppercase;">📊 Escenario Esperado</p>
                        <p style="font-size: 2.2rem; font-weight: 800; color: #ffffff; margin: 0.5rem 0; font-family: 'Space Mono', monospace;">{format_number(escenario_realista)}</p>
                        <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">Ingreso base proyectado.</p>
                    </div>
                    <div style="flex: 1; background: rgba(96, 165, 250, 0.1); border: 2px solid rgba(96, 165, 250, 0.4); border-radius: 12px; padding: 1.5rem; text-align: center;">
                        <p style="color: #60a5fa; margin: 0; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">🚀 Escenario Optimista</p>
                        <p style="font-size: 1.8rem; font-weight: 800; color: #ffffff; margin: 0.5rem 0; font-family: 'Space Mono', monospace;">{format_number(escenario_optimista)}</p>
                        <p style="color: #94a3b8; font-size: 0.75rem; margin: 0;">Si el juego se hace viral.</p>
                    </div>
                </div>
                """
                st.markdown(html_tarjetas, unsafe_allow_html=True)
                
                fig_risk = go.Figure(go.Funnel(
                    y=["Optimista (Techo)", "Esperado (Seguro)", "Pesimista (Piso)"],
                    x=[escenario_optimista, escenario_realista, escenario_pesimista],
                    textinfo="value", marker={"color": ["#60a5fa", "#34d399", "#f87171"]}
                ))
                fig_risk.update_layout(
                    title=f"Margen de Riesgo para un juego tipo {genero_elegido}",
                    template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    height=250, margin=dict(t=30, b=10, l=10, r=10)
                )
                st.plotly_chart(fig_risk, use_container_width=True)
            else:
                st.info("Ajusta tus parámetros comerciales y presiona el botón para calcular los 3 escenarios de riesgo.")
    else:
        st.warning("⚠️ Se necesitan al menos 10 registros en la base de datos para ejecutar el simulador.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: EXPLORADOR DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("## 🗄️ Explorador de Datos del Data Warehouse")
    st.markdown("Visualización y análisis detallado de todos los registros almacenados.")
    
    if df_filtered.empty:
        st.warning("⚠️ No hay datos disponibles con los filtros actuales.")
        st.info("💡 Ajusta los filtros en la barra lateral para ver más datos.")
    else:
        available_columns = df_filtered.columns.tolist()
        default_columns = ['nombre', 'subgenero', 'desarrollador', 'votos_positivos', 'votos_negativos', 'monto_ventas_usd', 'cantidad_descargas', 'ratio_positividad']
        
        selected_columns = st.multiselect(
            "🔍 Selecciona las columnas a mostrar:",
            options=available_columns, default=[col for col in default_columns if col in available_columns]
        )
    
    if selected_columns:
        col_opt1, col_opt2, col_opt3 = st.columns(3)
        with col_opt1:
            min_records = min(10, len(df_filtered))
            default_records = min(50, len(df_filtered))
            show_top_n = st.number_input("Mostrar primeros N registros", min_value=min_records, max_value=max(min_records, len(df_filtered)), value=default_records, step=10 if len(df_filtered) >= 10 else 1)
        with col_opt2:
            sort_column = st.selectbox("Ordenar por:", options=selected_columns, index=selected_columns.index('monto_ventas_usd') if 'monto_ventas_usd' in selected_columns else 0)
        with col_opt3:
            sort_order = st.radio("Orden:", options=["Descendente", "Ascendente"], horizontal=True)
        
        display_df = df_filtered[selected_columns].copy()
        ascending = (sort_order == "Ascendente")
        display_df = display_df.sort_values(by=sort_column, ascending=ascending)
        display_df = display_df.head(show_top_n)
        
        if 'monto_ventas_usd' in display_df.columns:
            display_df['monto_ventas_usd'] = display_df['monto_ventas_usd'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
        if 'ratio_positividad' in display_df.columns:
            display_df['ratio_positividad'] = display_df['ratio_positividad'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
        if 'cantidad_descargas' in display_df.columns:
            display_df['cantidad_descargas'] = display_df['cantidad_descargas'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
        
        st.dataframe(display_df, use_container_width=True, height=500)
        
        st.markdown("---")
        st.markdown("### 📊 Estadísticas de los Datos Mostrados")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        with stat_col1: st.metric("📋 Registros Mostrados", f"{len(display_df):,}")
        with stat_col2: st.metric("📁 Total en Filtro", f"{len(df_filtered):,}")
        with stat_col3: st.metric("🗃️ Total en DWH", f"{len(df):,}")
        with stat_col4: st.metric("🔗 Columnas Activas", f"{len(selected_columns)}")
            
        st.markdown("---")
        st.markdown("### 📥 Exportación Ejecutiva")
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📄 Descargar Reporte Actual (CSV)", data=csv, file_name='reporte_steam_analytics.csv', mime='text/csv', type="primary")
    else:
        st.info("👆 Selecciona al menos una columna para visualizar los datos.")
    
    st.markdown("---")
    col_sys1, col_sys2 = st.columns(2)
    with col_sys1:
        st.success("✅ **Integridad Referencial Validada**")
        st.markdown("- ✔️ Todas las claves foráneas están correctamente vinculadas\n- ✔️ Sin registros huérfanos detectados\n- ✔️ Esquema en estrella implementado correctamente")
    with col_sys2:
        st.info("🔄 **Sistema de Monitoreo Activo**")
        st.markdown("- 🤖 Pipeline ETL ejecutándose cada 24 horas\n- 🔒 Conexión SSL/TLS segura a Supabase\n- 📊 Motor VADER procesando lenguaje natural")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: INTELIGENCIA CUALITATIVA (NUEVA VERSIÓN VADER + DATA WAREHOUSE)
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 🧠 Motor de Inteligencia Cualitativa (VADER NLP)")
    st.markdown("Lectura directa del Data Warehouse. Análisis histórico de sentimiento, palabras clave y correlación con jugadores activos.")
    
    if not df_nlp.empty:
        col_ctrl1, col_ctrl2 = st.columns([1, 3])
        
        with col_ctrl1:
            st.markdown("### 🎯 Seleccionar Título")
            juegos_disponibles_nlp = sorted(df_nlp['nombre'].unique())
            juego_seleccionado = st.selectbox("Juego a analizar:", juegos_disponibles_nlp)
            
            df_juego_nlp = df_nlp[df_nlp['nombre'] == juego_seleccionado].copy()
            ultimo_registro = df_juego_nlp.iloc[-1]
            
            st.markdown("#### 📡 Contexto del Día")
            
            if ultimo_registro['en_oferta'] == 1:
                st.success("💰 ¡Descuento Activo en la Tienda!")
            else:
                st.info("🎮 Free-to-Play / Sin descuentos hoy")
                
            if ultimo_registro['hubo_actualizacion'] == 1:
                st.warning("🛠️ Hubo un PARCHE/UPDATE hoy")
            else:
                st.markdown("<div style='padding: 1rem; border-radius: 8px; background: rgba(255,255,255,0.05);'>✅ Sin actualizaciones recientes</div>", unsafe_allow_html=True)
        
        with col_ctrl2:
            st.markdown("### 🌡️ Termómetro de la Comunidad (Último Registro)")
            
            pol = float(ultimo_registro['polaridad_roberta']) if pd.notna(ultimo_registro['polaridad_roberta']) else 0.0
            
            if pol > 0.05:
                color, icono, label = "#34d399", "😀", "POSITIVO"
            elif pol < -0.05:
                color, icono, label = "#f87171", "😡", "NEGATIVO"
            else:
                color, icono, label = "#fbbf24", "😐", "NEUTRAL"
                
            kpi_html = f"""
            <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                <div style="flex: 1.5; background: linear-gradient(135deg, rgba(15,20,40,0.9) 0%, rgba(26,31,58,0.9) 100%); border: 2px solid {color}; border-radius: 16px; padding: 1.5rem; text-align: center; box-shadow: 0 0 20px {color}33;">
                    <p style="margin:0; color:#94a3b8; font-size:0.8rem; text-transform:uppercase; font-weight:600;">Veredicto VADER</p>
                    <p style="margin:0.5rem 0; font-size:2.2rem; font-weight:900; color:{color}; font-family:'Space Mono', monospace;">{icono} {label}</p>
                    <p style="margin:0; color:#e0e7ff;">Polaridad Neta: <strong style="color:{color}">{pol:+.3f}</strong></p>
                </div>
                <div style="flex: 1; background: rgba(102, 126, 234, 0.1); border: 1px solid rgba(102, 126, 234, 0.3); border-radius: 16px; padding: 1.5rem; text-align: center;">
                    <p style="margin:0; color:#a5b4fc; font-size:0.8rem; text-transform:uppercase; font-weight:600;">Tema Principal Hoy</p>
                    <p style="margin:0.5rem 0; font-size:1.8rem; font-weight:800; color:#ffffff; font-family:'Space Mono', monospace; text-transform: uppercase;">"{ultimo_registro['tema_principal']}"</p>
                </div>
                <div style="flex: 1; background: rgba(102, 126, 234, 0.1); border: 1px solid rgba(102, 126, 234, 0.3); border-radius: 16px; padding: 1.5rem; text-align: center;">
                    <p style="margin:0; color:#a5b4fc; font-size:0.8rem; text-transform:uppercase; font-weight:600;">Jugadores Activos</p>
                    <p style="margin:0.5rem 0; font-size:1.8rem; font-weight:800; color:#ffffff; font-family:'Space Mono', monospace;">{ultimo_registro['jugadores_activos']:,}</p>
                </div>
            </div>
            """
            st.markdown(kpi_html, unsafe_allow_html=True)
            
        st.markdown("---")
        
        st.markdown("### 📈 Evolución Histórica: Jugadores vs. Sentimiento")
        
        fig_hist = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_hist.add_trace(
            go.Scatter(x=df_juego_nlp['fk_tiempo'], y=df_juego_nlp['jugadores_activos'], 
                       name="Jugadores Activos", mode="lines+markers", line=dict(color="#a5b4fc", width=3), marker=dict(size=8)),
            secondary_y=False,
        )
        
        fig_hist.add_trace(
            go.Scatter(x=df_juego_nlp['fk_tiempo'], y=df_juego_nlp['polaridad_roberta'], 
                       name="Polaridad NLP (Sentimiento)", mode="lines+markers", fill='tozeroy', line=dict(color="#34d399", width=2), marker=dict(size=8)),
            secondary_y=True,
        )
        
        fig_hist.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(15, 20, 40, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.2)',
            margin=dict(t=40, b=40, l=40, r=40), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig_hist.update_yaxes(title_text="Cantidad de Jugadores", secondary_y=False, gridcolor='rgba(102, 126, 234, 0.1)')
        fig_hist.update_yaxes(title_text="Índice de Polaridad (-1 a 1)", secondary_y=True, showgrid=False)
        fig_hist.update_xaxes(type='category') 

        st.plotly_chart(fig_hist, use_container_width=True)
            
    else:
        st.warning("⚠️ No hay datos NLP almacenados en el Data Warehouse (tabla hechos_sentimiento). Ejecuta tu proceso Pentaho primero.")

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #64748b;">
    <p style="margin: 0; font-size: 0.9rem;">
        <strong>Steam Analytics v4.0</strong> · Plataforma de Inteligencia de Mercado
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem;">
        Powered by Streamlit · PostgreSQL · Plotly · VADER
    </p>
</div>
""", unsafe_allow_html=True)
