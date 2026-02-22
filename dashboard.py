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
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
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
    }
    
    h1 {
        font-size: 3.5rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
    }
    
    h2 {
        color: #a5b4fc !important;
        border-left: 4px solid #667eea;
        padding-left: 1rem;
        margin: 2rem 0 1.5rem 0 !important;
    }

    .stMetric {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.8rem 1.5rem !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 20, 40, 0.6);
        padding: 0.5rem;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES UTILITARIAS
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
    return create_engine(db_url, pool_pre_ping=True)

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
        for col in ['monto_ventas_usd', 'cantidad_descargas', 'conteo_resenas']:
            df[col] = df[col].fillna(0)
    return df

# ═══════════════════════════════════════════════════════════════════════════
# CARGA Y FILTROS
# ═══════════════════════════════════════════════════════════════════════════

df = load_data()

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=50)
    st.markdown("### Steam Analytics")
    st.markdown("---")
    all_subgenres = sorted(df['subgenero'].dropna().unique())
    selected_subgenres = st.multiselect("Categorías", options=all_subgenres, default=all_subgenres)
    
    sales_range = st.slider("Ventas (USD)", float(df['monto_ventas_usd'].min()), 
                           float(df['monto_ventas_usd'].max()), 
                           (float(df['monto_ventas_usd'].min()), float(df['monto_ventas_usd'].max())))

df_filtered = df[(df['subgenero'].isin(selected_subgenres)) & 
                 (df['monto_ventas_usd'].between(sales_range[0], sales_range[1]))].copy()

# ═══════════════════════════════════════════════════════════════════════════
# HEADER Y MÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("# 🎮 Steam Analytics")
st.markdown("### Inteligencia de Mercado & Sentimiento de Comunidad")

c1, c2, c3, c4 = st.columns(4)
c1.metric("💵 Ventas Totales", format_number(df_filtered['monto_ventas_usd'].sum()))
c2.metric("📥 Descargas", format_count(df_filtered['cantidad_descargas'].sum()))
c3.metric("⭐ Satisfacción", f"{df_filtered['ratio_positividad'].mean():.1%}")
c4.metric("🎯 Juegos", f"{len(df_filtered):,}")

# ═══════════════════════════════════════════════════════════════════════════
# TABS DE ANÁLISIS (SÓLO 3 APARTADOS)
# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs([
    "📊 Análisis de Mercado",
    "🗄️ Explorador de Datos",
    "☁️ Análisis Cualitativo (NLP)"
])

# --- TAB 1: ANÁLISIS DE MERCADO ---
with tab1:
    st.markdown("## 📊 Inteligencia de Mercado: Volumen vs. Rentabilidad")
    fig_scatter = px.scatter(df_filtered, x='conteo_resenas', y='monto_ventas_usd',
                            size='cantidad_descargas', color='subgenero', hover_name='nombre',
                            trendline="ols", template="plotly_dark", height=550)
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### 🥧 Distribución por Categoría")
        fig_pie = px.pie(df_filtered.groupby('subgenero')['monto_ventas_usd'].sum().reset_index(), 
                         values='monto_ventas_usd', names='subgenero', hole=0.4, template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_r:
        st.markdown("### ⚔️ Benchmarking: 1 vs 1")
        j_list = df_filtered['nombre'].unique()
        if len(j_list) >= 2:
            j1 = st.selectbox("Juego A", j_list, index=0)
            j2 = st.selectbox("Juego B", j_list, index=1)
            # Radar Chart Logic
            metricas = ['ratio_positividad', 'monto_ventas_usd', 'conteo_resenas']
            fig_radar = go.Figure()
            for j in [j1, j2]:
                val = df_filtered[df_filtered['nombre'] == j][metricas].iloc[0].values
                fig_radar.add_trace(go.Scatterpolar(r=val, theta=metricas, fill='toself', name=j))
            fig_radar.update_layout(template="plotly_dark", polar=dict(radialaxis=dict(visible=False)))
            st.plotly_chart(fig_radar, use_container_width=True)

# --- TAB 2: EXPLORADOR DE DATOS ---
with tab2:
    st.markdown("## 🗄️ Explorador de Datos")
    cols = st.multiselect("Columnas:", df_filtered.columns.tolist(), 
                          default=['nombre', 'subgenero', 'monto_ventas_usd', 'ratio_positividad'])
    st.dataframe(df_filtered[cols], use_container_width=True)
    
    csv = df_filtered[cols].to_csv(index=False).encode('utf-8')
    st.download_button("📄 Descargar Reporte (CSV)", data=csv, file_name='steam_analytics.csv', mime='text/csv')

# --- TAB 3: NLP Y SCRAPING ---
with tab3:
    st.markdown("## ☁️ Motor de Inteligencia Cualitativa (NLP)")
    col_sc1, col_sc2 = st.columns([1, 2.5])
    
    with col_sc1:
        target_game = st.selectbox("Juego a minar:", df_filtered['nombre'].unique())
        ejecutar = st.button("🕷️ Iniciar Minería", type="primary", use_container_width=True)
        st.info("💡 Scraping directo de Steam Community + Análisis de Sentimiento TextBlob.")

    with col_sc2:
        if ejecutar:
            with st.spinner('Extrayendo reseñas...'):
                try:
                    appid = df_filtered[df_filtered['nombre'] == target_game]['fk_juego'].iloc[0]
                    res = requests.get(f"https://steamcommunity.com/app/{appid}/reviews/?paged=1", 
                                     headers={'User-Agent': 'Mozilla/5.0'})
                    soup = BeautifulSoup(res.text, 'html.parser')
                    reviews = [b.text.strip() for b in soup.find_all('div', class_='apphub_CardTextContent')][:50]
                    
                    full_text = " ".join(reviews).lower()
                    full_text = re.sub(r'[^a-z\s]', '', full_text)
                    
                    # Sentiment
                    blob = TextBlob(full_text)
                    sent = blob.sentiment.polarity
                    
                    st.metric("Polaridad Promedio", f"{sent:+.3f}")
                    st.progress((sent + 1) / 2) # Normalizar -1,1 a 0,1
                    
                    wc = WordCloud(width=800, height=400, background_color='#0a0e27', colormap='cool').generate(full_text)
                    fig_wc, ax = plt.subplots(facecolor='#0a0e27')
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig_wc)
                except Exception as e:
                    st.error(f"Error en NLP: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("<center style='color: #64748b;'>Steam Analytics v2.0 | Tizimín, Yucatán</center>", unsafe_allow_html=True)
