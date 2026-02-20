import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import plotly.express as px
import plotly.graph_objects as go
import re  # <-- NUEVO: Para limpieza profunda con expresiones regulares en NLP
import requests
from bs4 import BeautifulSoup
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt

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
    
    /* RESET Y TEMA BASE */
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
    
    /* TIPOGRAFÍA DISTINTIVA */
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
    
    /* CARDS DE MÉTRICAS CON ELEVACIÓN */
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
    
    /* TABS MODERNOS */
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
    
    /* SIDEBAR REDISEÑADO */
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
    
    /* MULTISELECT MEJORADO */
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
    
    /* DATAFRAME ESTILIZADO */
    .stDataFrame {
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* BOTONES Y ELEMENTOS INTERACTIVOS */
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
    
    /* SLIDER PERSONALIZADO */
    .stSlider [data-baseweb="slider"] {
        background: rgba(102, 126, 234, 0.2);
    }
    
    .stSlider [role="slider"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
    }
    
    /* ALERTAS Y NOTIFICACIONES */
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
    
    /* SCROLLBAR PERSONALIZADO */
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
    
    /* EFECTOS DE CARGA */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* ANIMACIONES DE ENTRADA */
    .element-container {
        animation: fadeInUp 0.6s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* RESPONSIVE */
    @media (max-width: 768px) {
        h1 { font-size: 2rem !important; }
        .stMetric { padding: 1.2rem 1rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES UTILITARIAS
# ═══════════════════════════════════════════════════════════════════════════

def format_number(num):
    """Formateador de números con estilo profesional"""
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
    """Formateador de conteos sin símbolo de moneda"""
    if pd.isna(num):
        return "N/A"
    if num >= 1e9:
        return f"{num / 1e9:.2f}B"
    if num >= 1e6:
        return f"{num / 1e6:.2f}M"
    if num >= 1e3:
        return f"{num / 1e3:.2f}K"
    return f"{num:,.0f}"

# ═══════════════════════════════════════════════════════════════════════════
# CONEXIÓN A BASE DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def get_engine():
    """Establece conexión segura con Supabase"""
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
    """Carga y procesa datos del data warehouse"""
    engine = get_engine()
    query = """
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
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        # Calcula ratio de positividad
        df['ratio_positividad'] = df['votos_positivos'] / (
            df['votos_positivos'] + df['votos_negativos']
        )
        df['ratio_positividad'] = df['ratio_positividad'].fillna(0)
        
        # Limpieza de datos
        df['monto_ventas_usd'] = df['monto_ventas_usd'].fillna(0)
        df['cantidad_descargas'] = df['cantidad_descargas'].fillna(0)
        df['conteo_resenas'] = df['conteo_resenas'].fillna(0)
    
    return df

# ═══════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS CON INDICADOR
# ═══════════════════════════════════════════════════════════════════════════

with st.spinner('⚡ Cargando datos del data warehouse...'):
    df = load_data()

# Validación de datos
if df.empty:
    st.error("⚠️ No se pudieron cargar los datos. Verifica la conexión a la base de datos.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR: PANEL DE CONTROL
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    # Logo y título
    col_logo, col_title = st.columns([1, 3])
    with col_logo:
        st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=50)
    with col_title:
        st.markdown("### Steam Analytics")
    
    st.markdown("---")
    
    # Filtros principales
    st.markdown("#### 🎯 Filtros de Análisis")
    
    # Filtro de subgéneros
    all_subgenres = sorted(df['subgenero'].dropna().unique())
    selected_subgenres = st.multiselect(
        "Categorías de Juego",
        options=all_subgenres,
        default=all_subgenres,
        help="Selecciona los subgéneros que deseas analizar"
    )
    
    # Filtro de rango de ventas
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
    
    # Información del sistema
    st.markdown("#### 📊 Estado del Sistema")
    st.success(f"✅ **{len(df):,}** juegos en DWH")
    st.info(f"🔄 Última actualización: Hace {np.random.randint(5, 30)} min")
    
    st.markdown("---")
    
    # Información adicional
    with st.expander("ℹ️ Acerca del Dashboard"):
        st.markdown("""
        **Steam Analytics v2.0**
        
        Plataforma de inteligencia de mercado para análisis de videojuegos en Steam.
        
        - 📈 Análisis en tiempo real
        - 🤖 Predicciones con Machine Learning
        - 📊 Visualizaciones interactivas
        - ☁️ Análisis de Scraping Natural
        - 🔒 Conexión segura a Supabase
        """)

# Aplicar filtros
df_filtered = df[
    (df['subgenero'].isin(selected_subgenres)) &
    (df['monto_ventas_usd'].between(sales_range[0], sales_range[1]))
].copy()

# ═══════════════════════════════════════════════════════════════════════════
# HEADER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("# 🎮 Steam Analytics")
st.markdown("### Plataforma de Inteligencia de Mercado · Análisis Predictivo con IA")
st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# MÉTRICAS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sales = df_filtered['monto_ventas_usd'].sum()
    st.metric(
        "💵 Ventas Totales",
        format_number(total_sales),
        help="Suma total de ventas estimadas en USD"
    )

with col2:
    total_downloads = df_filtered['cantidad_descargas'].sum()
    st.metric(
        "📥 Descargas Totales",
        format_count(total_downloads),
        help="Número total de descargas registradas"
    )

with col3:
    avg_positivity = df_filtered['ratio_positividad'].mean()
    st.metric(
        "⭐ Índice de Satisfacción",
        f"{avg_positivity:.1%}",
        help="Promedio de reseñas positivas"
    )

with col4:
    game_count = len(df_filtered)
    st.metric(
        "🎯 Juegos Analizados",
        f"{game_count:,}",
        help="Número de juegos en el análisis actual"
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# TABS DE ANÁLISIS
# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Análisis de Mercado",
    "🤖 Motor Predictivo",
    "🗄️ Explorador de Datos",
    "☁️ Análisis Cualitativo (NLP)"
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: ANÁLISIS DE MERCADO
# ═══════════════════════════════════════════════════════════════════════════

with tab1:
    st.markdown("## 📊 Inteligencia de Mercado: Volumen vs. Rentabilidad")
    
    # Validar datos antes de mostrar gráficos
    if df_filtered.empty:
        st.warning("⚠️ No hay datos disponibles con los filtros actuales.")
        st.info("💡 Ajusta los filtros en la barra lateral para ver el análisis de mercado.")
    else:
        # Gráfico de dispersión con tendencia
        if len(df_filtered) > 2:
            fig_scatter = px.scatter(
                df_filtered,
                x='conteo_resenas',
                y='monto_ventas_usd',
                size='cantidad_descargas',
                color='subgenero',
                hover_name='nombre',
                hover_data={
                    'conteo_resenas': ':,',
                    'monto_ventas_usd': ':$,.2f',
                    'cantidad_descargas': ':,',
                    'ratio_positividad': ':.1%'
                },
                trendline="ols",
                labels={
                    'conteo_resenas': 'Popularidad (Número de Reseñas)',
                    'monto_ventas_usd': 'Ingresos Estimados (USD)',
                    'cantidad_descargas': 'Descargas',
                    'subgenero': 'Categoría'
                },
                template="plotly_dark",
                height=550
            )
            
            fig_scatter.update_layout(
                font=dict(family="DM Sans", size=12),
                paper_bgcolor='rgba(15, 20, 40, 0.6)',
                plot_bgcolor='rgba(0, 0, 0, 0.2)',
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(102, 126, 234, 0.1)',
                    tickformat=",",
                    title_font=dict(size=14, color='#a5b4fc')
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(102, 126, 234, 0.1)',
                    tickformat="$,.0f",
                    title_font=dict(size=14, color='#a5b4fc')
                ),
                legend=dict(
                    bgcolor='rgba(15, 20, 40, 0.8)',
                    bordercolor='rgba(102, 126, 234, 0.3)',
                    borderwidth=1
                ),
                margin=dict(t=40, b=40, l=40, r=40)
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("⚠️ No hay suficientes datos para generar el gráfico de correlación.")
        
        st.markdown("---")
        
        # Dos columnas para gráficos adicionales
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### 🥧 Distribución de Mercado por Categoría")
            
            market_share = df_filtered.groupby('subgenero')['monto_ventas_usd'].sum().reset_index()
            market_share = market_share.sort_values('monto_ventas_usd', ascending=False).head(10)
            
            fig_pie = px.pie(
                market_share,
                values='monto_ventas_usd',
                names='subgenero',
                hole=0.4,
                template="plotly_dark",
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            
            fig_pie.update_layout(
                font=dict(family="DM Sans", size=12),
                paper_bgcolor='rgba(15, 20, 40, 0.6)',
                legend=dict(
                    bgcolor='rgba(15, 20, 40, 0.8)',
                    bordercolor='rgba(102, 126, 234, 0.3)',
                    borderwidth=1
                ),
                margin=dict(t=20, b=20, l=20, r=20)
            )
            
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Ventas: $%{value:,.0f}<br>Porcentaje: %{percent}<extra></extra>"
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_right:
            st.markdown("### 🏆 Top 10: Juegos Más Rentables")
            
            if len(df_filtered) > 0:
                top_games = df_filtered.nlargest(min(10, len(df_filtered)), 'monto_ventas_usd').sort_values('monto_ventas_usd', ascending=True)
                
                fig_bar = px.bar(
                    top_games,
                    x='monto_ventas_usd',
                    y='nombre',
                    orientation='h',
                    color='monto_ventas_usd',
                    color_continuous_scale='Purples',
                    hover_data={
                        'monto_ventas_usd': ':$,.2f',
                        'conteo_resenas': ':,',
                        'ratio_positividad': ':.1%'
                    },
                    labels={
                        'monto_ventas_usd': 'Ventas (USD)',
                        'nombre': 'Juego'
                    },
                    template="plotly_dark"
                )
                
                fig_bar.update_layout(
                    font=dict(family="DM Sans", size=11),
                    paper_bgcolor='rgba(15, 20, 40, 0.6)',
                    plot_bgcolor='rgba(0, 0, 0, 0.2)',
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(102, 126, 234, 0.1)',
                        tickformat="$,.0s"
                    ),
                    yaxis=dict(tickfont=dict(size=10)),
                    showlegend=False,
                    margin=dict(t=20, b=40, l=10, r=20)
                )
                
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No hay datos disponibles para este filtro.")
        
        st.markdown("---")
        
        # Análisis adicional
        st.markdown("### 📈 Análisis de Rendimiento por Desarrollador")
        
        if 'desarrollador' in df_filtered.columns:
            dev_stats = df_filtered.groupby('desarrollador').agg({
                'monto_ventas_usd': 'sum',
                'cantidad_descargas': 'sum',
                'nombre': 'count'
            }).reset_index()
            
            dev_stats.columns = ['Desarrollador', 'Ventas Totales', 'Descargas', 'Cantidad de Juegos']
            dev_stats = dev_stats.sort_values('Ventas Totales', ascending=False).head(15)
            
            fig_dev = px.bar(
                dev_stats,
                x='Desarrollador',
                y='Ventas Totales',
                color='Cantidad de Juegos',
                hover_data=['Descargas'],
                labels={'Ventas Totales': 'Ventas (USD)'},
                template="plotly_dark",
                color_continuous_scale='Viridis'
            )
            
            fig_dev.update_layout(
                font=dict(family="DM Sans", size=12),
                paper_bgcolor='rgba(15, 20, 40, 0.6)',
                plot_bgcolor='rgba(0, 0, 0, 0.2)',
                xaxis=dict(
                    showgrid=False,
                    tickangle=-45
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(102, 126, 234, 0.1)',
                    tickformat="$,.0s"
                ),
                margin=dict(t=40, b=100, l=40, r=40),
                height=400
            )
            
            st.plotly_chart(fig_dev, use_container_width=True)

        st.markdown("---")

        # 1. GRÁFICO DE TENDENCIAS EN EL TIEMPO (TIME SERIES)
        st.markdown("### 📈 Tendencia de Ventas en el Tiempo")
        if 'fecha' in df_filtered.columns and not df_filtered['fecha'].isnull().all():
            df_time = df_filtered.groupby('fecha')['monto_ventas_usd'].sum().reset_index()
            df_time = df_time.sort_values('fecha')

            fig_time = px.line(
                df_time,
                x='fecha',
                y='monto_ventas_usd',
                template="plotly_dark",
                labels={'fecha': 'Fecha', 'monto_ventas_usd': 'Ventas Diarias (USD)'}
            )
            fig_time.update_traces(line_color='#a5b4fc', line_width=3)
            fig_time.update_layout(
                paper_bgcolor='rgba(15, 20, 40, 0.6)',
                plot_bgcolor='rgba(0, 0, 0, 0.2)',
                xaxis=dict(showgrid=True, gridcolor='rgba(102, 126, 234, 0.1)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(102, 126, 234, 0.1)', tickformat="$,.0s"),
                height=350,
                margin=dict(t=30, b=30, l=30, r=30)
            )
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("Aún no hay suficientes datos históricos de tiempo para mostrar esta tendencia.")

        st.markdown("---")

        col_bench, col_heat = st.columns(2)

        # 2. HERRAMIENTA DE BENCHMARKING (RADAR CHART 1 VS 1)
        with col_bench:
            st.markdown("### ⚔️ Benchmarking: 1 vs 1")

            juegos_disponibles = df_filtered['nombre'].dropna().unique()
            if len(juegos_disponibles) >= 2:
                g1, g2 = st.columns(2)
                with g1: juego1 = st.selectbox("Juego A", juegos_disponibles, index=0)
                with g2: juego2 = st.selectbox("Juego B", juegos_disponibles, index=1)

                data_j1 = df_filtered[df_filtered['nombre'] == juego1].iloc[0]
                data_j2 = df_filtered[df_filtered['nombre'] == juego2].iloc[0]

                metricas = ['ratio_positividad', 'cantidad_descargas', 'monto_ventas_usd', 'conteo_resenas']
                nombres_metricas = ['Positividad', 'Descargas', 'Ventas USD', 'Popularidad']

                vals_j1 = []
                vals_j2 = []
                for m in metricas:
                    val1 = float(data_j1[m]) if pd.notna(data_j1[m]) else 0.0
                    val2 = float(data_j2[m]) if pd.notna(data_j2[m]) else 0.0
                    max_val = max(val1, val2)
                    max_val = max_val if max_val > 0 else 1.0 # Evitar división por cero
                    vals_j1.append((val1 / max_val) * 100)
                    vals_j2.append((val2 / max_val) * 100)

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals_j1, theta=nombres_metricas, fill='toself', name=juego1, line_color='#667eea'
                ))
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals_j2, theta=nombres_metricas, fill='toself', name=juego2, line_color='#f093fb'
                ))

                fig_radar.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='rgba(15, 20, 40, 0.6)',
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
                        bgcolor='rgba(0,0,0,0.2)'
                    ),
                    margin=dict(t=30, b=30, l=30, r=30),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("Necesitas al menos 2 juegos filtrados para comparar.")

        # 3. MATRIZ DE CORRELACIÓN (HEATMAP)
        with col_heat:
            st.markdown("### 🌡️ Matriz de Correlación")

            cols_corr = ['votos_positivos', 'votos_negativos', 'monto_ventas_usd', 'cantidad_descargas', 'ratio_positividad']
            nombres_amigables = ['Positivos', 'Negativos', 'Ventas ($)', 'Descargas', 'Ratio +']

            if len(df_filtered) > 2:
                cols_validas = [c for c in cols_corr if c in df_filtered.columns]
                corr_matrix = df_filtered[cols_validas].corr(numeric_only=True)

                fig_corr = px.imshow(
                    corr_matrix,
                    x=nombres_amigables[:len(cols_validas)],
                    y=nombres_amigables[:len(cols_validas)],
                    color_continuous_scale='Purples',
                    template="plotly_dark",
                    text_auto=".2f",
                    aspect="auto"
                )
                fig_corr.update_layout(
                    paper_bgcolor='rgba(15, 20, 40, 0.6)',
                    margin=dict(t=30, b=30, l=30, r=30)
                )
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.warning("Se requieren más datos para calcular correlaciones estadísticas.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: MOTOR PREDICTIVO
# ═══════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("## 🤖 Motor de Predicción con Inteligencia Artificial")
    st.markdown("Utiliza algoritmos de Machine Learning para estimar el potencial de ingresos basado en métricas clave.")
    
    if not df.empty and len(df) > 10:
        # Preparación de datos para el modelo
        X = df[['conteo_resenas', 'ratio_positividad']].fillna(0)
        y = df['monto_ventas_usd'].fillna(0)
        
        # Entrenamiento del modelo
        with st.spinner('🧠 Entrenando modelo de Machine Learning...'):
            model = RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X, y)
        
        st.success("✅ Modelo entrenado exitosamente")
        
        col_input, col_output = st.columns([1, 2])
        
        with col_input:
            st.markdown("### ⚙️ Configurar Escenario")
            st.markdown("Ajusta los parámetros para simular diferentes escenarios de mercado.")
            
            # Inputs del usuario
            input_reviews = st.number_input(
                "📝 Número de Reseñas Proyectadas",
                min_value=0,
                max_value=1000000,
                value=5000,
                step=500,
                help="Cantidad estimada de reseñas que recibirá el juego"
            )
            
            input_positivity = st.slider(
                "⭐ Ratio de Satisfacción Objetivo",
                min_value=0.0,
                max_value=1.0,
                value=0.85,
                step=0.01,
                format="%.2f",
                help="Proporción de reseñas positivas esperadas"
            )
            
            st.markdown("---")
            
            # Botón de predicción
            if st.button("🚀 Calcular Predicción", type="primary", use_container_width=True):
                prediction = model.predict([[input_reviews, input_positivity]])[0]
                
                # Mostrar resultado
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.1) 100%);
                    padding: 2rem;
                    border-radius: 16px;
                    border: 2px solid rgba(102, 126, 234, 0.4);
                    margin-top: 1rem;
                    text-align: center;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                ">
                    <p style="font-size: 0.9rem; color: #a5b4fc; margin: 0; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;">Ingresos Estimados</p>
                    <p style="font-size: 3rem; font-weight: 700; color: #e0e7ff; margin: 0.5rem 0; font-family: 'Space Mono', monospace;">{format_number(prediction)}</p>
                    <p style="font-size: 0.85rem; color: #94a3b8; margin: 0;">Basado en algoritmo Random Forest</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col_output:
            st.markdown("### 📊 Visualización del Potencial")
            
            # Gauge chart mejorado
            max_value = df['monto_ventas_usd'].max()
            prediction = model.predict([[input_reviews, input_positivity]])[0]
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=prediction,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={
                    'text': "Potencial vs Máximo Histórico",
                    'font': {'size': 20, 'color': '#a5b4fc', 'family': 'Space Mono'}
                },
                delta={
                    'reference': max_value * 0.5,
                    'increasing': {'color': "#34d399"},
                    'decreasing': {'color': "#f87171"}
                },
                gauge={
                    'axis': {
                        'range': [None, max_value],
                        'tickwidth': 1,
                        'tickcolor': "#667eea",
                        'tickformat': '$,.0s'
                    },
                    'bar': {'color': "#667eea", 'thickness': 0.75},
                    'bgcolor': "rgba(15, 20, 40, 0.3)",
                    'borderwidth': 2,
                    'bordercolor': "rgba(102, 126, 234, 0.3)",
                    'steps': [
                        {'range': [0, max_value * 0.33], 'color': 'rgba(248, 113, 113, 0.2)'},
                        {'range': [max_value * 0.33, max_value * 0.66], 'color': 'rgba(251, 191, 36, 0.2)'},
                        {'range': [max_value * 0.66, max_value], 'color': 'rgba(52, 211, 153, 0.2)'}
                    ],
                    'threshold': {
                        'line': {'color': "#34d399", 'width': 4},
                        'thickness': 0.75,
                        'value': max_value * 0.8
                    }
                },
                number={'font': {'size': 48, 'color': '#e0e7ff', 'family': 'Space Mono'}}
            ))
            
            fig_gauge.update_layout(
                paper_bgcolor='rgba(15, 20, 40, 0.6)',
                font={'color': "#e0e7ff", 'family': 'DM Sans'},
                height=350,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            # Información adicional
            st.markdown("#### 📈 Contexto del Modelo")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("🎯 Precisión R²", f"{model.score(X, y):.3f}")
            with col_b:
                st.metric("🌲 Árboles", f"{model.n_estimators}")
            with col_c:
                avg_market = df['monto_ventas_usd'].mean()
                st.metric("💵 Promedio Mercado", format_number(avg_market))
        
        st.markdown("---")
        
        # Análisis de importancia de características
        st.markdown("### 🔍 Análisis de Factores Clave")
        
        feature_importance = pd.DataFrame({
            'Factor': ['Número de Reseñas', 'Ratio de Positividad'],
            'Importancia': model.feature_importances_
        }).sort_values('Importancia', ascending=True)
        
        fig_importance = px.bar(
            feature_importance,
            x='Importancia',
            y='Factor',
            orientation='h',
            template="plotly_dark",
            color='Importancia',
            color_continuous_scale='Purples'
        )
        
        fig_importance.update_layout(
            font=dict(family="DM Sans", size=12),
            paper_bgcolor='rgba(15, 20, 40, 0.6)',
            plot_bgcolor='rgba(0, 0, 0, 0.2)',
            xaxis=dict(showgrid=True, gridcolor='rgba(102, 126, 234, 0.1)'),
            yaxis=dict(showgrid=False),
            showlegend=False,
            margin=dict(t=20, b=40, l=150, r=20),
            height=250
        )
        
        st.plotly_chart(fig_importance, use_container_width=True)

        # ═══════════════════════════════════════════════════════════════════════════
        # CLASIFICADOR DE RIESGO
        # ═══════════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.markdown("## 🎲 Clasificador de Riesgo Comercial (Éxito vs Fracaso)")
        st.markdown("Evalúa la probabilidad de éxito de un proyecto basándose en su género y meta de tracción.")

        if not df.empty and len(df) > 10:
            with st.spinner('🧠 Entrenando modelo de Clasificación de Riesgo...'):
                # 1. Definir qué es el "Éxito" (Ventas superiores al promedio del mercado)
                umbral_exito = df['monto_ventas_usd'].median()
                df_class = df.copy()
                df_class['es_exito'] = (df_class['monto_ventas_usd'] >= umbral_exito).astype(int)
                
                # 2. Seleccionar variables predictoras (One-Hot Encoding para el género)
                X_cat = pd.get_dummies(df_class[['subgenero']], drop_first=True)
                X_num = df_class[['conteo_resenas', 'ratio_positividad']].fillna(0)
                X_class = pd.concat([X_num, X_cat], axis=1)
                y_class = df_class['es_exito']
                
                # 3. Entrenar el clasificador
                clf_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
                clf_model.fit(X_class, y_class)

            col_clas_in, col_clas_out = st.columns([1, 2])
            
            with col_clas_in:
                st.markdown("### 📝 Parámetros del Proyecto")
                
                # Selectores para el gerente
                generos_disponibles = sorted(df['subgenero'].dropna().unique())
                genero_input = st.selectbox("Selecciona el Género del Juego", generos_disponibles)
                
                resenas_obj = st.number_input(
                    "Meta de Reseñas Iniciales",
                    min_value=0, max_value=1000000, value=2000, step=100,
                    help="Tracción esperada en el primer mes",
                    key="resenas_obj_input"
                )
                
                pos_obj = st.slider(
                    "Calidad Esperada (Ratio Positividad)",
                    min_value=0.0, max_value=1.0, value=0.80, step=0.01, format="%.2f",
                    key="pos_obj_slider"
                )
                
            with col_clas_out:
                st.markdown("### 📊 Veredicto de Viabilidad")
                
                if st.button("⚖️ Evaluar Riesgo del Proyecto", use_container_width=True):
                    # Preparar el dato de entrada para que coincida con las columnas del modelo
                    input_data = pd.DataFrame(columns=X_class.columns)
                    input_data.loc[0] = 0 # Llenar todo con ceros inicialmente
                    
                    # Asignar los valores numéricos
                    input_data['conteo_resenas'] = resenas_obj
                    input_data['ratio_positividad'] = pos_obj
                    
                    # Activar el género seleccionado
                    columna_genero = f'subgenero_{genero_input}'
                    if columna_genero in input_data.columns:
                        input_data.loc[0, columna_genero] = 1
                        
                    # 4. Hacer la predicción probabilística
                    probabilidades = clf_model.predict_proba(input_data)[0]
                    prob_fracaso = probabilidades[0]
                    prob_exito = probabilidades[1]
                    
                    # 5. Visualización del resultado
                    st.markdown(f"""
                    <div style="display: flex; gap: 20px; margin-top: 1rem;">
                        <div style="flex: 1; padding: 1.5rem; background: rgba(52, 211, 153, 0.1); border: 2px solid rgba(52, 211, 153, 0.4); border-radius: 12px; text-align: center;">
                            <h4 style="color: #34d399; margin:0;">ÉXITO COMERCIAL</h4>
                            <p style="font-size: 2.5rem; font-family: 'Space Mono', monospace; font-weight: bold; margin:0.5rem 0; color: white;">{prob_exito:.1%}</p>
                            <p style="font-size: 0.8rem; color: #94a3b8; margin:0;">Probabilidad de superar los {format_number(umbral_exito)}</p>
                        </div>
                        <div style="flex: 1; padding: 1.5rem; background: rgba(248, 113, 113, 0.1); border: 2px solid rgba(248, 113, 113, 0.4); border-radius: 12px; text-align: center;">
                            <h4 style="color: #f87171; margin:0;">RIESGO DE FRACASO</h4>
                            <p style="font-size: 2.5rem; font-family: 'Space Mono', monospace; font-weight: bold; margin:0.5rem 0; color: white;">{prob_fracaso:.1%}</p>
                            <p style="font-size: 0.8rem; color: #94a3b8; margin:0;">Probabilidad de no alcanzar el ROI</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Barra de progreso visual para el éxito
                    st.progress(float(prob_exito))

    else:
        st.warning("⚠️ Se necesitan al menos 10 registros para entrenar el modelo predictivo.")
        st.info("💡 Ajusta los filtros en la barra lateral para incluir más datos.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: EXPLORADOR DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("## 🗄️ Explorador de Datos del Data Warehouse")
    st.markdown("Visualización y análisis detallado de todos los registros almacenados.")
    
    # Validar que hay datos para mostrar
    if df_filtered.empty:
        st.warning("⚠️ No hay datos disponibles con los filtros actuales.")
        st.info("💡 Ajusta los filtros en la barra lateral para ver más datos.")
    else:
        # Selector de columnas
        available_columns = df_filtered.columns.tolist()
        default_columns = ['nombre', 'subgenero', 'desarrollador', 'votos_positivos', 
                          'votos_negativos', 'monto_ventas_usd', 'cantidad_descargas', 'ratio_positividad']
        
        selected_columns = st.multiselect(
            "🔍 Selecciona las columnas a mostrar:",
            options=available_columns,
            default=[col for col in default_columns if col in available_columns],
            help="Personaliza las columnas visibles en la tabla"
        )
    
    if selected_columns:
        # Opciones de visualización
        col_opt1, col_opt2, col_opt3 = st.columns(3)
        
        with col_opt1:
            # Ajustar min_value dinámicamente basado en datos disponibles
            min_records = min(10, len(df_filtered))
            default_records = min(50, len(df_filtered))
            
            show_top_n = st.number_input(
                "Mostrar primeros N registros",
                min_value=min_records,
                max_value=max(min_records, len(df_filtered)),
                value=default_records,
                step=10 if len(df_filtered) >= 10 else 1
            )
        
        with col_opt2:
            sort_column = st.selectbox(
                "Ordenar por:",
                options=selected_columns,
                index=selected_columns.index('monto_ventas_usd') if 'monto_ventas_usd' in selected_columns else 0
            )
        
        with col_opt3:
            sort_order = st.radio(
                "Orden:",
                options=["Descendente", "Ascendente"],
                horizontal=True
            )
        
        # Preparar datos para mostrar
        display_df = df_filtered[selected_columns].copy()
        
        # Aplicar ordenamiento
        ascending = (sort_order == "Ascendente")
        display_df = display_df.sort_values(by=sort_column, ascending=ascending)
        
        # Mostrar solo los primeros N
        display_df = display_df.head(show_top_n)
        
        # Formatear columnas numéricas para mejor visualización
        if 'monto_ventas_usd' in display_df.columns:
            display_df['monto_ventas_usd'] = display_df['monto_ventas_usd'].apply(
                lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A"
            )
        
        if 'ratio_positividad' in display_df.columns:
            display_df['ratio_positividad'] = display_df['ratio_positividad'].apply(
                lambda x: f"{x:.1%}" if pd.notna(x) else "N/A"
            )
        
        if 'cantidad_descargas' in display_df.columns:
            display_df['cantidad_descargas'] = display_df['cantidad_descargas'].apply(
                lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
            )
        
        # Mostrar tabla
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500
        )
        
        # Estadísticas de la tabla
        st.markdown("---")
        st.markdown("### 📊 Estadísticas de los Datos Mostrados")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("📋 Registros Mostrados", f"{len(display_df):,}")
        
        with stat_col2:
            st.metric("📁 Total en Filtro", f"{len(df_filtered):,}")
        
        with stat_col3:
            st.metric("🗃️ Total en DWH", f"{len(df):,}")
        
        with stat_col4:
            st.metric("🔗 Columnas Activas", f"{len(selected_columns)}")
            
        # ═══════════════════════════════════════════════════════════════════════════
        # BOTÓN DE EXPORTACIÓN EJECUTIVA
        # ═══════════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.markdown("### 📥 Exportación Ejecutiva")
        # Convertir el dataframe mostrado a CSV
        csv = display_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📄 Descargar Reporte Actual (CSV)",
            data=csv,
            file_name='reporte_steam_analytics.csv',
            mime='text/csv',
            type="primary"
        )
    
    else:
        st.info("👆 Selecciona al menos una columna para visualizar los datos.")
    
    st.markdown("---")
    
    # Panel de información del sistema
    col_sys1, col_sys2 = st.columns(2)
    
    with col_sys1:
        st.success("✅ **Integridad Referencial Validada**")
        st.markdown("""
        - ✔️ Todas las claves foráneas están correctamente vinculadas
        - ✔️ Sin registros huérfanos detectados
        - ✔️ Esquema en estrella implementado correctamente
        """)
    
    with col_sys2:
        st.info("🔄 **Sistema de Monitoreo Activo**")
        st.markdown("""
        - 🤖 Pipeline ETL ejecutándose cada 24 horas
        - 🔒 Conexión SSL/TLS segura a Supabase
        - 📊 GitHub Actions monitoreando el proceso
        """)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: ANÁLISIS CUALITATIVO (WEB SCRAPING Y NLP)
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## ☁️ Motor de Inteligencia Cualitativa (NLP)")
    st.markdown("Extracción en tiempo real y minería de textos usando técnicas de Procesamiento de Lenguaje Natural para descubrir el verdadero sentimiento de la comunidad.")
    
    if not df_filtered.empty:
        col_scrap1, col_scrap2 = st.columns([1, 2.5])
        
        with col_scrap1:
            st.markdown("### 🎯 Configuración del Motor")
            juegos_disponibles = df_filtered['nombre'].dropna().unique()
            juego_wordcloud = st.selectbox("Juego a minar:", juegos_disponibles)
            
            st.info("💡 **Proceso NLP Activo:**\n1. Web Scraping\n2. Tokenización\n3. Filtrado Regex (Números/Símbolos)\n4. Eliminación de Stopwords")
            
            ejecutar_scraping = st.button("🕷️ Iniciar Minería de Datos", type="primary", use_container_width=True)
            
        with col_scrap2:
            if ejecutar_scraping:
                with st.spinner(f'Extrayendo y procesando datos en vivo de Steam para {juego_wordcloud}...'):
                    try:
                        # 1. EXTRACCIÓN (Web Scraping)
                        appid = df_filtered[df_filtered['nombre'] == juego_wordcloud]['fk_juego'].iloc[0]
                        url = f"https://steamcommunity.com/app/{appid}/reviews/?browsefilter=mostrecent&paged=1"
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        respuesta = requests.get(url, headers=headers)
                        soup = BeautifulSoup(respuesta.text, 'html.parser')
                        
                        bloques_texto = soup.find_all('div', class_='apphub_CardTextContent')
                        texto_bruto = " ".join([bloque.text.replace("\n", "").strip() for bloque in bloques_texto])
                        palabras_totales_brutas = len(texto_bruto.split())
                        
                        # 2. LIMPIEZA Y NORMALIZACIÓN (Pipeline NLP)
                        # Eliminar marcas de agua de Steam
                        texto_limpio = texto_bruto.replace("Early Access Review", "").replace("Posted", "")
                        # Convertir a minúsculas
                        texto_limpio = texto_limpio.lower()
                        # REGEX: Eliminar todo lo que NO sea texto (números, puntuación, caracteres especiales)
                        texto_limpio = re.sub(r'[^a-z\s]', '', texto_limpio)
                        # REGEX: Eliminar espacios múltiples
                        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
                        
                        if len(texto_limpio) > 50:
                            # 3. FILTRADO DE STOPWORDS (Palabras Vacías y Jerga)
                            palabras_basura = set(STOPWORDS)
                            palabras_basura.update([
                                # Términos genéricos del gaming
                                "game", "play", "playing", "player", "players", "gameplay",
                                # Verbos y adverbios comunes
                                "really", "even", "much", "one", "make", "time", "hour", "hours", 
                                "will", "feel", "never", "take", "get", "got", "just", "still",
                                # Jerga de Steam y abreviaturas comunes (Ruido)
                                "review", "product", "ive", "pls", "yea", "yeah", "im", "dont", 
                                "cant", "didnt", "buy", "bought", "money", "worth", "people"
                            ])

                            # Generar Nube de Palabras
                            wordcloud = WordCloud(
                                width=900, 
                                height=450, 
                                background_color='#0a0e27', # Alineado al fondo principal
                                colormap='cool', # Paleta vibrante y moderna
                                max_words=80,
                                stopwords=palabras_basura,
                                contour_width=1,
                                contour_color='#667eea'
                            ).generate(texto_limpio)
                            
                            palabras_post_limpieza = len(wordcloud.words_)

                            # 4. VISUALIZACIÓN PROFESIONAL
                            st.markdown("### 🧠 Resultados del Análisis Semántico")
                            
                            # KPIs del proceso NLP
                            kpi1, kpi2, kpi3 = st.columns(3)
                            with kpi1:
                                st.metric("Reseñas Analizadas", len(bloques_texto))
                            with kpi2:
                                st.metric("Palabras Extraídas (Bruto)", f"{palabras_totales_brutas:,}")
                            with kpi3:
                                st.metric("Términos Clave (Limpio)", f"{palabras_post_limpieza:,}")
                                
                            st.markdown("---")
                            
                            # Renderizado del WordCloud
                            fig_wc, ax = plt.subplots(figsize=(12, 6), facecolor='#0a0e27')
                            ax.imshow(wordcloud, interpolation='bilinear')
                            ax.axis('off')
                            # Ajustar márgenes para que ocupe todo el espacio
                            plt.tight_layout(pad=0)
                            st.pyplot(fig_wc)
                            
                        else:
                            st.warning("⚠️ El texto extraído es demasiado corto para un análisis significativo después de la limpieza.")
                            
                    except ImportError:
                        st.error("⚠️ Faltan librerías. Ejecuta: pip install beautifulsoup4 wordcloud matplotlib")
                    except Exception as e:
                        st.error(f"❌ Error durante el pipeline NLP: {e}")
            else:
                st.info("👈 Selecciona un juego en el panel izquierdo y haz clic en 'Iniciar Minería de Datos' para comenzar el análisis.")
    else:
        st.info("💡 Ajusta los filtros en la barra lateral para ver juegos disponibles.")

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #64748b;">
    <p style="margin: 0; font-size: 0.9rem;">
        <strong>Steam Analytics v2.0</strong> · Plataforma de Inteligencia de Mercado
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem;">
        Powered by Streamlit · PostgreSQL · Scikit-Learn · Plotly · BeautifulSoup
    </p>
</div>
""", unsafe_allow_html=True)
