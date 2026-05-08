"""
Steam Analytics BI v5.0 — Dashboard de Inteligencia de Mercado
Autor: Farid Rodriguez Puc | TecNM Ingenieria Informatica
GitHub: github.com/farmaniux/resenas_steam
URL Live: https://dashboardpy-nxggacwyh74mfpubiconcd.streamlit.app

NUEVAS FEATURES v5.0:
  • Catalogo Visual de Juegos con banner images (Steam CDN)
  • Word Cloud interactivo por juego (Tab 4 NLP)
  • Heatmap Sentiment por juego x mes (Tab 3)
  • Banner del juego seleccionado en Tab 4
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import os, time, ssl, datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from fpdf import FPDF
import io, base64, re
from wordcloud import WordCloud, STOPWORDS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

load_dotenv()
st.set_page_config(
    page_title="Steam Analytics BI v5.0",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CONSTANTES ────────────────────────────────────────────────────────────────
CACHE_TTL = 600

# Mapeo AppID → nombre y URL de imagen Steam CDN
GAME_IMAGES = {
    "Counter-Strike 2":     {"appid": 730,      "img": "https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg"},
    "PUBG: Battlegrounds":  {"appid": 578080,   "img": "https://cdn.akamai.steamstatic.com/steam/apps/578080/header.jpg"},
    "Rust":                 {"appid": 252490,   "img": "https://cdn.akamai.steamstatic.com/steam/apps/252490/header.jpg"},
    "Left 4 Dead 2":        {"appid": 550,      "img": "https://cdn.akamai.steamstatic.com/steam/apps/550/header.jpg"},
    "Call of Duty: MW":     {"appid": 2519060,  "img": "https://cdn.akamai.steamstatic.com/steam/apps/2519060/header.jpg"},
    "Destiny 2":            {"appid": 1085660,  "img": "https://cdn.akamai.steamstatic.com/steam/apps/1085660/header.jpg"},
    "Team Fortress 2":      {"appid": 440,      "img": "https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg"},
    "Halo Infinite":        {"appid": 1240440,  "img": "https://cdn.akamai.steamstatic.com/steam/apps/1240440/header.jpg"},
    "Apex Legends":         {"appid": 1172470,  "img": "https://cdn.akamai.steamstatic.com/steam/apps/1172470/header.jpg"},
    "PlanetSide 2":         {"appid": 218230,   "img": "https://cdn.akamai.steamstatic.com/steam/apps/218230/header.jpg"},
}

# ── ESTILOS CSS GLOBALES ──────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .metric-card {
    background: linear-gradient(135deg, #1B3A6B 0%, #2E75B6 100%);
    border-radius: 12px; padding: 18px 24px; color: white;
    box-shadow: 0 4px 16px rgba(30,60,115,.25);
  }
  .metric-value { font-size: 2.1rem; font-weight: 700; }
  .metric-label { font-size: .82rem; opacity: .85; text-transform: uppercase; letter-spacing: .06em; }
  .section-badge {
    display: inline-block; background: #EFF6FF; color: #1B3A6B;
    border-left: 4px solid #2E75B6; padding: 4px 14px;
    border-radius: 4px; font-weight: 600; margin-bottom: 14px; font-size: .93rem;
  }
  .game-card {
    border-radius: 10px; overflow: hidden;
    box-shadow: 0 3px 12px rgba(0,0,0,.18);
    transition: transform .2s, box-shadow .2s;
    background: #0e1117;
  }
  .game-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,.30); }
  .game-card img { width: 100%; display: block; }
  .game-card-info {
    padding: 10px 12px; color: #f0f0f0;
  }
  .game-card-title { font-weight: 700; font-size: .9rem; margin-bottom: 4px; }
  .game-card-sub { font-size: .78rem; color: #aaa; }
  .wc-title { text-align:center; font-weight:600; color:#1B3A6B; margin-bottom:6px; }
  .stTabs [data-baseweb="tab"] { font-size: .95rem; font-weight: 600; padding: 10px 20px; }
  div[data-testid="stSidebarContent"] { background: linear-gradient(180deg,#0D1B38 0%,#1B3A6B 100%); color:white; }
</style>
""", unsafe_allow_html=True)

# ── CONEXIÓN BD ───────────────────────────────────────────────────────────────
@st.cache_resource
def get_pool():
    db_url = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL", "")
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    return psycopg2.pool.SimpleConnectionPool(
        1, 5, db_url,
        sslmode="require",
        connect_timeout=15
    )

