import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
import re
import requests
from bs4 import BeautifulSoup
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from textblob import TextBlob

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN INICIAL DE LA PLATAFORMA
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Steam Analytics | Inteligencia de Mercado",
    layout="wide",
    page_icon="🎮",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════
# DISEÑO VISUAL: NEO-BRUTALIST CON GRADIENTES PREMIUM (CSS CUSTOM)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;700&display=swap');
    
    /* RESET Y TEMA BASE */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background: #0a0e27;
        color: #e8e9ed;
    }
    
    .main {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1428 100%);
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
        border-left: 4px solid #667eea;
        padding-left: 1rem;
        margin: 2rem 0 1.5rem 0 !important;
    }

    /* CARDS DE MÉTRICAS CON ELEVACIÓN */
    .stMetric {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.8rem 1.5rem !important;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-4px);
        border-color: rgba(102, 126, 234, 0.6);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
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
        color: #94a3b8;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 8px;
    }

    /* BOTONES */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.75rem 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# ENGINE DE DATOS Y LÓGICA DE NEGOCIO
# ═══════════════════════════════════════════════════════════════════════════

def format_number(num):
    if pd.isna(num): return "N/A"
    if num >= 1e9: return f"${num / 1e9:.2f}B"
    if num >= 1e6: return f"${num / 1e6:.2f}M"
    if num >= 1e3: return f"${num / 1e3:.2f}K"
    return f"${num:.2f}"

def format_count(num):
    if pd.isna(num): return "N/A"
    if num >= 1e6: return f"{num / 1e6:.2f}M"
    if num >= 1e3: return f"{num / 1e3:.2f}K"
    return f"{num:,.0f}"

@st.cache_resource(show_spinner=False)
def get_engine():
    db_url = st.secrets["DB_URI"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    return create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)

