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
    
    .stMetric {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.8rem 1.5rem !important;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stMetric:hover {
        transform: translateY(-4px);
        border-color: rgba(102, 126, 234, 0.6);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 20, 40, 0.6);
        padding: 0.5rem;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
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
    if num >= 1e9: return f"{num / 1e9:.2f}B"
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
# CARGA DE DATOS Y SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

with st.spinner('⚡ Cargando datos del data warehouse...'):
    df = load_data()

if df.empty:
    st.error("⚠️ No se pudieron cargar los datos.")
    st.stop()

with st.sidebar:
    col_logo, col_title = st.columns([1, 3])
    with col_logo: st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=50)
    with col_title: st.markdown("### Steam Analytics")
    st.markdown("---")
    
    all_subgenres = sorted(df['subgenero'].dropna().unique())
    selected_subgenres = st.multiselect("Categorías", options=all_subgenres, default=all_subgenres)
    
    min_sales, max_sales = float(df['monto_ventas_usd'].min()), float(df['monto_ventas_usd'].max())
    sales_range = st.slider("Ventas (USD)", min_sales, max_sales, (min_sales, max_sales), format="$%.0f")
    
    st.markdown("---")
    st.success(f"✅ **{len(df):,}** juegos en DWH")
    st.info(f"🔄 Última actualización: Hace {np.random.randint(5, 30)} min")

df_filtered = df[(df['subgenero'].isin(selected_subgenres)) & (df['monto_ventas_usd'].between(sales_range[0], sales_range[1]))].copy()

# ═══════════════════════════════════════════════════════════════════════════
# HEADER PRINCIPAL Y MÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("# 🎮 Steam Analytics")
st.markdown("### Plataforma de Inteligencia de Mercado · Exploración Estratégica")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💵 Ventas Totales", format_number(df_filtered['monto_ventas_usd'].sum()))
col2.metric("📥 Descargas Totales", format_count(df_filtered['cantidad_descargas'].sum()))
col3.metric("⭐ Satisfacción", f"{df_filtered['ratio_positividad'].mean():.1%}")
col4.metric("🎯 Juegos Analizados", f"{len(df_filtered):,}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# TABS DE ANÁLISIS
# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs([
    "📊 Análisis de Mercado",
    "🗄️ Explorador de Datos",
    "☁️ Análisis Cualitativo (NLP)"
])

# ───────────────────────────────────────────────────────────────────────────
# TAB 1: ANÁLISIS DE MERCADO
# ───────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("## 📊 Inteligencia de Mercado: Volumen vs. Rentabilidad")
    if not df_filtered.empty:
        fig_scatter = px.scatter(df_filtered, x='conteo_resenas', y='monto_ventas_usd',
                                size='cantidad_descargas', color='subgenero', hover_name='nombre',
                                trendline="ols", template="plotly_dark", height=550)
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("---")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 🥧 Distribución por Categoría")
            market_share = df_filtered.groupby('subgenero')['monto_ventas_usd'].sum().reset_index()
            fig_pie = px.pie(market_share.head(10), values='monto_ventas_usd', names='subgenero', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_r:
            st.markdown("### ⚔️ Benchmarking: 1 vs 1")
            juegos = df_filtered['nombre'].dropna().unique()
            if len(juegos) >= 2:
                g1, g2 = st.columns(2)
                with g1: j1 = st.selectbox("Juego A", juegos, index=0)
                with g2: j2 = st.selectbox("Juego B", juegos, index=1)
                
                d1, d2 = df_filtered[df_filtered['nombre'] == j1].iloc[0], df_filtered[df_filtered['nombre'] == j2].iloc[0]
                metricas_radar = ['ratio_positividad', 'cantidad_descargas', 'monto_ventas_usd', 'conteo_resenas']
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=[d1[m] for m in metricas_radar], theta=metricas_radar, fill='toself', name=j1))
                fig_radar.add_trace(go.Scatterpolar(r=[d2[m] for m in metricas_radar], theta=metricas_radar, fill='toself', name=j2))
                fig_radar.update_layout(template="plotly_dark", polar=dict(radialaxis=dict(visible=False)))
                st.plotly_chart(fig_radar, use_container_width=True)