@st.cache_data(ttl=CACHE_TTL)
def load_data():
    conn = get_pool().getconn()
    try:
        df_res = pd.read_sql("""
            SELECT h.fecha_registro, h.ventas_estimadas, h.descargas_estimadas,
                   h.precio_usd, h.votos_positivos, h.votos_negativos,
                   h.promedio_jugadores, h.pico_jugadores,
                   d.nombre_juego, d.desarrollador, d.subgenero,
                   d.plataformas, d.metascore, d.appid
            FROM hechos_resenas_steam h
            JOIN dim_juego d ON h.id_juego = d.id_juego
        """, conn)
        df_nlp = pd.read_sql("""
            SELECT s.fecha_procesamiento, s.polaridad_roberta, s.polaridad_score,
                   s.clasificacion_sentimiento, s.tema_principal,
                   s.conteo_resenas, s.promedio_jugadores_dia,
                   d.nombre_juego, d.appid
            FROM hechos_sentimiento s
            JOIN dim_juego d ON s.id_juego = d.id_juego
        """, conn)
        return df_res, df_nlp
    finally:
        get_pool().putconn(conn)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px'>
      <span style='font-size:2.4rem'>🎮</span><br>
      <span style='color:white;font-weight:700;font-size:1.1rem'>Steam Analytics BI</span><br>
      <span style='color:#90CAF9;font-size:.8rem'>v5.0 Premium</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    with st.spinner("Cargando datos..."):
        df, df_nlp = load_data()

    df['fecha_registro'] = pd.to_datetime(df['fecha_registro'])
    df_nlp['fecha_procesamiento'] = pd.to_datetime(df_nlp['fecha_procesamiento'])

    st.markdown("<p style='color:#90CAF9;font-weight:600;font-size:.85rem'>🎯 FILTROS</p>", unsafe_allow_html=True)

    subgeneros = sorted(df['subgenero'].dropna().unique().tolist())
    sel_sub = st.multiselect("Subgénero", subgeneros, default=subgeneros[:3] if len(subgeneros) >= 3 else subgeneros,
                              help="Filtra por subgénero de videojuego")

    ventas_min, ventas_max = int(df['ventas_estimadas'].min()), int(df['ventas_estimadas'].max())
    rango_ventas = st.slider("Rango de Ventas (M)", ventas_min // 1_000_000, ventas_max // 1_000_000,
                              (ventas_min // 1_000_000, ventas_max // 1_000_000))

    df_f = df[
        (df['subgenero'].isin(sel_sub)) &
        (df['ventas_estimadas'] >= rango_ventas[0] * 1_000_000) &
        (df['ventas_estimadas'] <= rango_ventas[1] * 1_000_000)
    ].copy() if sel_sub else df.copy()

    st.markdown("---")
    st.markdown("<p style='color:#90CAF9;font-weight:600;font-size:.85rem'>📊 ESTADO DEL SISTEMA</p>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#4CAF50'>✔</span> <span style='color:white;font-size:.82rem'>BD conectada</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#4CAF50'>✔</span> <span style='color:white;font-size:.82rem'>{len(df):,} registros históricos</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#4CAF50'>✔</span> <span style='color:white;font-size:.82rem'>{len(df_nlp):,} registros NLP</span>", unsafe_allow_html=True)
    last_update = df['fecha_registro'].max().strftime('%d %b %Y') if len(df) else "—"
    st.markdown(f"<span style='color:#FFB300'>🕐</span> <span style='color:white;font-size:.82rem'>Última ETL: {last_update}</span>", unsafe_allow_html=True)

    st.markdown("---")
    pdf_btn = st.button("📥 Exportar PDF Ejecutivo", use_container_width=True)

# ── HEADER & KPIs ─────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0D1B38 0%,#1B3A6B 60%,#2E75B6 100%);
     border-radius:14px;padding:20px 30px;margin-bottom:24px;
     box-shadow:0 6px 24px rgba(0,0,0,.3)'>
  <h1 style='color:white;margin:0;font-size:1.9rem;font-weight:700'>
    🎮 Steam Analytics BI <span style='color:#64B5F6'>v5.0</span>
  </h1>
  <p style='color:#90CAF9;margin:4px 0 0;font-size:.9rem'>
    Plataforma de Inteligencia de Mercado — Constelación Galáctica (Kimball) + NLP Híbrido
  </p>
</div>
""", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
total_ventas   = df_f['ventas_estimadas'].sum()
total_desc     = df_f['descargas_estimadas'].sum()
avg_satisfaction = (df_f['votos_positivos'].sum() /
                    (df_f['votos_positivos'].sum() + df_f['votos_negativos'].sum()) * 100
                    if (df_f['votos_positivos'].sum() + df_f['votos_negativos'].sum()) > 0 else 0)
n_juegos = df_f['nombre_juego'].nunique()

def kpi_html(val, label, icon):
    return f"""<div class='metric-card'>
        <div class='metric-label'>{icon} {label}</div>
        <div class='metric-value'>{val}</div>
    </div>"""

with k1: st.markdown(kpi_html(f"${total_ventas/1e9:.1f}B", "Ventas Totales", "💰"), unsafe_allow_html=True)
with k2: st.markdown(kpi_html(f"{total_desc/1e6:.0f}M", "Descargas Totales", "⬇️"), unsafe_allow_html=True)
with k3: st.markdown(kpi_html(f"{avg_satisfaction:.1f}%", "Satisfacción Prom.", "⭐"), unsafe_allow_html=True)
with k4: st.markdown(kpi_html(str(n_juegos), "Juegos Activos", "🎯"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Análisis de Mercado",
    "🎛️ Simulador Estratégico",
    "🗄️ Explorador de Datos",
    "☁️ Inteligencia NLP"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANÁLISIS DE MERCADO
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── 1.1 CATÁLOGO VISUAL DE JUEGOS (NUEVO v5.0) ───────────────────────────
    st.markdown("<div class='section-badge'>🎮 Catálogo Visual de Juegos Analizados — Steam CDN</div>", unsafe_allow_html=True)

    game_cols = st.columns(5)
    games_list = list(GAME_IMAGES.items())
    for idx, (game_name, info) in enumerate(games_list):
        col = game_cols[idx % 5]
        # Obtener KPIs del juego
        jdf = df_f[df_f['nombre_juego'].str.contains(game_name.split(":")[0], na=False, case=False)]
        ventas_g = jdf['ventas_estimadas'].sum()
        sat_g = (jdf['votos_positivos'].sum() /
                 (jdf['votos_positivos'].sum() + jdf['votos_negativos'].sum()) * 100
                 if (jdf['votos_positivos'].sum() + jdf['votos_negativos'].sum()) > 0 else 0)
        with col:
            st.markdown(f"""
            <div class='game-card'>
              <img src='{info["img"]}' alt='{game_name}' style='width:100%;height:90px;object-fit:cover'>
              <div class='game-card-info'>
                <div class='game-card-title'>{game_name[:20]}</div>
                <div class='game-card-sub'>💰 ${ventas_g/1e6:.0f}M ventas</div>
                <div class='game-card-sub'>⭐ {sat_g:.1f}% satisf.</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 1.2 SCATTER — VENTAS vs SATISFACCIÓN ─────────────────────────────────
    st.markdown("<div class='section-badge'>🔵 Correlación: Ventas vs Satisfacción por Juego</div>", unsafe_allow_html=True)

    scatter_df = df_f.groupby('nombre_juego').agg(
        ventas=('ventas_estimadas','sum'),
        positivos=('votos_positivos','sum'),
        negativos=('votos_negativos','sum'),
        jugadores=('promedio_jugadores','mean'),
        precio=('precio_usd','mean'),
        subgenero=('subgenero','first')
    ).reset_index()
    scatter_df['satisfaccion'] = (scatter_df['positivos'] /
                                   (scatter_df['positivos'] + scatter_df['negativos']) * 100).round(2)

    fig_scatter = px.scatter(
        scatter_df, x='ventas', y='satisfaccion',
        size='jugadores', color='subgenero', hover_name='nombre_juego',
        hover_data={'precio': True, 'jugadores': ':.0f'},
        trendline='ols', trendline_color_override='#FF4444',
        labels={'ventas': 'Ventas Estimadas (USD)', 'satisfaccion': 'Satisfacción (%)'},
        title='Ventas vs Satisfacción — OLS Trendline',
        template='plotly_dark', height=420,
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig_scatter.update_traces(marker=dict(opacity=0.85, line=dict(width=1, color='white')))
    fig_scatter.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,40,.6)',
                               font_family='Inter', legend_title_text='Subgénero')
    st.plotly_chart(fig_scatter, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        # ── 1.3 DONUT — CUOTA DE MERCADO ─────────────────────────────────
        st.markdown("<div class='section-badge'>🥧 Cuota de Mercado por Subgénero</div>", unsafe_allow_html=True)
        donut_df = df_f.groupby('subgenero')['ventas_estimadas'].sum().reset_index()
        fig_donut = px.pie(donut_df, values='ventas_estimadas', names='subgenero',
                           hole=.45, template='plotly_dark', height=340,
                           color_discrete_sequence=px.colors.qualitative.Bold)
        fig_donut.update_traces(textposition='inside', textinfo='percent+label',
                                 pull=[0.05] * len(donut_df))
        fig_donut.update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=True,
                                  font_family='Inter',
                                  annotations=[dict(text='Mercado', x=.5, y=.5, font_size=14, showarrow=False)])
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_b:
        # ── 1.4 BAR — TOP 10 JUEGOS ──────────────────────────────────────
        st.markdown("<div class='section-badge'>🏆 Top 10 Juegos por Ventas</div>", unsafe_allow_html=True)
        top10 = scatter_df.nlargest(10, 'ventas').sort_values('ventas')
        fig_top = px.bar(top10, x='ventas', y='nombre_juego', orientation='h',
                         color='satisfaccion', color_continuous_scale='Blues',
                         labels={'ventas': 'Ventas (USD)', 'nombre_juego': '', 'satisfaccion': 'Sat.%'},
                         template='plotly_dark', height=340)
        fig_top.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,40,.6)',
                               font_family='Inter', yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)

    # ── 1.5 TIME SERIES ───────────────────────────────────────────────────────
    st.markdown("<div class='section-badge'>📈 Serie Temporal — Ventas e Jugadores Promedio</div>", unsafe_allow_html=True)
    ts_df = df_f.groupby('fecha_registro').agg(
        ventas=('ventas_estimadas', 'sum'),
        jugadores=('promedio_jugadores', 'mean')
    ).reset_index().sort_values('fecha_registro')

    fig_ts = make_subplots(specs=[[{"secondary_y": True}]])
    fig_ts.add_trace(go.Scatter(x=ts_df['fecha_registro'], y=ts_df['ventas'],
                                name='Ventas', fill='tozeroy',
                                line=dict(color='#2E75B6', width=2),
                                fillcolor='rgba(46,117,182,.2)'), secondary_y=False)
    fig_ts.add_trace(go.Scatter(x=ts_df['fecha_registro'], y=ts_df['jugadores'],
                                name='Jugadores Prom.', mode='lines+markers',
                                line=dict(color='#FF8F00', width=2, dash='dot')), secondary_y=True)
    fig_ts.update_layout(template='plotly_dark', height=340,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,40,.6)',
                          font_family='Inter', legend=dict(x=.01, y=.99))
    fig_ts.update_yaxes(title_text="Ventas (USD)", secondary_y=False)
    fig_ts.update_yaxes(title_text="Jugadores Prom.", secondary_y=True)
    st.plotly_chart(fig_ts, use_container_width=True)

    # ── 1.6 BENCHMARKING RADAR + BAR ─────────────────────────────────────────
    st.markdown("<div class='section-badge'>🕸️ Benchmarking Multidimensional</div>", unsafe_allow_html=True)
    bench_metrics = ['ventas', 'satisfaccion', 'jugadores', 'precio']
    bench_df = scatter_df.nlargest(6, 'ventas')

    fig_radar = go.Figure()
    categories = ['Ventas', 'Satisfacción', 'Jugadores', 'Precio']
    for _, row in bench_df.iterrows():
        vals = [
            row['ventas'] / scatter_df['ventas'].max() * 100,
            row['satisfaccion'],
            row['jugadores'] / scatter_df['jugadores'].max() * 100,
            row['precio'] / scatter_df['precio'].max() * 100
        ]
        fig_radar.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=categories + [categories[0]],
                                             name=row['nombre_juego'][:16], fill='toself', opacity=.5))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                             template='plotly_dark', height=380,
                             paper_bgcolor='rgba(0,0,0,0)', font_family='Inter',
                             title='Radar Competitivo — Top 6 Juegos')
    st.plotly_chart(fig_radar, use_container_width=True)

    # Developer bar chart
    dev_df = df_f.groupby('desarrollador')['ventas_estimadas'].sum().nlargest(8).reset_index()
    fig_dev = px.bar(dev_df, x='desarrollador', y='ventas_estimadas',
                     color='ventas_estimadas', color_continuous_scale='Blues',
                     labels={'desarrollador': 'Desarrollador', 'ventas_estimadas': 'Ventas (USD)'},
                     template='plotly_dark', height=300, title='Top Desarrolladores por Ventas')
    fig_dev.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,40,.6)', font_family='Inter')
    st.plotly_chart(fig_dev, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SIMULADOR ESTRATÉGICO
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-badge'>🤖 Simulador What-If — RandomForest Revenue Model (100 árboles, max_depth=12)</div>", unsafe_allow_html=True)

    col_ctrl, col_chart = st.columns([1, 2])

    with col_ctrl:
        st.markdown("#### ⚙️ Parámetros del Escenario")
        precio_sim  = st.slider("Precio USD", 0.0, 80.0, 29.99, 0.5)
        jugadores_sim = st.slider("Jugadores Prom.", 1000, 200000, 50000, 1000)
        meta_sim    = st.slider("Metascore", 40, 100, 75)
        pos_ratio   = st.slider("Ratio Positivos (%)", 30, 100, 80)
        sub_sim     = st.selectbox("Subgénero", subgeneros)
        run_sim     = st.button("🚀 Ejecutar Simulación", use_container_width=True)

    with col_chart:
        if run_sim or True:
            try:
                le = LabelEncoder()
                train = df_f.dropna(subset=['ventas_estimadas', 'precio_usd', 'promedio_jugadores',
                                             'metascore', 'votos_positivos', 'votos_negativos', 'subgenero']).copy()
                train['sub_enc'] = le.fit_transform(train['subgenero'])
                train['pos_ratio'] = train['votos_positivos'] / (train['votos_positivos'] + train['votos_negativos'] + 1)
                X = train[['precio_usd', 'promedio_jugadores', 'metascore', 'pos_ratio', 'sub_enc']]
                y = train['ventas_estimadas']
                rf = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
                rf.fit(X, y)

                sub_enc_val = le.transform([sub_sim])[0] if sub_sim in le.classes_ else 0
                base_input = [[precio_sim, jugadores_sim, meta_sim, pos_ratio / 100, sub_enc_val]]
                pred_base = rf.predict(base_input)[0]

                scenarios = {
                    "🐻 Conservador (-20%)": pred_base * 0.80,
                    "📊 Base (Modelo)": pred_base,
                    "🚀 Optimista (+20%)": pred_base * 1.20
                }

                fig_bar = px.bar(
                    x=list(scenarios.keys()), y=list(scenarios.values()),
                    labels={'x': 'Escenario', 'y': 'Ventas Estimadas (USD)'},
                    color=list(scenarios.keys()),
                    color_discrete_map={
                        "🐻 Conservador (-20%)": "#FF7043",
                        "📊 Base (Modelo)": "#2E75B6",
                        "🚀 Optimista (+20%)": "#43A047"
                    },
                    template='plotly_dark', height=350, title='Proyección de Escenarios'
                )
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,40,.6)',
                                       font_family='Inter', showlegend=False)
                fig_bar.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)

                col_r1, col_r2, col_r3 = st.columns(3)
                for col_r, (sc, val) in zip([col_r1, col_r2, col_r3], scenarios.items()):
                    col_r.metric(sc, f"${val/1e6:.1f}M")

                # Feature importance funnel
                feat_names = ['Precio', 'Jugadores', 'Metascore', 'Satisfacción', 'Subgénero']
                importances = rf.feature_importances_
                fig_funnel = go.Figure(go.Funnel(
                    y=feat_names, x=[i * 100 for i in importances],
                    textinfo='value+percent total',
                    marker_color=['#2E75B6', '#1565C0', '#0D47A1', '#42A5F5', '#90CAF9']
                ))
                fig_funnel.update_layout(template='plotly_dark', height=320,
                                          paper_bgcolor='rgba(0,0,0,0)', font_family='Inter',
                                          title='Importancia de Variables (RandomForest)')
                st.plotly_chart(fig_funnel, use_container_width=True)

            except Exception as e:
                st.error(f"Error en simulación: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — EXPLORADOR DE DATOS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-badge'>🗄️ Explorador Configurable de Datos Históricos</div>", unsafe_allow_html=True)

    col_cfg1, col_cfg2 = st.columns([2, 1])
    with col_cfg1:
        cols_disponibles = ['fecha_registro', 'nombre_juego', 'subgenero', 'desarrollador',
                             'ventas_estimadas', 'descargas_estimadas', 'precio_usd',
                             'votos_positivos', 'votos_negativos', 'promedio_jugadores',
                             'pico_jugadores', 'metascore']
        cols_disp = [c for c in cols_disponibles if c in df_f.columns]
        sel_cols = st.multiselect("Columnas a mostrar", cols_disp, default=cols_disp[:7])
    with col_cfg2:
        ordenar_por = st.selectbox("Ordenar por", [c for c in cols_disp if c in df_f.columns], index=4)
        asc = st.checkbox("Ascendente", value=False)
        n_rows = st.number_input("Filas", min_value=10, max_value=1000, value=50, step=10)

    if sel_cols:
        df_show = df_f[sel_cols].sort_values(ordenar_por, ascending=asc).head(n_rows) if ordenar_por in sel_cols else df_f[sel_cols].head(n_rows)
        st.dataframe(df_show, use_container_width=True, height=350)
        csv = df_f.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV Completo", csv, "steam_analytics_data.csv", "text/csv", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── HEATMAP NUEVO v5.0 ────────────────────────────────────────────────────
    st.markdown("<div class='section-badge'>🔥 Heatmap — Sentimiento por Juego × Mes (NUEVO v5.0)</div>", unsafe_allow_html=True)

    try:
        heat_df = df_nlp.copy()
        heat_df['mes'] = heat_df['fecha_procesamiento'].dt.to_period('M').astype(str)
        heat_pivot = heat_df.groupby(['nombre_juego', 'mes'])['polaridad_roberta'].mean().reset_index()
        heat_pivot = heat_pivot.pivot(index='nombre_juego', columns='mes', values='polaridad_roberta')
        heat_pivot = heat_pivot.fillna(0)

        fig_heat = px.imshow(
            heat_pivot,
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
            aspect='auto',
            labels={'color': 'Polaridad RoBERTa', 'x': 'Mes', 'y': 'Juego'},
            title='🔥 Sentimiento (RoBERTa) por Juego y Mes — Valores positivos = verde, negativos = rojo',
            template='plotly_dark',
            height=420
        )
        fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_family='Inter',
                                xaxis_tickangle=-45, coloraxis_colorbar_title='Polaridad')
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption("📌 El color verde indica sentimiento positivo (RoBERTa > 0), el rojo indica sentimiento negativo. "
                   "La intensidad refleja la magnitud del sentimiento promedio diario.")
    except Exception as e:
        st.warning(f"Heatmap no disponible: {e}")

    # ── INTEGRIDAD DE DATOS ───────────────────────────────────────────────────
    st.markdown("<div class='section-badge'>🔍 Panel de Integridad de Datos</div>", unsafe_allow_html=True)
    col_int1, col_int2 = st.columns(2)
    with col_int1:
        nulls = df_f.isnull().sum()
        null_pct = (nulls / len(df_f) * 100).round(2)
        int_df = pd.DataFrame({'Nulos': nulls, '% Nulos': null_pct, 'Tipo': df_f.dtypes.astype(str)})
        st.dataframe(int_df[int_df['Nulos'] > 0] if int_df['Nulos'].sum() > 0 else int_df.head(8),
                     use_container_width=True)
    with col_int2:
        st.markdown("**📊 Estadísticas de la Muestra Filtrada**")
        st.dataframe(df_f[['ventas_estimadas', 'promedio_jugadores', 'precio_usd',
                             'votos_positivos']].describe().round(0), use_container_width=True)

    # ── MONITORING ────────────────────────────────────────────────────────────
    st.markdown("<div class='section-badge'>⚙️ Monitor de Cobertura por Juego</div>", unsafe_allow_html=True)
    monitor_df = df_f.groupby('nombre_juego').agg(
        registros=('fecha_registro', 'count'),
        primera=('fecha_registro', 'min'),
        ultima=('fecha_registro', 'max')
    ).reset_index()
    monitor_df['primera'] = monitor_df['primera'].dt.strftime('%Y-%m-%d')
    monitor_df['ultima']  = monitor_df['ultima'].dt.strftime('%Y-%m-%d')
    st.dataframe(monitor_df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — INTELIGENCIA NLP PREMIUM
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-badge'>☁️ Inteligencia NLP Premium — VADER + TextBlob + RoBERTa Híbrido</div>", unsafe_allow_html=True)

    juegos_nlp = sorted(df_nlp['nombre_juego'].unique().tolist())

    col_ctrl1, col_main = st.columns([1, 3])

    with col_ctrl1:
        # ── BANNER DEL JUEGO (NUEVO v5.0) ────────────────────────────────
        juego_sel = st.selectbox("🎮 Selecciona Juego", juegos_nlp)

        # Mostrar banner del juego seleccionado
        matched_key = None
        for gname, ginfo in GAME_IMAGES.items():
            if any(part.lower() in juego_sel.lower() for part in gname.split(":")):
                matched_key = gname
                break

        if matched_key:
            st.markdown(f"""
            <div style='border-radius:8px;overflow:hidden;margin:8px 0;
                         box-shadow:0 4px 14px rgba(0,0,0,.35)'>
              <img src='{GAME_IMAGES[matched_key]["img"]}' style='width:100%' alt='{matched_key}'>
              <div style='background:#1B3A6B;color:white;padding:6px 10px;font-size:.8rem;font-weight:600'>
                🎮 {matched_key}<br>
                <span style='color:#90CAF9;font-weight:400'>AppID: {GAME_IMAGES[matched_key]["appid"]}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        df_j = df_nlp[df_nlp['nombre_juego'] == juego_sel].copy()
        df_j = df_j.sort_values('fecha_procesamiento')

        if len(df_j) == 0:
            st.warning("Sin datos NLP para este juego.")
        else:
            last_row = df_j.iloc[-1]
            polarity  = last_row.get('polaridad_roberta', last_row.get('polaridad_score', 0))
            clasif    = last_row.get('clasificacion_sentimiento', 'N/A')
            tema      = last_row.get('tema_principal', 'N/A')
            conteo    = int(last_row.get('conteo_resenas', 0))

            # Context badges
            color_clasif = "#4CAF50" if 'pos' in str(clasif).lower() else "#F44336" if 'neg' in str(clasif).lower() else "#FF9800"
            st.markdown(f"""
            <div style='background:#1B3A6B;border-radius:8px;padding:12px;margin-top:8px'>
              <div style='color:#90CAF9;font-size:.75rem;font-weight:600'>ÚLTIMO ANÁLISIS</div>
              <div style='color:white;font-size:.88rem;margin-top:6px'>
                <span style='background:{color_clasif};border-radius:4px;padding:2px 8px;font-weight:700'>
                  {clasif}
                </span>
              </div>
              <div style='color:#B0BEC5;font-size:.78rem;margin-top:6px'>
                📌 Tema: <b style='color:white'>{str(tema)[:22]}</b><br>
                📝 Reseñas: <b style='color:white'>{conteo:,}</b><br>
                📅 {last_row['fecha_procesamiento'].strftime('%d/%m/%Y')}
              </div>
            </div>
            """, unsafe_allow_html=True)

    with col_main:
        if len(df_j) > 0:
            # ── TERMÓMETRO VADER ──────────────────────────────────────────
            st.markdown("#### 🌡️ Termómetro de Sentimiento (VADER/RoBERTa)")
            pol_val = float(df_j['polaridad_roberta'].mean() if 'polaridad_roberta' in df_j.columns else df_j['polaridad_score'].mean())
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=round(pol_val, 4),
                delta={'reference': 0, 'increasing': {'color': '#4CAF50'}, 'decreasing': {'color': '#F44336'}},
                gauge={
                    'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': 'white'},
                    'bar': {'color': '#2E75B6'},
                    'bgcolor': 'rgba(0,0,0,0)',
                    'borderwidth': 2,
                    'bordercolor': 'gray',
                    'steps': [
                        {'range': [-1, -0.05], 'color': 'rgba(244,67,54,.4)'},
                        {'range': [-0.05, 0.05], 'color': 'rgba(255,152,0,.3)'},
                        {'range': [0.05, 1], 'color': 'rgba(76,175,80,.4)'}
                    ],
                    'threshold': {'line': {'color': 'white', 'width': 3}, 'thickness': .8, 'value': pol_val}
                },
                title={'text': f"Polaridad Promedio — {juego_sel}", 'font': {'size': 14, 'color': 'white'}}
            ))
            fig_gauge.update_layout(height=280, template='plotly_dark',
                                     paper_bgcolor='rgba(0,0,0,0)', font_family='Inter',
                                     font_color='white')
            st.plotly_chart(fig_gauge, use_container_width=True)

            # ── GRÁFICO HISTÓRICO DUAL-AXIS ───────────────────────────────
            st.markdown("#### 📈 Histórico de Sentimiento y Actividad")
            fig_hist = make_subplots(specs=[[{"secondary_y": True}]])
            fig_hist.add_trace(go.Scatter(
                x=df_j['fecha_procesamiento'],
                y=df_j['polaridad_roberta'] if 'polaridad_roberta' in df_j.columns else df_j['polaridad_score'],
                name='Polaridad', line=dict(color='#2E75B6', width=2), fill='tozeroy',
                fillcolor='rgba(46,117,182,.15)'
            ), secondary_y=False)
            if 'promedio_jugadores_dia' in df_j.columns:
                fig_hist.add_trace(go.Scatter(
                    x=df_j['fecha_procesamiento'], y=df_j['promedio_jugadores_dia'],
                    name='Jugadores/día', line=dict(color='#FF8F00', width=2, dash='dot'),
                    mode='lines+markers', marker=dict(size=4)
                ), secondary_y=True)
            fig_hist.update_layout(template='plotly_dark', height=300,
                                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,40,.6)',
                                    font_family='Inter', legend=dict(x=.01, y=.99))
            fig_hist.update_yaxes(title_text="Polaridad RoBERTa", secondary_y=False)
            fig_hist.update_yaxes(title_text="Jugadores/día", secondary_y=True)
            st.plotly_chart(fig_hist, use_container_width=True)

    # ── WORD CLOUD (NUEVO v5.0) ────────────────────────────────────────────────
    if len(df_j) > 0 and 'tema_principal' in df_j.columns:
        st.markdown("---")
        st.markdown("<div class='section-badge'>☁️ Word Cloud — Temas Principales de la Comunidad (NUEVO v5.0)</div>", unsafe_allow_html=True)

        temas_texto = " ".join(df_j['tema_principal'].dropna().astype(str).tolist())

        if len(temas_texto.strip()) > 5:
            try:
                custom_stopwords = set(STOPWORDS) | {
                    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                    'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into',
                    'game', 'games', 'steam', 'play', 'player', 'players',
                    'el', 'la', 'los', 'las', 'de', 'del', 'en', 'y', 'que',
                    'se', 'es', 'un', 'una', 'su', 'por', 'con'
                }

                wc = WordCloud(
                    width=900, height=380,
                    background_color='#0e1117',
                    colormap='Blues',
                    stopwords=custom_stopwords,
                    max_words=80,
                    min_font_size=10,
                    max_font_size=90,
                    prefer_horizontal=0.8,
                    random_state=42
                ).generate(temas_texto)

                fig_wc, ax = plt.subplots(figsize=(10, 4))
                fig_wc.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                ax.imshow(wc, interpolation='bilinear')
                ax.axis('off')
                ax.set_title(f'Temas más frecuentes en reseñas de {juego_sel}',
                              color='white', fontsize=13, pad=10, fontweight='bold')
                plt.tight_layout(pad=0)

                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                             facecolor='#0e1117', edgecolor='none')
                buf.seek(0)
                plt.close(fig_wc)
                st.image(buf, use_container_width=True)
                st.caption(f"☁️ Word Cloud generado a partir de {len(df_j)} registros de `tema_principal` para {juego_sel}. "
                           "El tamaño de cada palabra refleja su frecuencia en las reseñas de la comunidad.")
            except Exception as e:
                st.warning(f"Word Cloud no disponible: {e}")
        else:
            st.info("No hay suficiente texto de temas para generar el Word Cloud.")

    # ── TABLA NLP RESUMEN ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-badge'>📋 Resumen NLP por Juego</div>", unsafe_allow_html=True)
    nlp_summary = df_nlp.groupby('nombre_juego').agg(
        registros=('fecha_procesamiento', 'count'),
        polaridad_media=('polaridad_roberta', 'mean'),
        polaridad_min=('polaridad_roberta', 'min'),
        polaridad_max=('polaridad_roberta', 'max'),
        resenas_total=('conteo_resenas', 'sum')
    ).round(4).reset_index()

    def color_polarity(val):
        if isinstance(val, float):
            color = '#4CAF50' if val > 0.05 else '#F44336' if val < -0.05 else '#FF9800'
            return f'color: {color}; font-weight: bold'
        return ''

    st.dataframe(
        nlp_summary.style.applymap(color_polarity, subset=['polaridad_media']),
        use_container_width=True, height=280
    )


# ── PDF EXPORT ────────────────────────────────────────────────────────────────
if pdf_btn:
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(27, 58, 107)
        pdf.cell(0, 12, "Steam Analytics BI v5.0 — Reporte Ejecutivo", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, f"Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} | Farid Rodriguez Puc", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 9, "KPIs Principales", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, f"Ventas Totales: ${total_ventas/1e9:.2f}B USD", ln=True)
        pdf.cell(0, 7, f"Descargas: {total_desc/1e6:.0f}M", ln=True)
        pdf.cell(0, 7, f"Satisfaccion Promedio: {avg_satisfaction:.1f}%", ln=True)
        pdf.cell(0, 7, f"Juegos Monitoreados: {n_juegos}", ln=True)
        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 9, "Top 5 Juegos por Ventas", ln=True)
        pdf.set_font("Arial", "", 10)
        for _, row in scatter_df.nlargest(5, 'ventas').iterrows():
            pdf.cell(0, 7, f"  {row['nombre_juego']}: ${row['ventas']/1e6:.1f}M | Sat: {row['satisfaccion']:.1f}%", ln=True)
        pdf.ln(4)
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 7, "Modelo: Constellacion Galactica (Kimball) | NLP: VADER+TextBlob+RoBERTa | ML: RandomForest", ln=True)

        pdf_bytes = bytes(pdf.output())
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="SteamBI_Reporte_v5.pdf" style="color:#2E75B6;font-weight:700">📥 Descargar Reporte PDF</a>'
        st.sidebar.markdown(href, unsafe_allow_html=True)
        st.sidebar.success("✅ PDF generado!")
    except Exception as e:
        st.sidebar.error(f"Error PDF: {e}")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style='margin-top:40px;border-color:#1B3A6B'>
<div style='text-align:center;color:#555;font-size:.8rem;padding:12px 0'>
  🎮 <b>Steam Analytics BI v5.0</b> — TecNM Ingeniería Informática — Farid Rodriguez Puc<br>
  🔗 <a href='https://github.com/farmaniux/resenas_steam' target='_blank' style='color:#2E75B6'>github.com/farmaniux/resenas_steam</a> &nbsp;|&nbsp;
  ETL: GitHub Actions 02:20 AM &nbsp;|&nbsp; Modelo: Constelación Galáctica (Kimball) &nbsp;|&nbsp; NLP: VADER+TextBlob+RoBERTa
</div>
""", unsafe_allow_html=True)