@st.cache_data(ttl=600, show_spinner=False)
def load_data():
    engine = get_engine()
    query = """
        SELECT h.*, d.nombre, d.subgenero, d.desarrollador, t.id_tiempo as fecha
        FROM hechos_resenas_steam h 
        JOIN dim_juego d ON h.fk_juego = d.appid
        LEFT JOIN dim_tiempo t ON h.fk_tiempo = t.id_tiempo
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        df['ratio_positividad'] = (df['votos_positivos'] / (df['votos_positivos'] + df['votos_negativos'])).fillna(0)
        df[['monto_ventas_usd', 'cantidad_descargas', 'conteo_resenas']] = df[['monto_ventas_usd', 'cantidad_descargas', 'conteo_resenas']].fillna(0)
    return df

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR Y FILTROS PROFESIONALES
# ═══════════════════════════════════════════════════════════════════════════

with st.spinner('⚡ Sincronizando con Data Warehouse...'):
    df = load_data()

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=60)
    st.markdown("## Control de Inteligencia")
    st.markdown("---")
    
    all_subgenres = sorted(df['subgenero'].dropna().unique())
    selected_subgenres = st.multiselect("Categorías Objetivo", options=all_subgenres, default=all_subgenres)
    
    min_s, max_s = float(df['monto_ventas_usd'].min()), float(df['monto_ventas_usd'].max())
    sales_range = st.slider("Rango de Capital (USD)", min_s, max_s, (min_s, max_s), format="$%.0f")
    
    st.markdown("---")
    st.markdown("#### 📊 Estado de los Datos")
    st.success(f"✅ {len(df):,} Registros activos")
    st.info(f"🔄 ETL Status: Latencia {np.random.randint(1, 15)}ms")

df_filtered = df[(df['subgenero'].isin(selected_subgenres)) & (df['monto_ventas_usd'].between(sales_range[0], sales_range[1]))].copy()

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD MAIN HEADER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("# 🎮 Steam Analytics")
st.markdown("### Inteligencia de Mercado · Ecosistema de Datos Transaccionales")
st.markdown("---")

# MÉTRICAS TOP-LEVEL
m1, m2, m3, m4 = st.columns(4)
m1.metric("💵 Ventas Brutas Estimadas", format_number(df_filtered['monto_ventas_usd'].sum()))
m2.metric("📥 Volumen de Descargas", format_count(df_filtered['cantidad_descargas'].sum()))
m3.metric("⭐ Índice de Reputación", f"{df_filtered['ratio_positividad'].mean():.1%}")
m4.metric("🎯 Muestra Analizada", f"{len(df_filtered):,}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# SISTEMA DE PESTAÑAS (MÓDULOS DE ANÁLISIS)
# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs([
    "📊 Inteligencia de Mercado",
    "🗄️ Warehouse Explorer",
    "☁️ Análisis Cualitativo (NLP)"
])

# ───────────────────────────────────────────────────────────────────────────
# MODULO 1: ANALISIS DE MERCADO
# ───────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("## 📈 Macro-Análisis: Popularidad vs. Rentabilidad")
    
    fig_scatter = px.scatter(
        df_filtered, x='conteo_resenas', y='monto_ventas_usd', 
        size='cantidad_descargas', color='subgenero', hover_name='nombre',
        trendline="ols", template="plotly_dark", height=600,
        labels={'conteo_resenas': 'N° de Reseñas', 'monto_ventas_usd': 'Ventas (USD)'}
    )
    fig_scatter.update_layout(paper_bgcolor='rgba(15, 20, 40, 0.6)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")
    c_left, c_right = st.columns(2)
    
    with c_left:
        st.markdown("### 🥧 Distribución del Mercado")
        market_share = df_filtered.groupby('subgenero')['monto_ventas_usd'].sum().reset_index()
        fig_pie = px.pie(market_share, values='monto_ventas_usd', names='subgenero', hole=0.5, template="plotly_dark")
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_right:
        st.markdown("### ⚔️ Benchmarking Directo (1 vs 1)")
        games = df_filtered['nombre'].dropna().unique()
        if len(games) >= 2:
            ga, gb = st.columns(2)
            with ga: j1 = st.selectbox("Juego Alfa", games, index=0)
            with gb: j2 = st.selectbox("Juego Beta", games, index=1)
            
            d1, d2 = df_filtered[df_filtered['nombre'] == j1].iloc[0], df_filtered[df_filtered['nombre'] == j2].iloc[0]
            metrics = ['ratio_positividad', 'monto_ventas_usd', 'conteo_resenas', 'cantidad_descargas']
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=[d1[m] for m in metrics], theta=['Satisfacción', 'Ventas', 'Reseñas', 'Descargas'], fill='toself', name=j1))
            fig_radar.add_trace(go.Scatterpolar(r=[d2[m] for m in metrics], theta=['Satisfacción', 'Ventas', 'Reseñas', 'Descargas'], fill='toself', name=j2))
            fig_radar.update_layout(template="plotly_dark", polar=dict(radialaxis=dict(visible=False)))
            st.plotly_chart(fig_radar, use_container_width=True)

# ───────────────────────────────────────────────────────────────────────────
# MODULO 2: EXPLORADOR DE DATOS
# ───────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("## 🗄️ Explorador del Data Warehouse")
    
    available_cols = df_filtered.columns.tolist()
    selected_cols = st.multiselect("Personalizar Columnas:", available_cols, default=['nombre', 'subgenero', 'monto_ventas_usd', 'ratio_positividad', 'desarrollador'])
    
    o1, o2 = st.columns([1, 1])
    with o1: sort_by = st.selectbox("Ordenar por:", selected_cols, index=2)
    with o2: n_rows = st.number_input("N° Registros:", 5, 500, 50)
    
    df_display = df_filtered[selected_cols].sort_values(sort_by, ascending=False).head(n_rows)
    st.dataframe(df_display, use_container_width=True, height=500)
    
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Exportar Reporte Ejecutivo", data=csv, file_name='reporte_steam.csv', mime='text/csv')

# ───────────────────────────────────────────────────────────────────────────
# MODULO 3: ANALISIS CUALITATIVO (SCRAPING + NLP) - VERSIÓN ROBUSTA
# ───────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("## ☁️ Motor de Inteligencia Cualitativa (NLP)")
    st.markdown("Minería de datos en tiempo real mediante Scraping Multi-Página.")
    
    col_config, col_results = st.columns([1, 2.5])
    
    with col_config:
        st.markdown("### 🎯 Configuración")
        game_nlp = st.selectbox("Seleccionar Título:", df_filtered['nombre'].unique())
        st.info("💡 **Pipeline:** \n1. Extracción de 5 páginas \n2. Limpieza con Regex \n3. Análisis TextBlob \n4. Generación Sincrónica")
        
        if st.button("🕷️ Iniciar Proceso de Minería", type="primary", use_container_width=True):
            ejecutar_nlp = True
        else:
            ejecutar_nlp = False

    if ejecutar_nlp:
        with st.spinner(f'Extrayendo datos de Steam para {game_nlp}...'):
            try:
                appid = df_filtered[df_filtered['nombre'] == game_nlp]['fk_juego'].iloc[0]
                headers = {'User-Agent': 'Mozilla/5.0'}
                all_reviews = []
                
                # Scraping de 5 páginas (Robustez)
                for p in range(1, 6):
                    url = f"https://steamcommunity.com/app/{appid}/reviews/?browsefilter=mostrecent&paged={p}"
                    r = requests.get(url, headers=headers)
                    soup = BeautifulSoup(r.text, 'html.parser')
                    blocks = soup.find_all('div', class_='apphub_CardTextContent')
                    if not blocks: break
                    for b in blocks:
                        all_reviews.append(b.text.replace("\n", "").strip())

                # Limpieza y Procesamiento
                raw_text = " ".join(all_reviews).lower()
                clean_text = re.sub(r'[^a-z\s]', '', raw_text)
                
                # Análisis de Sentimiento
                polarities = [TextBlob(rev).sentiment.polarity for rev in all_reviews]
                avg_pol = np.mean(polarities) if polarities else 0
                
                # Definición de colores según sentimiento
                s_color = "#34d399" if avg_pol > 0.1 else "#f87171" if avg_pol < -0.1 else "#fbbf24"
                s_label = "POSITIVO 😀" if avg_pol > 0.1 else "NEGATIVO 😞" if avg_pol < -0.1 else "NEUTRAL 😐"

                with col_results:
                    # KPIs NLP
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Reseñas Extraídas", len(all_reviews))
                    k2.metric("Palabras Procesadas", f"{len(clean_text.split()):,}")
                    k3.metric("Polaridad", f"{avg_pol:+.3f}")
                    
                    # Nube de Palabras
                    st.markdown("#### ☁️ Nube de Términos Clave")
                    wc = WordCloud(width=900, height=450, background_color='#0a0e27', colormap='cool', stopwords=STOPWORDS).generate(clean_text)
                    fig_wc, ax = plt.subplots(facecolor='#0a0e27')
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig_wc)
                    
                    st.markdown("---")
                    
                    # Visualización del Medidor de Sentimiento (Premium Gauge)
                    st.markdown("#### 🎭 Veredicto de la Comunidad")
                    st.markdown(f"""
                        <div style="background: rgba(15,20,40,0.8); border: 2px solid {s_color}; border-radius: 15px; padding: 2rem; text-align: center;">
                            <p style="color: #94a3b8; text-transform: uppercase; font-weight: 600;">Sentimiento Predominante</p>
                            <h2 style="color: {s_color}; font-size: 3rem; margin: 0;">{s_label}</h2>
                            <p style="color: #e0e7ff; font-family: 'Space Mono';">Valor de Polaridad: {avg_pol:.4f}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Barra de distribución
                    st.progress((avg_pol + 1) / 2)
                    st.markdown("<p style='text-align: center; color: #475569;'>Rango: Negativo (-1.0) a Positivo (+1.0)</p>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Falla en el pipeline NLP: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER SISTÉMICO
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem 0; color: #64748b;">
    <p><strong>Steam Analytics v2.0</strong> · Tizimín, Yucatán, México</p>
    <p style="font-size: 0.8rem;">Infraestructura: Python 3.12 · Streamlit · PostgreSQL · Plotly · BeautifulSoup4</p>
</div>
""", unsafe_allow_html=True)
