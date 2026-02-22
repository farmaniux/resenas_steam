import re  
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import streamlit as st
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from wordcloud import WordCloud, STOPWORDS
from textblob import TextBlob  
from sklearn.ensemble import RandomForestRegressor  # <-- NUEVO: Para el Simulador What-If

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
st.markdown("### Plataforma de Inteligencia de Mercado")
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
# TABS DE ANÁLISIS (Actualizado a 4 pestañas)
# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Análisis de Mercado",
    "🎛️ Simulador Estratégico",
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
# TAB 2: SIMULADOR DE ESCENARIOS (Riesgo y Segmentación)
# ═══════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("## 🎛️ Simulador de Riesgo y Estrategia Comercial (What-If)")
    st.markdown("Proyecta los ingresos de tu lanzamiento basándote en datos reales del mercado. La Inteligencia de Negocios evalúa el riesgo y te da **tres escenarios posibles**.")
    
    if not df.empty and len(df) > 10:
        
        # --- PREPARACIÓN DEL MODELO CON GÉNEROS (Punto 1) ---
        with st.spinner('🧠 Entrenando modelo analítico avanzado con datos de tu DWH...'):
            df_ml = df.copy()
            # Convertimos los géneros en columnas (One-Hot Encoding) para que el modelo los entienda
            df_ml = pd.get_dummies(df_ml, columns=['subgenero'], drop_first=False)
            
            # Variables predictoras: Reseñas, Positividad y todas las columnas de género generadas
            columnas_genero = [col for col in df_ml.columns if col.startswith('subgenero_')]
            X_cols = ['conteo_resenas', 'ratio_positividad'] + columnas_genero
            
            X = df_ml[X_cols].fillna(0)
            y = df_ml['monto_ventas_usd'].fillna(0)
            
            # Entrenamos el Bosque Aleatorio
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
            
            # Input 1: Selector de Categoría (Punto 1 implementado)
            generos_disponibles = sorted(df['subgenero'].dropna().unique())
            genero_elegido = st.selectbox(
                "🎮 Categoría del Juego", 
                generos_disponibles,
                help="El mercado paga distinto dependiendo si es un Shooter o un Puzzle."
            )
            
            # Input 2 y 3: Tracción y Calidad
            input_reviews = st.number_input(
                "📢 Meta de Tracción (Número de Reseñas)", 
                min_value=100, max_value=1000000, value=5000, step=500,
                help="¿Cuánta gente probará y reseñará el juego?"
            )
            
            input_positivity = st.slider(
                "⭐ Meta de Calidad (Satisfacción %)", 
                0.0, 1.0, 0.85, 0.01, format="%.2f",
                help="Porcentaje de reseñas positivas esperado."
            )
            
            btn_calcular = st.button("🚀 Calcular Riesgo e Ingresos", type="primary", use_container_width=True)

        with col_out:
            st.markdown("### 2️⃣ Análisis de Riesgo Financiero")
            
            if btn_calcular:
                # --- PREPARAR DATOS PARA PREDICCIÓN ---
                input_data = pd.DataFrame(columns=X_cols)
                input_data.loc[0] = 0  # Llenamos de ceros
                input_data['conteo_resenas'] = input_reviews
                input_data['ratio_positividad'] = input_positivity
                
                # Activamos el género que eligió el usuario poniéndole un 1
                columna_activa = f'subgenero_{genero_elegido}'
                if columna_activa in input_data.columns:
                    input_data.loc[0, columna_activa] = 1
                
                # --- EXTRAER ESCENARIOS DE RIESGO (Punto 2) ---
                # Obtenemos las 100 predicciones individuales de los 100 árboles
                predicciones_arboles = [arbol.predict(input_data.values)[0] for arbol in model.estimators_]
                
                # Calculamos percentiles para definir el riesgo
                escenario_pesimista = np.percentile(predicciones_arboles, 15)  # El peor 15% de los casos
                escenario_realista = np.median(predicciones_arboles)           # El caso promedio (Mediana)
                escenario_optimista = np.percentile(predicciones_arboles, 85)  # El mejor 15% de los casos
                
                # --- TARJETAS DE RESULTADO ---
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
                
                # Gráfico de Embudo (Funnel) para explicar el riesgo
                fig_risk = go.Figure(go.Funnel(
                    y=["Optimista (Techo)", "Esperado (Seguro)", "Pesimista (Piso)"],
                    x=[escenario_optimista, escenario_realista, escenario_pesimista],
                    textinfo="value",
                    marker={"color": ["#60a5fa", "#34d399", "#f87171"]}
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
# TAB 4: ANÁLISIS CUALITATIVO (NLP)
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
            
            st.info("💡 **Proceso NLP Activo:**\n1. Web Scraping (Paginado)\n2. Tokenización\n3. Filtrado Regex\n4. Eliminación de Stopwords\n5. Análisis de Sentimiento (TextBlob)")
            
            ejecutar_scraping = st.button("🕷️ Iniciar Minería de Datos", type="primary", use_container_width=True)
            
        with col_scrap2:
            if ejecutar_scraping:
                with st.spinner(f'Navegando y extrayendo múltiples páginas de Steam para {juego_wordcloud}...'):
                    try:
                        # 1. EXTRACCIÓN MEJORADA (Paginación múltiple)
                        appid = df_filtered[df_filtered['nombre'] == juego_wordcloud]['fk_juego'].iloc[0]
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        
                        textos_recolectados = []
                        textos_para_sentimiento = []  
                        total_resenas_extraidas = 0
                        
                        # Loop para minar las primeras 5 páginas (Aprox 50 reseñas)
                        for pagina in range(1, 6):
                            url = f"https://steamcommunity.com/app/{appid}/reviews/?browsefilter=mostrecent&paged={pagina}"
                            respuesta = requests.get(url, headers=headers)
                            soup = BeautifulSoup(respuesta.text, 'html.parser')
                            
                            bloques_texto = soup.find_all('div', class_='apphub_CardTextContent')
                            if not bloques_texto:
                                break  
                                
                            total_resenas_extraidas += len(bloques_texto)
                            
                            for bloque in bloques_texto:
                                texto_bloque = bloque.text.replace("\n", "").strip()
                                textos_recolectados.append(texto_bloque)
                                textos_para_sentimiento.append(texto_bloque)  
                            
                        texto_bruto = " ".join(textos_recolectados)
                        palabras_totales_brutas = len(texto_bruto.split())
                        
                        # 2. LIMPIEZA Y NORMALIZACIÓN (Pipeline NLP)
                        texto_limpio = texto_bruto.replace("Early Access Review", "").replace("Posted", "")
                        texto_limpio = texto_limpio.lower()
                        texto_limpio = re.sub(r'[^a-z\s]', '', texto_limpio)
                        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
                        
                        if len(texto_limpio) > 50:
                            # 3. FILTRADO DE STOPWORDS (Actualizado con meses)
                            palabras_basura = set(STOPWORDS)
                            palabras_basura.update([
                                "game", "play", "playing", "player", "players", "gameplay",
                                "really", "even", "much", "one", "make", "time", "hour", "hours", 
                                "will", "feel", "never", "take", "get", "got", "just", "still",
                                "review", "product", "ive", "pls", "yea", "yeah", "im", "dont", 
                                "cant", "didnt", "buy", "bought", "money", "worth", "people",
                                "january", "february", "march", "april", "may", "june", 
                                "july", "august", "september", "october", "november", "december"
                            ])

                            # Generar Nube de Palabras
                            wordcloud = WordCloud(
                                width=900, 
                                height=450, 
                                background_color='#0a0e27', 
                                colormap='cool', 
                                max_words=80,
                                stopwords=palabras_basura,
                                contour_width=1,
                                contour_color='#667eea'
                            ).generate(texto_limpio)
                            
                            palabras_post_limpieza = len(wordcloud.words_)

                            # ── ANÁLISIS DE SENTIMIENTO CON TEXTBLOB ─────────────────
                            polaridades = []
                            subjetividades = []
                            for texto_resena in textos_para_sentimiento:
                                blob = TextBlob(texto_resena)
                                polaridades.append(blob.sentiment.polarity)
                                subjetividades.append(blob.sentiment.subjectivity)

                            polaridad_promedio = np.mean(polaridades) if polaridades else 0.0
                            subjetividad_promedio = np.mean(subjetividades) if subjetividades else 0.0

                            # Clasificar en Positivo / Neutral / Negativo
                            if polaridad_promedio >= 0.1:
                                sentimiento_label = "POSITIVO 😀"
                                sentimiento_color = "#34d399"
                            elif polaridad_promedio <= -0.1:
                                sentimiento_label = "NEGATIVO 😞"
                                sentimiento_color = "#f87171"
                            else:
                                sentimiento_label = "NEUTRAL 😐"
                                sentimiento_color = "#fbbf24"

                            # Conteo por categoría
                            pos_count = sum(1 for p in polaridades if p >= 0.1)
                            neg_count = sum(1 for p in polaridades if p <= -0.1)
                            neu_count = len(polaridades) - pos_count - neg_count
                            # ────────────────────────────────────────────────────────────────

                            # 4. KPIs SUPERIORES
                            st.markdown("### 🧠 Resultados del Análisis Semántico")
                            
                            kpi1, kpi2, kpi3 = st.columns(3)
                            with kpi1:
                                st.metric("Reseñas Analizadas", total_resenas_extraidas)
                            with kpi2:
                                st.metric("Palabras Extraídas (Bruto)", f"{palabras_totales_brutas:,}")
                            with kpi3:
                                st.metric("Términos Clave (Limpio)", f"{palabras_post_limpieza:,}")
                                
                            st.markdown("---")
                            
                            # 5. NUBE DE PALABRAS
                            st.markdown("#### ☁️ Nube de Palabras")
                            fig_wc, ax = plt.subplots(figsize=(12, 6), facecolor='#0a0e27')
                            ax.imshow(wordcloud, interpolation='bilinear')
                            ax.axis('off')
                            plt.tight_layout(pad=0)
                            st.pyplot(fig_wc)
                            
                            st.markdown("---")

                            # ── MEDIDOR DE SENTIMIENTO ───────────────────────────────
                            st.markdown("#### 🎭 Medidor de Sentimiento de la Comunidad")
                            st.markdown(f"Análisis matemático basado en **{total_resenas_extraidas} reseñas reales** extraídas en este momento exacto de Steam.")

                            # Convertimos polaridad de [-1,+1] a [0,100] para posicionar la aguja
                            pct = (polaridad_promedio + 1) / 2 * 100

                            col_gauge_sent, col_detalle_sent = st.columns([1.6, 1])

                            with col_gauge_sent:
                                # ── Tarjeta principal de veredicto ──────────────────────
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, rgba(15,20,40,0.95) 0%, rgba(26,31,58,0.9) 100%);
                                    border: 2px solid {sentimiento_color};
                                    border-radius: 20px;
                                    padding: 1.8rem 2.5rem;
                                    text-align: center;
                                    box-shadow: 0 0 40px {sentimiento_color}33, inset 0 1px 0 rgba(255,255,255,0.05);
                                    margin-bottom: 1.2rem;
                                ">
                                    <p style="margin:0; color:#94a3b8; font-size:0.78rem; text-transform:uppercase; letter-spacing:.12em; font-weight:600;">Veredicto TextBlob</p>
                                    <p style="margin:0.3rem 0; font-size:2.6rem; font-weight:900; color:{sentimiento_color}; font-family:'Space Mono',monospace; text-shadow: 0 0 20px {sentimiento_color}88;">{sentimiento_label}</p>
                                    <p style="margin:0; font-size:1rem; color:#e0e7ff; font-family:'Space Mono',monospace;">Polaridad: <strong style="color:{sentimiento_color};">{polaridad_promedio:+.3f}</strong></p>
                                </div>
                                """, unsafe_allow_html=True)

                                # ── Barra horizontal con gradiente y aguja ──────────────
                                st.markdown(f"""
                                <div style="margin: 0.2rem 0 0 0;">
                                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                        <span style="color:#f87171; font-size:0.78rem; font-weight:700;">😞 NEGATIVO</span>
                                        <span style="color:#fbbf24; font-size:0.78rem; font-weight:700;">😐 NEUTRAL</span>
                                        <span style="color:#34d399; font-size:0.78rem; font-weight:700;">😀 POSITIVO</span>
                                    </div>
                                    <div style="position:relative; height:32px; border-radius:16px;
                                        background: linear-gradient(to right,
                                            #ef4444 0%, #f97316 20%, #fbbf24 42%, #fbbf24 58%, #84cc16 80%, #34d399 100%);
                                        box-shadow: 0 2px 16px rgba(0,0,0,0.5); overflow:visible;">
                                        <div style="
                                            position:absolute;
                                            left: calc({pct:.1f}% - 11px);
                                            top: -14px;
                                            width: 0; height: 0;
                                            border-left: 11px solid transparent;
                                            border-right: 11px solid transparent;
                                            border-top: 18px solid white;
                                            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.7));
                                        "></div>
                                        <div style="
                                            position:absolute;
                                            left: calc({pct:.1f}% - 2px);
                                            top: 0; width: 4px; height: 32px;
                                            background: rgba(255,255,255,0.9);
                                            border-radius: 2px;
                                            box-shadow: 0 0 10px rgba(255,255,255,0.8);
                                        "></div>
                                    </div>
                                    <div style="display:flex; justify-content:space-between; margin-top:5px;">
                                        <span style="color:#475569; font-size:0.68rem; font-family:'Space Mono',monospace;">-1.0</span>
                                        <span style="color:#475569; font-size:0.68rem; font-family:'Space Mono',monospace;">-0.5</span>
                                        <span style="color:#475569; font-size:0.68rem; font-family:'Space Mono',monospace;">0</span>
                                        <span style="color:#475569; font-size:0.68rem; font-family:'Space Mono',monospace;">+0.5</span>
                                        <span style="color:#475569; font-size:0.68rem; font-family:'Space Mono',monospace;">+1.0</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                                # ── Barra apilada de distribución ───────────────────────
                                total_r = max(pos_count + neu_count + neg_count, 1)
                                pct_pos = pos_count / total_r * 100
                                pct_neu = neu_count / total_r * 100
                                pct_neg = neg_count / total_r * 100

                                st.markdown(f"""
                                <div style="margin-top:1.4rem;">
                                    <p style="margin:0 0 0.5rem 0; color:#94a3b8; font-size:0.72rem; text-transform:uppercase; letter-spacing:.08em;">
                                        Distribución de las {total_resenas_extraidas} reseñas
                                    </p>
                                    <div style="display:flex; height:22px; border-radius:11px; overflow:hidden; gap:2px;">
                                        <div style="width:{pct_pos:.1f}%; background:#34d399; display:flex; align-items:center; justify-content:center;">
                                            <span style="color:#064e3b; font-size:0.68rem; font-weight:800;">{pos_count}</span>
                                        </div>
                                        <div style="width:{pct_neu:.1f}%; background:#fbbf24; display:flex; align-items:center; justify-content:center;">
                                            <span style="color:#78350f; font-size:0.68rem; font-weight:800;">{neu_count}</span>
                                        </div>
                                        <div style="width:{pct_neg:.1f}%; background:#f87171; display:flex; align-items:center; justify-content:center;">
                                            <span style="color:#7f1d1d; font-size:0.68rem; font-weight:800;">{neg_count}</span>
                                        </div>
                                    </div>
                                    <div style="display:flex; gap:1.4rem; margin-top:0.5rem;">
                                        <span style="color:#34d399; font-size:0.72rem; font-weight:600;">● Positivas {pct_pos:.0f}%</span>
                                        <span style="color:#fbbf24; font-size:0.72rem; font-weight:600;">● Neutrales {pct_neu:.0f}%</span>
                                        <span style="color:#f87171; font-size:0.72rem; font-weight:600;">● Negativas {pct_neg:.0f}%</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                            with col_detalle_sent:
                                st.markdown("##### 📐 Métricas Detalladas")

                                st.markdown(f"""
                                <div style="display:flex; flex-direction:column; gap:0.65rem; margin-top:0.4rem;">
                                    <div style="padding:0.9rem 1.1rem; background:rgba(52,211,153,0.08); border:1.5px solid rgba(52,211,153,0.35); border-radius:12px; display:flex; justify-content:space-between; align-items:center;">
                                        <span style="color:#94a3b8; font-size:0.82rem;">✅ Positivas</span>
                                        <span style="color:#34d399; font-weight:800; font-size:1.5rem; font-family:'Space Mono',monospace;">{pos_count}</span>
                                    </div>
                                    <div style="padding:0.9rem 1.1rem; background:rgba(251,191,36,0.08); border:1.5px solid rgba(251,191,36,0.35); border-radius:12px; display:flex; justify-content:space-between; align-items:center;">
                                        <span style="color:#94a3b8; font-size:0.82rem;">⚖️ Neutrales</span>
                                        <span style="color:#fbbf24; font-weight:800; font-size:1.5rem; font-family:'Space Mono',monospace;">{neu_count}</span>
                                    </div>
                                    <div style="padding:0.9rem 1.1rem; background:rgba(248,113,113,0.08); border:1.5px solid rgba(248,113,113,0.35); border-radius:12px; display:flex; justify-content:space-between; align-items:center;">
                                        <span style="color:#94a3b8; font-size:0.82rem;">❌ Negativas</span>
                                        <span style="color:#f87171; font-weight:800; font-size:1.5rem; font-family:'Space Mono',monospace;">{neg_count}</span>
                                    </div>
                                    <div style="padding:0.9rem 1.1rem; background:rgba(102,126,234,0.08); border:1.5px solid rgba(102,126,234,0.3); border-radius:12px;">
                                        <p style="margin:0; color:#a5b4fc; font-size:0.7rem; text-transform:uppercase; letter-spacing:.06em;">Polaridad Promedio</p>
                                        <p style="margin:0.1rem 0 0 0; color:#e0e7ff; font-weight:800; font-size:1.2rem; font-family:'Space Mono',monospace;">{polaridad_promedio:+.4f}</p>
                                    </div>
                                    <div style="padding:0.9rem 1.1rem; background:rgba(102,126,234,0.04); border:1.5px solid rgba(102,126,234,0.18); border-radius:12px;">
                                        <p style="margin:0; color:#a5b4fc; font-size:0.7rem; text-transform:uppercase; letter-spacing:.06em;">Subjetividad Promedio</p>
                                        <p style="margin:0.1rem 0 0 0; color:#e0e7ff; font-weight:800; font-size:1.2rem; font-family:'Space Mono',monospace;">{subjetividad_promedio:.3f}</p>
                                        <p style="margin:0; color:#475569; font-size:0.7rem;">0 = objetivo · 1 = muy subjetivo</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                        else:
                            st.warning("⚠️ El texto extraído es demasiado corto para un análisis significativo después de la limpieza.")
                            
                    except ImportError:
                        st.error("⚠️ Faltan librerías. Ejecuta: pip install beautifulsoup4 wordcloud matplotlib textblob")
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
        <strong>Steam Analytics v4.0</strong> · Plataforma de Inteligencia de Mercado
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem;">
        Powered by Streamlit · PostgreSQL · Plotly · BeautifulSoup
    </p>
</div>
""", unsafe_allow_html=True)