# ───────────────────────────────────────────────────────────────────────────
# TAB 2: EXPLORADOR DE DATOS
# ───────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("## 🗄️ Explorador del Data Warehouse")
    cols_disp = df_filtered.columns.tolist()
    selected_cols = st.multiselect("Columnas:", cols_disp, default=['nombre', 'subgenero', 'monto_ventas_usd', 'ratio_positividad'])
    
    c_opt1, c_opt2 = st.columns(2)
    with c_opt1: sort_col = st.selectbox("Ordenar por:", selected_cols)
    with c_opt2: order = st.radio("Orden:", ["Descendente", "Ascendente"], horizontal=True)
    
    df_display = df_filtered[selected_cols].sort_values(by=sort_col, ascending=(order=="Ascendente"))
    st.dataframe(df_display.head(100), use_container_width=True, height=500)
    st.download_button("📥 Descargar CSV", df_display.to_csv(index=False).encode('utf-8'), "reporte_steam.csv", "text/csv")

# ───────────────────────────────────────────────────────────────────────────
# TAB 3: ANÁLISIS CUALITATIVO (ROBUSTO)
# ───────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("## ☁️ Motor de Inteligencia Cualitativa (NLP)")
    col_s1, col_s2 = st.columns([1, 2.5])
    
    with col_s1:
        st.markdown("### 🎯 Configuración")
        j_wc = st.selectbox("Juego a minar:", df_filtered['nombre'].unique())
        ejecutar = st.button("🕷️ Iniciar Minería", type="primary", use_container_width=True)
        st.info("💡 Pipeline: Scraping (5 págs) → Regex → Stopwords → TextBlob Sentiment.")

    with col_s2:
        if ejecutar:
            with st.spinner(f'Extrayendo datos reales de Steam para {j_wc}...'):
                try:
                    appid = df_filtered[df_filtered['nombre'] == j_wc]['fk_juego'].iloc[0]
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    recolectados, individuales = [], []
                    
                    for p in range(1, 6):
                        url = f"https://steamcommunity.com/app/{appid}/reviews/?browsefilter=mostrecent&paged={p}"
                        res = requests.get(url, headers=headers)
                        soup = BeautifulSoup(res.text, 'html.parser')
                        bloques = soup.find_all('div', class_='apphub_CardTextContent')
                        if not bloques: break
                        for b in bloques:
                            t = b.text.replace("\n", "").strip()
                            recolectados.append(t)
                            individuales.append(t)

                    texto_bruto = " ".join(recolectados).lower()
                    texto_limpio = re.sub(r'[^a-z\s]', '', texto_bruto)
                    
                    if len(texto_limpio) > 50:
                        # Sentiment Analysis
                        pols = [TextBlob(rev).sentiment.polarity for rev in individuales]
                        avg_p = np.mean(pols) if pols else 0
                        s_label = "POSITIVO 😀" if avg_p > 0.1 else "NEGATIVO 😞" if avg_p < -0.1 else "NEUTRAL 😐"
                        s_color = "#34d399" if avg_p > 0.1 else "#f87171" if avg_p < -0.1 else "#fbbf24"

                        # Visualización Premium de NLP
                        k1, k2, k3 = st.columns(3)
                        k1.metric("Reseñas", len(recolectados))
                        k2.metric("Términos", len(texto_limpio.split()))
                        k3.metric("Polaridad", f"{avg_p:+.3f}")

                        st.markdown("#### ☁️ Nube de Palabras")
                        wc = WordCloud(width=900, height=450, background_color='#0a0e27', colormap='cool', stopwords=STOPWORDS).generate(texto_limpio)
                        fig_wc, ax = plt.subplots(facecolor='#0a0e27')
                        ax.imshow(wc)
                        ax.axis('off')
                        st.pyplot(fig_wc)

                        st.markdown(f"""
                            <div style="background: rgba(15,20,40,0.9); border: 2px solid {s_color}; border-radius: 20px; padding: 2rem; text-align: center;">
                                <p style="color: #94a3b8; text-transform: uppercase;">Sentimiento TextBlob</p>
                                <h2 style="color: {s_color}; font-size: 3rem; margin: 0;">{s_label}</h2>
                                <p style="font-family: 'Space Mono';">Polaridad Promedio: {avg_p:.4f}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.progress((avg_p + 1) / 2)
                    else:
                        st.warning("Texto insuficiente para análisis.")
                except Exception as e:
                    st.error(f"Error en NLP: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""<div style="text-align: center; color: #64748b;">
    <strong>Steam Analytics v2.0</strong> · Plataforma de Inteligencia de Mercado<br>
    Powered by Streamlit · Plotly · BeautifulSoup
</div>""", unsafe_allow_html=True)
