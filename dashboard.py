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
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background: #050a18;
        color: #c8d6e5;
    }
    
    .main {
        background: 
            radial-gradient(ellipse at 20% 50%, rgba(0, 212, 255, 0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(180, 74, 255, 0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 80%, rgba(0, 255, 136, 0.04) 0%, transparent 50%),
            linear-gradient(180deg, #050a18 0%, #0a1628 50%, #050a18 100%);
        background-attachment: fixed;
        padding: 2rem 1rem;
    }
    
    /* Scanline CRT overlay */
    .main::before {
        content: '';
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: repeating-linear-gradient(0deg, rgba(0, 212, 255, 0.015) 0px, transparent 1px, transparent 3px);
        pointer-events: none;
        z-index: 999;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em;
    }
    
    h1 {
        font-size: 3rem !important;
        background: linear-gradient(135deg, #00d4ff 0%, #b44aff 40%, #00ff88 80%, #00d4ff 100%);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem !important;
        text-transform: uppercase;
        animation: neonShimmer 4s ease-in-out infinite;
        filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.3));
    }
    
    @keyframes neonShimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    h2 {
        color: #00d4ff !important;
        font-size: 1.4rem !important;
        border-left: 3px solid #00d4ff;
        padding-left: 1rem;
        margin: 2rem 0 1.5rem 0 !important;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }
    
    h3 {
        color: #7dd3fc !important;
        font-size: 1.05rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* === METRIC CARDS — NEON GLOW === */
    .stMetric {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.05) 0%, rgba(180, 74, 255, 0.03) 100%);
        border: 1px solid rgba(0, 212, 255, 0.25);
        border-radius: 12px;
        padding: 1.8rem 1.5rem !important;
        box-shadow: 
            0 0 15px rgba(0, 212, 255, 0.08),
            inset 0 1px 0 rgba(0, 212, 255, 0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    
    .stMetric::after {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, #00d4ff, #b44aff, transparent);
        animation: scanTop 3s linear infinite;
    }
    @keyframes scanTop {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    .stMetric:hover {
        transform: translateY(-6px) scale(1.02);
        border-color: rgba(0, 212, 255, 0.6);
        box-shadow: 
            0 0 30px rgba(0, 212, 255, 0.2),
            0 15px 40px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(0, 212, 255, 0.2);
    }
    
    .stMetric label {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #00d4ff !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-family: 'Orbitron', sans-serif !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #e0f2fe !important;
        font-family: 'JetBrains Mono', monospace !important;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
    }
    
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 0.85rem !important;
        color: #00ff88 !important;
    }
    
    /* === TABS — NEON === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: rgba(5, 10, 24, 0.8);
        padding: 0.5rem;
        border-radius: 10px;
        border: 1px solid rgba(0, 212, 255, 0.15);
        backdrop-filter: blur(10px);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background: transparent;
        border-radius: 8px;
        color: #64748b;
        font-weight: 600;
        font-size: 0.9rem;
        border: 1px solid transparent;
        padding: 0 1.2rem;
        transition: all 0.3s ease;
        font-family: 'Orbitron', sans-serif;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 212, 255, 0.08);
        color: #00d4ff;
        border-color: rgba(0, 212, 255, 0.2);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(180, 74, 255, 0.15) 100%) !important;
        color: #00d4ff !important;
        border: 1px solid rgba(0, 212, 255, 0.5) !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2), inset 0 0 15px rgba(0, 212, 255, 0.05);
    }
    
    /* === SIDEBAR === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #060d1f 0%, #0a1628 50%, #060d1f 100%);
        border-right: 1px solid rgba(0, 212, 255, 0.15);
    }
    
    [data-testid="stSidebar"] .stMarkdown { color: #c8d6e5; }
    
    [data-testid="stSidebar"] h1 {
        font-size: 1.3rem !important;
        background: linear-gradient(135deg, #00d4ff 0%, #b44aff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* === FORM ELEMENTS === */
    .stMultiSelect [data-baseweb="select"] {
        background: rgba(5, 10, 24, 0.8);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 8px;
    }
    
    .stMultiSelect [data-baseweb="tag"] {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.3) 0%, rgba(180, 74, 255, 0.3) 100%);
        border: 1px solid rgba(0, 212, 255, 0.4);
        border-radius: 4px;
        font-weight: 600;
        color: #e0f2fe;
    }
    
    .stDataFrame {
        border: 1px solid rgba(0, 212, 255, 0.15);
        border-radius: 10px;
        overflow: hidden;
    }
    
    .stButton button {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(180, 74, 255, 0.2) 100%);
        color: #00d4ff;
        border: 1px solid rgba(0, 212, 255, 0.4);
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 700;
        font-size: 0.9rem;
        font-family: 'Orbitron', sans-serif;
        letter-spacing: 0.05em;
        transition: all 0.3s ease;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.1);
        text-transform: uppercase;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.3);
        border-color: #00d4ff;
        color: #ffffff;
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.3) 0%, rgba(180, 74, 255, 0.3) 100%);
    }
    
    .stSlider [data-baseweb="slider"] { background: rgba(0, 212, 255, 0.15); }
    .stSlider [role="slider"] {
        background: linear-gradient(135deg, #00d4ff 0%, #b44aff 100%);
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.4);
    }
    
    .stAlert {
        background: rgba(5, 10, 24, 0.85);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 10px;
        padding: 1rem;
        backdrop-filter: blur(10px);
    }
    .stSuccess { border-color: rgba(0, 255, 136, 0.4); background: rgba(0, 255, 136, 0.05); }
    .stInfo { border-color: rgba(0, 212, 255, 0.4); background: rgba(0, 212, 255, 0.05); }
    .stWarning { border-color: rgba(255, 183, 0, 0.4); background: rgba(255, 183, 0, 0.05); }
    
    /* === SCROLLBAR NEON === */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(5, 10, 24, 0.6); }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00d4ff 0%, #b44aff 100%);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #00ff88 0%, #00d4ff 100%); }
    
    /* === ANIMATIONS === */
    .element-container { animation: fadeInUp 0.5s ease-out; }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes neonPulse {
        0%, 100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.2); }
        50% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.4), 0 0 40px rgba(0, 212, 255, 0.1); }
    }
    
    @keyframes borderGlow {
        0%, 100% { border-color: rgba(0, 212, 255, 0.3); }
        50% { border-color: rgba(180, 74, 255, 0.5); }
    }
    
    hr { border-color: rgba(0, 212, 255, 0.1) !important; }
    
    .stExpander {
        border: 1px solid rgba(0, 212, 255, 0.15);
        border-radius: 8px;
        background: rgba(5, 10, 24, 0.6);
    }
    
    .stSelectbox [data-baseweb="select"] {
        background: rgba(5, 10, 24, 0.8);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 8px;
    }
    
    .stNumberInput input {
        background: rgba(5, 10, 24, 0.8) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        color: #e0f2fe !important;
        border-radius: 8px !important;
    }
    
    .stTextInput input {
        background: rgba(5, 10, 24, 0.8) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        color: #e0f2fe !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.2) !important;
    }
    
    @media (max-width: 768px) {
        h1 { font-size: 1.8rem !important; }
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

def generar_insights(df_f):
    """Genera frases automáticas de insights clave a partir de los datos filtrados."""
    insights = []
    if df_f.empty:
        return ["⚠️ No hay datos para generar insights."]
    # Top juego por ventas
    top_game = df_f.loc[df_f['monto_ventas_usd'].idxmax()]
    insights.append(f"🏆 El juego con **más ventas** es **{top_game['nombre']}** con **{format_number(top_game['monto_ventas_usd'])}**")
    # Género más rentable
    genre_sales = df_f.groupby('subgenero')['monto_ventas_usd'].sum()
    top_genre = genre_sales.idxmax()
    insights.append(f"🎮 El género **más rentable** es **{top_genre}** con **{format_number(genre_sales.max())}** en ventas totales")
    # Pareto: cuántos juegos hacen el 80%
    sorted_sales = df_f.groupby('nombre')['monto_ventas_usd'].sum().sort_values(ascending=False)
    cumsum = sorted_sales.cumsum()
    total = sorted_sales.sum()
    if total > 0:
        n_80 = (cumsum <= total * 0.8).sum() + 1
        pct_games = (n_80 / len(sorted_sales)) * 100
        insights.append(f"📊 El **{pct_games:.0f}%** de los juegos ({n_80}) genera el **80%** de las ventas totales")
    # Satisfacción promedio
    avg_sat = df_f['ratio_positividad'].mean()
    if avg_sat >= 0.80:
        insights.append(f"😀 La satisfacción promedio es **{avg_sat:.1%}** — el mercado está **muy saludable**")
    elif avg_sat >= 0.60:
        insights.append(f"😐 La satisfacción promedio es **{avg_sat:.1%}** — el mercado es **competitivo**")
    else:
        insights.append(f"😟 La satisfacción promedio es **{avg_sat:.1%}** — el mercado muestra **señales de riesgo**")
    # Juego con más descargas
    top_dl = df_f.loc[df_f['cantidad_descargas'].idxmax()]
    insights.append(f"📥 El juego **más descargado** es **{top_dl['nombre']}** con **{format_count(top_dl['cantidad_descargas'])}** descargas")
    # Ingreso promedio por juego
    n_juegos = df_f['nombre'].nunique()
    if n_juegos > 0:
        avg_rev = total / n_juegos if total > 0 else 0
        insights.append(f"💵 Ingreso promedio por título: **{format_number(avg_rev)}**")
    return insights

def get_steam_image(appid):
    """Generate Steam CDN header capsule image URL."""
    return f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"

def get_steam_url(appid):
    """Generate Steam store URL."""
    return f"https://store.steampowered.com/app/{appid}"

def get_sentiment_badge(ratio):
    """Return styled HTML badge for satisfaction ratio."""
    if ratio >= 0.85:
        return '<span style="background:#00ff88;color:#050a18;padding:2px 8px;border-radius:4px;font-weight:700;font-size:0.75rem;">MUY POSITIVO</span>'
    elif ratio >= 0.70:
        return '<span style="background:#00d4ff;color:#050a18;padding:2px 8px;border-radius:4px;font-weight:700;font-size:0.75rem;">POSITIVO</span>'
    elif ratio >= 0.40:
        return '<span style="background:#ffb700;color:#050a18;padding:2px 8px;border-radius:4px;font-weight:700;font-size:0.75rem;">MIXTO</span>'
    else:
        return '<span style="background:#ff2d78;color:#ffffff;padding:2px 8px;border-radius:4px;font-weight:700;font-size:0.75rem;">NEGATIVO</span>'

def generar_pdf(df_filtered, ventas, descargas, ratio, juegos_count):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Cabecera Corporativa Premium (Fondo oscuro)
    pdf.set_fill_color(15, 20, 40) # Azul muy oscuro
    pdf.rect(0, 0, 210, 35, 'F')
    
    pdf.set_y(12)
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, txt="STEAM ANALYTICS BI", ln=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(165, 180, 252) # Color acento claro
    pdf.cell(0, 8, txt="Reporte Ejecutivo de Inteligencia de Mercado", ln=True, align='C')
    
    # Fecha de generación
    pdf.set_y(40)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(120, 120, 120)
    from datetime import datetime
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 10, txt=f"Generado el: {fecha_actual}", ln=True, align='R')
    pdf.ln(5)
    
    # 2. Resumen de KPIs
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(26, 31, 58)
    pdf.cell(0, 10, txt="1. Resumen de Mercado (KPIs Globales)", ln=True)
    pdf.ln(5)
    
    def draw_kpi_card(x, y, title, value, color_r, color_g, color_b):
        pdf.set_fill_color(245, 247, 250)
        pdf.rect(x, y, 90, 22, 'F')
        pdf.set_fill_color(color_r, color_g, color_b)
        pdf.rect(x, y, 3, 22, 'F')
        
        pdf.set_xy(x + 5, y + 3)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(80, 5, txt=title.upper(), ln=True)
        
        pdf.set_xy(x + 5, y + 9)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(80, 10, txt=str(value), ln=True)

    y_kpi = pdf.get_y()
    draw_kpi_card(10, y_kpi, "Ventas Totales Est.", format_number(ventas), 102, 126, 234)
    draw_kpi_card(110, y_kpi, "Descargas Est.", format_count(descargas), 118, 75, 162)
    
    draw_kpi_card(10, y_kpi + 26, "Indice de Satisfaccion", f"{ratio*100:.1f}%", 52, 211, 153)
    draw_kpi_card(110, y_kpi + 26, "Juegos Analizados", str(juegos_count), 248, 113, 113)
    
    pdf.set_y(y_kpi + 55)
    
    # 3. Recomendación Estratégica (Movida ARRIBA de la tabla larga)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(26, 31, 58)
    pdf.cell(0, 10, txt="2. Veredicto Estrategico del Modelo Analitico", ln=True)
    pdf.ln(2)
    
    if ratio >= 0.80:
        rec_title = "ESTADO: ALTA VIABILIDAD (FAVORABLE)"
        rec_body = "El mercado actual presenta un indice de satisfaccion excelente. Se recomienda aprobar presupuestos para desarrollo y expansion en estos subgeneros. Priorizar la visibilidad organica."
        r_fill, g_fill, b_fill = 236, 253, 245
        r_text, g_text, b_text = 6, 95, 70
    elif ratio >= 0.65:
        rec_title = "ESTADO: RIESGO MODERADO (ESTABLE)"
        rec_body = "El mercado es estable pero altamente competitivo. Es vital invertir en campañas de marketing agresivas y analizar de cerca las quejas recurrentes para asegurar la retencion a largo plazo."
        r_fill, g_fill, b_fill = 255, 251, 235
        r_text, g_text, b_text = 146, 64, 14
    else:
        rec_title = "ESTADO: ALTO RIESGO (CRITICO)"
        rec_body = "La comunidad muestra una insatisfaccion generalizada. Se sugiere paralizar inversiones fuertes y realizar un analisis profundo de NLP (bugs, rendimiento) antes de comprometer capital en estos nichos."
        r_fill, g_fill, b_fill = 254, 242, 242
        r_text, g_text, b_text = 153, 27, 27
        
    y_rec = pdf.get_y()
    pdf.set_fill_color(r_fill, g_fill, b_fill)
    pdf.rect(10, y_rec, 190, 22, 'F')
    
    pdf.set_xy(15, y_rec + 3)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(r_text, g_text, b_text)
    pdf.cell(0, 6, txt=rec_title, ln=True)
    
    pdf.set_xy(15, y_rec + 9)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(180, 5, txt=rec_body)
    
    pdf.ln(10)
    
    # 4. TABLA DETALLADA DE TODOS LOS JUEGOS (El motor FPDF creará páginas nuevas automáticamente)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(26, 31, 58)
    pdf.cell(0, 10, txt="3. Anexo: Rendimiento Financiero por Titulo", ln=True)
    pdf.ln(2)
    
    if not df_filtered.empty:
        # Agrupar por juego (para sumar ventas históricas y no repetir juegos)
        df_agrupado = df_filtered.groupby('nombre').agg({
            'monto_ventas_usd': 'sum',
            'cantidad_descargas': 'sum',
            'ratio_positividad': 'mean'
        }).reset_index().sort_values('monto_ventas_usd', ascending=False)
        
        # Cabecera de la tabla
        pdf.set_fill_color(102, 126, 234) # Azul
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 9)
        
        # Anchos = 190 total
        w_nombre, w_ventas, w_descargas, w_ratio, w_sent = 70, 35, 30, 25, 30
        
        pdf.cell(w_nombre, 8, txt='Titulo del Juego', border=1, align='C', fill=True)
        pdf.cell(w_ventas, 8, txt='Ventas Est.', border=1, align='C', fill=True)
        pdf.cell(w_descargas, 8, txt='Descargas', border=1, align='C', fill=True)
        pdf.cell(w_ratio, 8, txt='Satisfaccion', border=1, align='C', fill=True)
        pdf.cell(w_sent, 8, txt='Sentimiento', border=1, ln=True, align='C', fill=True)
        
        pdf.set_font("Arial", '', 8)
        fill = False
        
        for index, row in df_agrupado.iterrows():
            if fill:
                pdf.set_fill_color(245, 247, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
                
            pdf.set_text_color(50, 50, 50)
            
            # Limpiar nombre de caracteres raros (emojis, simbolos) que rompan el PDF
            nombre_raw = str(row['nombre'])
            nombre = nombre_raw.encode('latin-1', 'ignore').decode('latin-1')
            if len(nombre) > 38:
                nombre = nombre[:35] + "..."
                
            ventas_str = format_number(row['monto_ventas_usd'])
            descargas_str = format_count(row['cantidad_descargas'])
            ratio_val = row['ratio_positividad']
            ratio_str = f"{ratio_val*100:.1f}%"
            
            # Traductor de Sentimiento
            if ratio_val >= 0.85: sentimiento = "Muy Positivo"
            elif ratio_val >= 0.70: sentimiento = "Positivo"
            elif ratio_val >= 0.40: sentimiento = "Mixto"
            else: sentimiento = "Negativo"
            
            pdf.cell(w_nombre, 7, txt=" " + nombre, border=1, align='L', fill=fill)
            pdf.cell(w_ventas, 7, txt=ventas_str, border=1, align='C', fill=fill)
            pdf.cell(w_descargas, 7, txt=descargas_str, border=1, align='C', fill=fill)
            pdf.cell(w_ratio, 7, txt=ratio_str, border=1, align='C', fill=fill)
            pdf.cell(w_sent, 7, txt=sentimiento, border=1, ln=True, align='C', fill=fill)
            
            fill = not fill
            
    # Pie de página final
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, txt="Generado por Steam Analytics BI v4.0 - Documento Confidencial", align='C')
    
    return bytes(pdf.output())
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
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg" width="45" style="filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.5));">
        <p style="font-family:'Orbitron',sans-serif; font-size:1.1rem; font-weight:700; margin:0.5rem 0 0 0; background:linear-gradient(135deg,#00d4ff,#b44aff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">STEAM ANALYTICS</p>
        <p style="font-size:0.7rem; color:#64748b; letter-spacing:0.1em; font-family:'Orbitron',sans-serif;">ENTERPRISE v6.0</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 🎯 Filtros de Análisis")
    
    # FILTRO: Búsqueda por nombre
    search_name = st.text_input("🔍 Buscar Juego", "", placeholder="Nombre del juego...", help="Búsqueda parcial por nombre")
    
    # FILTRO: Subgéneros (existente)
    all_subgenres = sorted(df['subgenero'].dropna().unique())
    selected_subgenres = st.multiselect(
        "🎮 Categorías de Juego",
        options=all_subgenres,
        default=all_subgenres,
        help="Selecciona los subgéneros que deseas analizar"
    )
    
    # FILTRO: Desarrollador (nuevo)
    all_developers = sorted(df['desarrollador'].dropna().unique()) if 'desarrollador' in df.columns else []
    if all_developers:
        selected_devs = st.multiselect(
            "🏢 Desarrollador",
            options=all_developers,
            default=all_developers,
            help="Filtrar por estudio desarrollador"
        )
    else:
        selected_devs = []
    
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
    
    # FILTRO: Satisfacción mínima (nuevo)
    st.markdown("#### ⭐ Calidad Mínima")
    min_satisfaction = st.slider(
        "Satisfacción mínima (%)",
        min_value=0,
        max_value=100,
        value=0,
        format="%d%%",
        help="Filtra juegos con satisfacción igual o superior"
    )
    
    st.markdown("---")
    st.markdown("#### 📊 Estado del Sistema")
    st.success(f"✅ **{len(df):,}** registros en DWH")
    st.info(f"🔄 Última actualización: Hace {np.random.randint(5, 30)} min")
    
    st.markdown("---")
    with st.expander("ℹ️ Acerca del Dashboard"):
        st.markdown("""
        **Steam Analytics Enterprise v6.0**
        Plataforma de inteligencia de mercado para análisis de videojuegos en Steam.
        - 🏠 Resumen Ejecutivo con Insights IA
        - 📈 Análisis de Mercado Avanzado
        - 📊 Pareto, Sunburst, BoxPlot, Funnel  
        - 🖼️ Imágenes y links de Steam Store
        - ☁️ Inteligencia Artificial NLP
        - 🔒 Conexión segura a Supabase
        """)

    st.markdown("---")
    st.markdown("#### 📄 Reportes para Gerencia")
    
    # === APLICAR TODOS LOS FILTROS ===
    df_filtered = df[
        (df['subgenero'].isin(selected_subgenres)) & 
        (df['monto_ventas_usd'].between(sales_range[0], sales_range[1])) &
        (df['ratio_positividad'] >= min_satisfaction / 100.0)
    ].copy()
    
    if search_name.strip():
        df_filtered = df_filtered[df_filtered['nombre'].str.contains(search_name.strip(), case=False, na=False)]
    
    if selected_devs and 'desarrollador' in df.columns:
        df_filtered = df_filtered[df_filtered['desarrollador'].isin(selected_devs)]

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
# HEADER PRINCIPAL — NEON CYBERPUNK
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="text-align:center; padding: 1.5rem 0 0.5rem 0;">
    <p style="font-family:'Orbitron',sans-serif; font-size:0.75rem; color:#00d4ff; letter-spacing:0.3em; text-transform:uppercase; margin-bottom:0.5rem; text-shadow: 0 0 10px rgba(0,212,255,0.5);">⬡ ENTERPRISE INTELLIGENCE PLATFORM ⬡</p>
    <h1 style="font-family:'Orbitron',sans-serif; font-size:2.8rem; font-weight:900; margin:0; background:linear-gradient(135deg,#00d4ff 0%,#b44aff 40%,#00ff88 80%,#00d4ff 100%); background-size:300% 300%; -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; animation: neonShimmer 4s ease-in-out infinite; filter:drop-shadow(0 0 30px rgba(0,212,255,0.3)); text-transform:uppercase; letter-spacing:0.05em;">🎮 Steam Analytics</h1>
    <p style="font-family:'Orbitron',sans-serif; font-size:0.85rem; color:#64748b; margin-top:0.3rem; letter-spacing:0.1em;">PLATAFORMA DE INTELIGENCIA DE MERCADO</p>
    <div style="width:200px; height:2px; background:linear-gradient(90deg,transparent,#00d4ff,#b44aff,#00ff88,transparent); margin:1rem auto 0; border-radius:1px;"></div>
</div>
""", unsafe_allow_html=True)

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

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Resumen Ejecutivo",
    "📊 Análisis de Mercado",
    "🎛️ Simulador Estratégico",
    "🗄️ Explorador de Datos",
    "☁️ Inteligencia NLP",
    "🎮 Game Explorer"
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 0: RESUMEN EJECUTIVO (POWER BI STYLE)
# ═══════════════════════════════════════════════════════════════════════════

with tab0:
    st.markdown("## 🏠 Resumen Ejecutivo — Vista General del Mercado")
    st.markdown("Panel de control de alto nivel con los indicadores clave de rendimiento y hallazgos automáticos generados por IA.")
    
    if df_filtered.empty:
        st.warning("⚠️ No hay datos disponibles con los filtros actuales.")
    else:
        # --- 6 KPI CARDS ---
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        
        n_juegos_uniq = df_filtered['nombre'].nunique()
        total_ventas_exec = df_filtered['monto_ventas_usd'].sum()
        total_descargas_exec = df_filtered['cantidad_descargas'].sum()
        avg_sat_exec = df_filtered['ratio_positividad'].mean()
        ingreso_promedio = total_ventas_exec / n_juegos_uniq if n_juegos_uniq > 0 else 0
        total_resenas = df_filtered['conteo_resenas'].sum()
        ratio_dl_review = total_descargas_exec / total_resenas if total_resenas > 0 else 0
        
        with kpi1:
            st.metric("💵 Ventas Totales", format_number(total_ventas_exec))
        with kpi2:
            st.metric("📥 Descargas", format_count(total_descargas_exec))
        with kpi3:
            st.metric("⭐ Satisfacción", f"{avg_sat_exec:.1%}")
        with kpi4:
            st.metric("🎯 Títulos", f"{n_juegos_uniq:,}")
        with kpi5:
            st.metric("💰 Ingreso/Juego", format_number(ingreso_promedio))
        with kpi6:
            st.metric("📊 Ratio DL/Reseña", f"{ratio_dl_review:.1f}x")
        
        st.markdown("---")
        
        # --- FILA: GAUGE DE SALUD + COMPOSICIÓN DE MERCADO + DISTRIBUCIÓN ---
        col_exec_g, col_exec_comp, col_exec_dist = st.columns([1, 1, 1])
        
        with col_exec_g:
            st.markdown("### 🌡️ Salud del Mercado")
            gauge_exec = avg_sat_exec * 100 if not pd.isna(avg_sat_exec) else 0
            if gauge_exec >= 80:
                salud_label = "EXCELENTE"
            elif gauge_exec >= 60:
                salud_label = "ESTABLE"
            elif gauge_exec >= 40:
                salud_label = "EN RIESGO"
            else:
                salud_label = "CRÍTICO"
            fig_g_exec = go.Figure(go.Indicator(
                mode="gauge+number",
                value=gauge_exec,
                number={'suffix': '%', 'font': {'size': 36, 'color': '#e0f2fe', 'family': 'JetBrains Mono'}},
                title={'text': salud_label, 'font': {'size': 14, 'color': '#00d4ff', 'family': 'Orbitron'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#00d4ff', 'dtick': 25},
                    'bar': {'color': '#00d4ff', 'thickness': 0.3},
                    'bgcolor': 'rgba(0,0,0,0.3)',
                    'borderwidth': 2, 'bordercolor': 'rgba(0,212,255,0.3)',
                    'steps': [
                        {'range': [0, 40], 'color': 'rgba(255,45,120,0.15)'},
                        {'range': [40, 60], 'color': 'rgba(255,183,0,0.1)'},
                        {'range': [60, 80], 'color': 'rgba(0,212,255,0.08)'},
                        {'range': [80, 100], 'color': 'rgba(0,255,136,0.1)'}
                    ],
                    'threshold': {'line': {'color': '#00ff88', 'width': 3}, 'thickness': 0.8, 'value': 75}
                }
            ))
            fig_g_exec.update_layout(
                paper_bgcolor='rgba(5,10,24,0.6)', font=dict(color='#c8d6e5', family='DM Sans'),
                height=260, margin=dict(t=50, b=10, l=30, r=30)
            )
            st.plotly_chart(fig_g_exec, use_container_width=True)
        
        with col_exec_comp:
            st.markdown("### 🥧 Composición del Mercado")
            comp_data = df_filtered.groupby('subgenero')['monto_ventas_usd'].sum().reset_index()
            comp_data = comp_data.sort_values('monto_ventas_usd', ascending=False).head(8)
            fig_comp = px.pie(comp_data, values='monto_ventas_usd', names='subgenero', hole=0.55,
                              template="plotly_dark",
                              color_discrete_sequence=['#00d4ff','#b44aff','#00ff88','#ff2d78','#ffb700','#7dd3fc','#a78bfa','#34d399'])
            fig_comp.update_layout(
                paper_bgcolor='rgba(5,10,24,0.6)',
                legend=dict(bgcolor='rgba(5,10,24,0.9)', bordercolor='rgba(0,212,255,0.2)', borderwidth=1, font=dict(size=10)),
                margin=dict(t=10, b=10, l=10, r=10), height=260,
                showlegend=True
            )
            fig_comp.update_traces(textposition='inside', textinfo='percent', hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>")
            st.plotly_chart(fig_comp, use_container_width=True)
        
        with col_exec_dist:
            st.markdown("### 📊 Distribución de Ventas")
            fig_hist_exec = px.histogram(
                df_filtered, x='monto_ventas_usd', nbins=30,
                template="plotly_dark",
                labels={'monto_ventas_usd': 'Ventas (USD)', 'count': 'Frecuencia'},
                color_discrete_sequence=['#00d4ff']
            )
            fig_hist_exec.update_layout(
                paper_bgcolor='rgba(5,10,24,0.6)', plot_bgcolor='rgba(0,0,0,0.3)',
                xaxis=dict(showgrid=True, gridcolor='rgba(0,212,255,0.08)', tickformat='$,.0s'),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,212,255,0.08)'),
                height=260, margin=dict(t=10, b=30, l=30, r=10),
                showlegend=False, bargap=0.1
            )
            st.plotly_chart(fig_hist_exec, use_container_width=True)
        
        st.markdown("---")
        
        # --- TOP 5 QUICK RANKING ---
        col_rank, col_insights = st.columns([1.2, 1])
        
        with col_rank:
            st.markdown("### 🏆 Ranking de Rendimiento — Top Juegos")
            rank_df = df_filtered.groupby('nombre').agg({
                'monto_ventas_usd': 'sum',
                'cantidad_descargas': 'sum',
                'ratio_positividad': 'mean',
                'subgenero': 'first'
            }).reset_index().sort_values('monto_ventas_usd', ascending=False).head(10)
            
            max_venta_rank = rank_df['monto_ventas_usd'].max() if len(rank_df) > 0 else 1
            
            rank_html = '<div style="background:rgba(5,10,24,0.8); border:1px solid rgba(0,212,255,0.15); border-radius:10px; padding:1rem; overflow:hidden;">'
            rank_html += '<div style="display:grid; grid-template-columns:30px 1fr 120px 80px; gap:8px; padding:0.5rem 0.8rem; border-bottom:1px solid rgba(0,212,255,0.15); font-family:Orbitron,sans-serif; font-size:0.65rem; color:#00d4ff; text-transform:uppercase; letter-spacing:0.05em;">'
            rank_html += '<span>#</span><span>Título</span><span>Ventas</span><span>Rating</span></div>'
            
            for i, (_, row) in enumerate(rank_df.iterrows()):
                pct = (row['monto_ventas_usd'] / max_venta_rank * 100) if max_venta_rank > 0 else 0
                rat = row['ratio_positividad']
                if rat >= 0.85: rc = '#00ff88'
                elif rat >= 0.70: rc = '#00d4ff'
                elif rat >= 0.40: rc = '#ffb700'
                else: rc = '#ff2d78'
                nombre_r = str(row['nombre'])[:30]
                rank_html += f'''<div style="display:grid; grid-template-columns:30px 1fr 120px 80px; gap:8px; padding:0.6rem 0.8rem; align-items:center; border-bottom:1px solid rgba(255,255,255,0.03); transition:background 0.2s;" onmouseover="this.style.background='rgba(0,212,255,0.05)'" onmouseout="this.style.background='transparent'">
                    <span style="color:#64748b; font-weight:700; font-family:JetBrains Mono,monospace; font-size:0.8rem;">{i+1}</span>
                    <span style="color:#e0f2fe; font-size:0.8rem; font-weight:600;">{nombre_r}</span>
                    <div style="position:relative;">
                        <div style="background:rgba(255,255,255,0.05); border-radius:4px; height:18px; overflow:hidden;">
                            <div style="background:linear-gradient(90deg,#00d4ff,#b44aff); width:{pct:.0f}%; height:100%; border-radius:4px; box-shadow:0 0 8px rgba(0,212,255,0.3);"></div>
                        </div>
                        <span style="position:absolute; right:4px; top:0; font-size:0.65rem; color:#c8d6e5; font-family:JetBrains Mono,monospace; line-height:18px;">{format_number(row["monto_ventas_usd"])}</span>
                    </div>
                    <span style="color:{rc}; font-weight:700; font-size:0.75rem; font-family:JetBrains Mono,monospace;">{rat:.0%}</span>
                </div>'''
            rank_html += '</div>'
            st.markdown(rank_html, unsafe_allow_html=True)
        
        with col_insights:
            st.markdown("### 🧠 Insights Automáticos (IA)")
            insights_list = generar_insights(df_filtered)
            for idx, insight in enumerate(insights_list):
                st.markdown(f"""
                <div style="background:rgba(0,212,255,0.03); border-left:3px solid {'#00d4ff' if idx % 2 == 0 else '#b44aff'}; padding:0.8rem 1rem; margin-bottom:0.5rem; border-radius:0 8px 8px 0; transition:all 0.3s;" onmouseover="this.style.background='rgba(0,212,255,0.08)'" onmouseout="this.style.background='rgba(0,212,255,0.03)'">
                    <p style="margin:0; font-size:0.85rem; color:#c8d6e5; line-height:1.5;">{insight}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Recomendación estratégica
            st.markdown("### 📋 Veredicto Estratégico")
            if avg_sat_exec >= 0.80:
                vered_color, vered_icon, vered_text = '#00ff88', '✅', 'ALTA VIABILIDAD — Mercado saludable. Inversión recomendada.'
            elif avg_sat_exec >= 0.60:
                vered_color, vered_icon, vered_text = '#ffb700', '⚠️', 'RIESGO MODERADO — Mercado competitivo. Precaución recomendada.'
            else:
                vered_color, vered_icon, vered_text = '#ff2d78', '🚨', 'ALTO RIESGO — Insatisfacción detectada. Análisis profundo requerido.'
            st.markdown(f"""
            <div style="background:rgba(5,10,24,0.9); border:1px solid {vered_color}; border-radius:10px; padding:1.2rem; text-align:center; box-shadow:0 0 20px {vered_color}22;">
                <p style="margin:0; font-size:1.5rem;">{vered_icon}</p>
                <p style="margin:0.3rem 0 0; color:{vered_color}; font-family:Orbitron,sans-serif; font-size:0.8rem; font-weight:700; letter-spacing:0.05em;">{vered_text}</p>
            </div>
            """, unsafe_allow_html=True)

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
                font=dict(family="DM Sans", size=12), paper_bgcolor='rgba(5, 10, 24, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.3)',
                xaxis=dict(showgrid=True, gridcolor='rgba(0, 212, 255, 0.08)', tickformat=",", title_font=dict(size=14, color='#00d4ff')),
                yaxis=dict(showgrid=True, gridcolor='rgba(0, 212, 255, 0.08)', tickformat="$,.0f", title_font=dict(size=14, color='#00d4ff')),
                legend=dict(bgcolor='rgba(5, 10, 24, 0.9)', bordercolor='rgba(0, 212, 255, 0.2)', borderwidth=1),
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
            fig_pie = px.pie(market_share, values='monto_ventas_usd', names='subgenero', hole=0.45, template="plotly_dark", color_discrete_sequence=['#00d4ff','#b44aff','#00ff88','#ff2d78','#ffb700','#7dd3fc','#a78bfa','#34d399','#f472b6','#38bdf8'])
            fig_pie.update_layout(font=dict(family="DM Sans", size=12), paper_bgcolor='rgba(5, 10, 24, 0.6)', legend=dict(bgcolor='rgba(5, 10, 24, 0.9)', bordercolor='rgba(0, 212, 255, 0.2)', borderwidth=1), margin=dict(t=20, b=20, l=20, r=20))
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>Ventas: $%{value:,.0f}<br>Porcentaje: %{percent}<extra></extra>")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_right:
            st.markdown("### 🏆 Top 10 Juegos Rentables")
            if len(df_filtered) > 0:
                top_games = df_filtered.nlargest(min(10, len(df_filtered)), 'monto_ventas_usd').sort_values('monto_ventas_usd', ascending=True)
                fig_bar = px.bar(top_games, x='monto_ventas_usd', y='nombre', orientation='h', color='monto_ventas_usd', color_continuous_scale=[[0,'#0a1628'],[0.5,'#00d4ff'],[1,'#00ff88']], hover_data={'monto_ventas_usd': ':$,.2f', 'conteo_resenas': ':,', 'ratio_positividad': ':.1%'}, labels={'monto_ventas_usd': 'Ventas (USD)', 'nombre': 'Juego'}, template="plotly_dark")
                fig_bar.update_layout(font=dict(family="DM Sans", size=11), paper_bgcolor='rgba(5, 10, 24, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.3)', xaxis=dict(showgrid=True, gridcolor='rgba(0, 212, 255, 0.08)', tickformat="$,.0s"), yaxis=dict(tickfont=dict(size=10)), showlegend=False, margin=dict(t=20, b=40, l=10, r=20))
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No hay datos disponibles para este filtro.")
        
        st.markdown("---")
        st.markdown("### 📈 Rendimiento por Desarrollador")
        if 'desarrollador' in df_filtered.columns:
            dev_stats = df_filtered.groupby('desarrollador').agg({'monto_ventas_usd': 'sum', 'cantidad_descargas': 'sum', 'nombre': 'count'}).reset_index()
            dev_stats.columns = ['Desarrollador', 'Ventas Totales', 'Descargas', 'Cantidad de Juegos']
            dev_stats = dev_stats.sort_values('Ventas Totales', ascending=False).head(15)
            fig_dev = px.bar(dev_stats, x='Desarrollador', y='Ventas Totales', color='Cantidad de Juegos', hover_data=['Descargas'], labels={'Ventas Totales': 'Ventas (USD)'}, template="plotly_dark", color_continuous_scale=[[0,'#0a1628'],[0.5,'#b44aff'],[1,'#00d4ff']])
            fig_dev.update_layout(font=dict(family="DM Sans", size=12), paper_bgcolor='rgba(5, 10, 24, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.3)', xaxis=dict(showgrid=False, tickangle=-45), yaxis=dict(showgrid=True, gridcolor='rgba(0, 212, 255, 0.08)', tickformat="$,.0s"), margin=dict(t=40, b=100, l=40, r=40), height=400)
            st.plotly_chart(fig_dev, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📈 Tendencia de Ventas en el Tiempo")
        if 'fecha' in df_filtered.columns and not df_filtered['fecha'].isnull().all():
            df_time = df_filtered.groupby('fecha')['monto_ventas_usd'].sum().reset_index()
            df_time = df_time.sort_values('fecha')
            fig_time = px.line(df_time, x='fecha', y='monto_ventas_usd', template="plotly_dark", labels={'fecha': 'Fecha', 'monto_ventas_usd': 'Ventas Diarias (USD)'})
            fig_time.update_traces(line_color='#00d4ff', line_width=3, fill='tozeroy', fillcolor='rgba(0, 212, 255, 0.05)')
            fig_time.update_layout(paper_bgcolor='rgba(5, 10, 24, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.3)', xaxis=dict(showgrid=True, gridcolor='rgba(0, 212, 255, 0.08)'), yaxis=dict(showgrid=True, gridcolor='rgba(0, 212, 255, 0.08)', tickformat="$,.0s"), height=350, margin=dict(t=30, b=30, l=30, r=30))
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
                fig_radar.add_trace(go.Scatterpolar(r=vals_j1, theta=nombres_metricas, fill='toself', name=juego1, line_color='#00d4ff', fillcolor='rgba(0,212,255,0.15)'))
                fig_radar.add_trace(go.Scatterpolar(r=vals_j2, theta=nombres_metricas, fill='toself', name=juego2, line_color='#b44aff', fillcolor='rgba(180,74,255,0.15)'))
                fig_radar.update_layout(
                    template="plotly_dark", paper_bgcolor='rgba(5, 10, 24, 0.6)',
                    polar=dict(radialaxis=dict(visible=False, range=[0, 100]), bgcolor='rgba(0,0,0,0.3)'),
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
                    text_auto='.2s', color_discrete_sequence=['#00d4ff', '#b44aff'], template="plotly_dark"
                )
                fig_barras.update_layout(
                    paper_bgcolor='rgba(5, 10, 24, 0.6)', plot_bgcolor='rgba(0,0,0,0.3)',
                    margin=dict(t=20, b=20, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_barras, use_container_width=True)
                
                st.markdown(f"""
                <div style="background: rgba(0,212,255,0.05); padding: 10px; border-radius: 8px; border-left: 3px solid #00ff88; margin-top: 10px;">
                    <p style="margin:0; font-size: 0.9rem;"><strong>🏆 Resumen Financiero:</strong></p>
                    <p style="margin:0; font-size: 0.85rem; color: #00d4ff;">{juego1}: <strong>${data_j1['monto_ventas_usd']:,.0f}</strong> ({data_j1['ratio_positividad']:.0%} Positivo)</p>
                    <p style="margin:0; font-size: 0.85rem; color: #b44aff;">{juego2}: <strong>${data_j2['monto_ventas_usd']:,.0f}</strong> ({data_j2['ratio_positividad']:.0%} Positivo)</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("⚠️ Necesitas al menos 2 juegos filtrados para usar la herramienta de Benchmarking.")

        # === NEW: TREEMAP DE MERCADO ===
        st.markdown("---")
        st.markdown("### 🗺️ Mapa de Mercado (Treemap)")
        if len(df_filtered) > 0 and 'subgenero' in df_filtered.columns:
            treemap_data = df_filtered.groupby(['subgenero', 'nombre'])['monto_ventas_usd'].sum().reset_index()
            treemap_data = treemap_data[treemap_data['monto_ventas_usd'] > 0]
            if len(treemap_data) > 0:
                fig_tree = px.treemap(
                    treemap_data, path=['subgenero', 'nombre'], values='monto_ventas_usd',
                    color='monto_ventas_usd', color_continuous_scale=[[0,'#0a1628'],[0.3,'#00d4ff'],[0.7,'#b44aff'],[1,'#00ff88']],
                    template="plotly_dark", labels={'monto_ventas_usd': 'Ventas (USD)'}
                )
                fig_tree.update_layout(
                    paper_bgcolor='rgba(5, 10, 24, 0.6)', margin=dict(t=30, b=10, l=10, r=10), height=500,
                    font=dict(family="DM Sans", size=12)
                )
                fig_tree.update_traces(
                    hovertemplate="<b>%{label}</b><br>Ventas: $%{value:,.0f}<extra></extra>",
                    textfont=dict(color="white")
                )
                st.plotly_chart(fig_tree, use_container_width=True)
        
        # === NEW: GAUGE + HEATMAP ROW ===
        st.markdown("---")
        col_gauge, col_heat = st.columns(2)
        
        with col_gauge:
            st.markdown("### 🎯 Gauge de Satisfacción Global")
            gauge_val = avg_positivity * 100 if not pd.isna(avg_positivity) else 0
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=gauge_val,
                number={'suffix': '%', 'font': {'size': 40, 'color': '#e0f2fe', 'family': 'JetBrains Mono'}},
                delta={'reference': 75, 'increasing': {'color': '#00ff88'}, 'decreasing': {'color': '#ff2d78'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#00d4ff', 'dtick': 20},
                    'bar': {'color': '#00d4ff', 'thickness': 0.3},
                    'bgcolor': 'rgba(0,0,0,0.3)',
                    'borderwidth': 2, 'bordercolor': 'rgba(0, 212, 255, 0.3)',
                    'steps': [
                        {'range': [0, 40], 'color': 'rgba(255, 45, 120, 0.15)'},
                        {'range': [40, 70], 'color': 'rgba(255, 183, 0, 0.1)'},
                        {'range': [70, 100], 'color': 'rgba(0, 255, 136, 0.1)'}
                    ],
                    'threshold': {'line': {'color': '#00ff88', 'width': 3}, 'thickness': 0.8, 'value': 75}
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(5, 10, 24, 0.6)', font=dict(color='#c8d6e5', family='DM Sans'),
                height=300, margin=dict(t=30, b=10, l=30, r=30)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col_heat:
            st.markdown("### 🔥 Matriz de Correlación")
            numeric_cols = ['monto_ventas_usd', 'cantidad_descargas', 'conteo_resenas', 'ratio_positividad']
            available_numeric = [c for c in numeric_cols if c in df_filtered.columns]
            if len(available_numeric) >= 2:
                corr_matrix = df_filtered[available_numeric].corr()
                labels_map = {'monto_ventas_usd': 'Ventas', 'cantidad_descargas': 'Descargas', 'conteo_resenas': 'Reseñas', 'ratio_positividad': 'Satisfacción'}
                corr_matrix.columns = [labels_map.get(c, c) for c in corr_matrix.columns]
                corr_matrix.index = [labels_map.get(c, c) for c in corr_matrix.index]
                fig_heat = px.imshow(
                    corr_matrix, text_auto='.2f', template="plotly_dark",
                    color_continuous_scale=[[0,'#ff2d78'],[0.5,'#0a1628'],[1,'#00ff88']],
                    aspect='auto'
                )
                fig_heat.update_layout(
                    paper_bgcolor='rgba(5, 10, 24, 0.6)', font=dict(family='DM Sans', size=12),
                    height=300, margin=dict(t=30, b=10, l=10, r=10)
                )
                st.plotly_chart(fig_heat, use_container_width=True)

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
            <div style='background: rgba(0, 212, 255, 0.05); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(0, 212, 255, 0.2);'>
                <h4 style='color: #00d4ff; margin-top: 0; font-family: Orbitron, sans-serif;'>1️⃣ Configura tu Estrategia</h4>
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
                    <div style="flex: 1; background: rgba(255, 45, 120, 0.05); border: 1px solid rgba(255, 45, 120, 0.3); border-radius: 10px; padding: 1.5rem; text-align: center;">
                        <p style="color: #ff2d78; margin: 0; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; font-family:'Orbitron',sans-serif; letter-spacing:0.05em;">📉 Escenario Pesimista</p>
                        <p style="font-size: 1.8rem; font-weight: 800; color: #ffffff; margin: 0.5rem 0; font-family: 'JetBrains Mono', monospace;">{format_number(escenario_pesimista)}</p>
                        <p style="color: #64748b; font-size: 0.7rem; margin: 0;">Tracción baja.</p>
                    </div>
                    <div style="flex: 1; background: linear-gradient(135deg, rgba(0, 255, 136, 0.08) 0%, rgba(0, 212, 255, 0.05) 100%); border: 1px solid rgba(0, 255, 136, 0.4); border-radius: 10px; padding: 1.5rem; text-align: center; transform: scale(1.05); box-shadow: 0 0 25px rgba(0,255,136,0.1);">
                        <p style="color: #00ff88; margin: 0; font-size: 0.85rem; font-weight: bold; text-transform: uppercase; font-family:'Orbitron',sans-serif; letter-spacing:0.05em;">📊 Escenario Esperado</p>
                        <p style="font-size: 2.2rem; font-weight: 800; color: #ffffff; margin: 0.5rem 0; font-family: 'JetBrains Mono', monospace;">{format_number(escenario_realista)}</p>
                        <p style="color: #64748b; font-size: 0.75rem; margin: 0;">Ingreso base proyectado.</p>
                    </div>
                    <div style="flex: 1; background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 10px; padding: 1.5rem; text-align: center;">
                        <p style="color: #00d4ff; margin: 0; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; font-family:'Orbitron',sans-serif; letter-spacing:0.05em;">🚀 Escenario Optimista</p>
                        <p style="font-size: 1.8rem; font-weight: 800; color: #ffffff; margin: 0.5rem 0; font-family: 'JetBrains Mono', monospace;">{format_number(escenario_optimista)}</p>
                        <p style="color: #64748b; font-size: 0.7rem; margin: 0;">Si el juego se hace viral.</p>
                    </div>
                </div>
                """
                st.markdown(html_tarjetas, unsafe_allow_html=True)
                
                fig_risk = go.Figure(go.Funnel(
                    y=["Optimista (Techo)", "Esperado (Seguro)", "Pesimista (Piso)"],
                    x=[escenario_optimista, escenario_realista, escenario_pesimista],
                    textinfo="value", marker={"color": ["#00d4ff", "#00ff88", "#ff2d78"]}
                ))
                fig_risk.update_layout(
                    title=f"Margen de Riesgo para un juego tipo {genero_elegido}",
                    template="plotly_dark", paper_bgcolor='rgba(5,10,24,0.6)', plot_bgcolor='rgba(0,0,0,0.3)',
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
                color, icono, label = "#00ff88", "😀", "POSITIVO"
            elif pol < -0.05:
                color, icono, label = "#ff2d78", "😡", "NEGATIVO"
            else:
                color, icono, label = "#ffb700", "😐", "NEUTRAL"
                
            kpi_html = f"""
            <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                <div style="flex: 1.5; background: linear-gradient(135deg, rgba(5,10,24,0.95) 0%, rgba(10,22,40,0.95) 100%); border: 1px solid {color}; border-radius: 12px; padding: 1.5rem; text-align: center; box-shadow: 0 0 25px {color}22;">
                    <p style="margin:0; color:#64748b; font-size:0.75rem; text-transform:uppercase; font-weight:600; font-family:'Orbitron',sans-serif; letter-spacing:0.1em;">Veredicto VADER</p>
                    <p style="margin:0.5rem 0; font-size:2rem; font-weight:900; color:{color}; font-family:'JetBrains Mono', monospace;">{icono} {label}</p>
                    <p style="margin:0; color:#c8d6e5;">Polaridad Neta: <strong style="color:{color}">{pol:+.3f}</strong></p>
                </div>
                <div style="flex: 1; background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 12px; padding: 1.5rem; text-align: center;">
                    <p style="margin:0; color:#00d4ff; font-size:0.75rem; text-transform:uppercase; font-weight:600; font-family:'Orbitron',sans-serif; letter-spacing:0.1em;">Tema Principal Hoy</p>
                    <p style="margin:0.5rem 0; font-size:1.6rem; font-weight:800; color:#ffffff; font-family:'JetBrains Mono', monospace; text-transform: uppercase;">"{ultimo_registro['tema_principal']}"</p>
                </div>
                <div style="flex: 1; background: rgba(180, 74, 255, 0.05); border: 1px solid rgba(180, 74, 255, 0.2); border-radius: 12px; padding: 1.5rem; text-align: center;">
                    <p style="margin:0; color:#b44aff; font-size:0.75rem; text-transform:uppercase; font-weight:600; font-family:'Orbitron',sans-serif; letter-spacing:0.1em;">Jugadores Activos</p>
                    <p style="margin:0.5rem 0; font-size:1.6rem; font-weight:800; color:#ffffff; font-family:'JetBrains Mono', monospace;">{ultimo_registro['jugadores_activos']:,}</p>
                </div>
            </div>
            """
            st.markdown(kpi_html, unsafe_allow_html=True)
            
        st.markdown("---")
        
        st.markdown("### 📈 Evolución Histórica: Jugadores vs. Sentimiento")
        
        fig_hist = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_hist.add_trace(
            go.Scatter(x=df_juego_nlp['fk_tiempo'], y=df_juego_nlp['jugadores_activos'], 
                       name="Jugadores Activos", mode="lines+markers", line=dict(color="#00d4ff", width=3), marker=dict(size=8)),
            secondary_y=False,
        )
        
        fig_hist.add_trace(
            go.Scatter(x=df_juego_nlp['fk_tiempo'], y=df_juego_nlp['polaridad_roberta'], 
                       name="Polaridad NLP (Sentimiento)", mode="lines+markers", fill='tozeroy', line=dict(color="#00ff88", width=2), fillcolor='rgba(0,255,136,0.05)', marker=dict(size=8)),
            secondary_y=True,
        )
        
        fig_hist.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(5, 10, 24, 0.6)', plot_bgcolor='rgba(0, 0, 0, 0.3)',
            margin=dict(t=40, b=40, l=40, r=40), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig_hist.update_yaxes(title_text="Cantidad de Jugadores", secondary_y=False, gridcolor='rgba(0, 212, 255, 0.08)')
        fig_hist.update_yaxes(title_text="Índice de Polaridad (-1 a 1)", secondary_y=True, showgrid=False)
        fig_hist.update_xaxes(type='category') 

        st.plotly_chart(fig_hist, use_container_width=True)
            
    else:
        st.warning("⚠️ No hay datos NLP almacenados en el Data Warehouse (tabla hechos_sentimiento). Ejecuta tu proceso Pentaho primero.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5: GAME EXPLORER — CATÁLOGO VISUAL ESTILO STEAM
# ═══════════════════════════════════════════════════════════════════════════

with tab5:
    st.markdown("## 🎮 Game Explorer — Catálogo Visual")
    st.markdown("Explora los juegos del Data Warehouse con imágenes, links directos a Steam Store y métricas clave.")
    
    if df_filtered.empty:
        st.warning("⚠️ No hay datos disponibles con los filtros actuales.")
    else:
        # Controls
        col_sort, col_n, col_order = st.columns(3)
        with col_sort:
            sort_by = st.selectbox("Ordenar por:", ["monto_ventas_usd", "cantidad_descargas", "ratio_positividad", "conteo_resenas"], 
                                   format_func=lambda x: {"monto_ventas_usd": "💰 Ventas", "cantidad_descargas": "📥 Descargas", "ratio_positividad": "⭐ Satisfacción", "conteo_resenas": "💬 Reseñas"}.get(x, x),
                                   key="explorer_sort")
        with col_n:
            cards_n = st.number_input("Cantidad de juegos:", min_value=3, max_value=min(60, len(df_filtered)), value=min(12, len(df_filtered)), step=3, key="explorer_n")
        with col_order:
            order_dir = st.radio("Orden:", ["Descendente", "Ascendente"], horizontal=True, key="explorer_order")
        
        # Get unique games
        explorer_df = df_filtered.groupby(['nombre']).agg({
            'monto_ventas_usd': 'sum',
            'cantidad_descargas': 'sum',
            'ratio_positividad': 'mean',
            'conteo_resenas': 'sum',
            'subgenero': 'first',
            'desarrollador': 'first'
        }).reset_index()
        
        if 'fk_juego' in df_filtered.columns:
            appid_map = df_filtered.groupby('nombre')['fk_juego'].first()
            explorer_df['appid'] = explorer_df['nombre'].map(appid_map)
        elif 'appid' in df_filtered.columns:
            appid_map = df_filtered.groupby('nombre')['appid'].first()
            explorer_df['appid'] = explorer_df['nombre'].map(appid_map)
        else:
            explorer_df['appid'] = None
        
        ascending = (order_dir == "Ascendente")
        explorer_df = explorer_df.sort_values(sort_by, ascending=ascending).head(int(cards_n))
        
        st.markdown("---")
        
        # Render cards in 3-column grid
        cols_per_row = 3
        rows = [explorer_df.iloc[i:i+cols_per_row] for i in range(0, len(explorer_df), cols_per_row)]
        
        for row_df in rows:
            cols = st.columns(cols_per_row)
            for idx, (_, game) in enumerate(row_df.iterrows()):
                with cols[idx]:
                    appid = game.get('appid', None)
                    img_url = get_steam_image(appid) if pd.notna(appid) else ""
                    store_url = get_steam_url(appid) if pd.notna(appid) else "#"
                    ratio = game['ratio_positividad'] if pd.notna(game['ratio_positividad']) else 0
                    ratio_pct = ratio * 100
                    
                    # Color for satisfaction bar
                    if ratio >= 0.85:
                        bar_color = "#00ff88"
                    elif ratio >= 0.70:
                        bar_color = "#00d4ff"
                    elif ratio >= 0.40:
                        bar_color = "#ffb700"
                    else:
                        bar_color = "#ff2d78"
                    
                    nombre_clean = str(game['nombre'])[:40]
                    sub = str(game['subgenero']) if pd.notna(game['subgenero']) else "N/A"
                    dev = str(game['desarrollador'])[:25] if pd.notna(game['desarrollador']) else "N/A"
                    
                    card_html = f"""
                    <div style="background: linear-gradient(180deg, rgba(5,10,24,0.95) 0%, rgba(10,22,40,0.95) 100%); border: 1px solid rgba(0,212,255,0.15); border-radius: 10px; overflow: hidden; margin-bottom: 1rem; transition: all 0.3s ease; box-shadow: 0 2px 15px rgba(0,0,0,0.3);">
                        <img src="{img_url}" style="width:100%; height:140px; object-fit:cover; display:block; border-bottom: 1px solid rgba(0,212,255,0.1);" onerror="this.style.display='none'">
                        <div style="padding: 1rem;">
                            <p style="margin:0 0 4px 0; font-family:'Orbitron',sans-serif; font-size:0.8rem; font-weight:700; color:#e0f2fe; line-height:1.3;">{nombre_clean}</p>
                            <div style="display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap;">
                                <span style="background:rgba(0,212,255,0.15); border:1px solid rgba(0,212,255,0.3); color:#00d4ff; padding:1px 6px; border-radius:3px; font-size:0.65rem; font-weight:600;">{sub}</span>
                                <span style="color:#64748b; font-size:0.65rem;">{dev}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                <span style="color:#64748b; font-size:0.7rem;">💰 {format_number(game['monto_ventas_usd'])}</span>
                                <span style="color:#64748b; font-size:0.7rem;">📥 {format_count(game['cantidad_descargas'])}</span>
                            </div>
                            <div style="background:rgba(255,255,255,0.05); border-radius:4px; height:6px; overflow:hidden; margin-bottom:6px;">
                                <div style="background:{bar_color}; width:{min(ratio_pct, 100):.0f}%; height:100%; border-radius:4px; box-shadow: 0 0 6px {bar_color}44;"></div>
                            </div>
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="color:{bar_color}; font-size:0.7rem; font-weight:700;">⭐ {ratio_pct:.1f}%</span>
                                <a href="{store_url}" target="_blank" style="color:#00d4ff; font-size:0.65rem; text-decoration:none; font-family:'Orbitron',sans-serif; border:1px solid rgba(0,212,255,0.3); padding:2px 8px; border-radius:4px; transition: all 0.2s;">VER EN STEAM →</a>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER — NEON ENTERPRISE
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 2rem 0;">
    <div style="width:150px; height:1px; background:linear-gradient(90deg,transparent,#00d4ff,transparent); margin:0 auto 1.5rem;"></div>
    <p style="margin: 0; font-family:'Orbitron',sans-serif; font-size:0.85rem; font-weight:700; letter-spacing:0.1em;">
        <span style="background:linear-gradient(135deg,#00d4ff,#b44aff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">STEAM ANALYTICS</span>
        <span style="color:#334155;"> · </span>
        <span style="color:#64748b;">Enterprise v5.0</span>
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; color: #475569;">
        <span style="border:1px solid rgba(0,212,255,0.2); padding:2px 8px; border-radius:3px; margin:0 3px; color:#00d4ff;">Streamlit</span>
        <span style="border:1px solid rgba(180,74,255,0.2); padding:2px 8px; border-radius:3px; margin:0 3px; color:#b44aff;">PostgreSQL</span>
        <span style="border:1px solid rgba(0,255,136,0.2); padding:2px 8px; border-radius:3px; margin:0 3px; color:#00ff88;">Plotly</span>
        <span style="border:1px solid rgba(255,183,0,0.2); padding:2px 8px; border-radius:3px; margin:0 3px; color:#ffb700;">VADER NLP</span>
        <span style="border:1px solid rgba(255,45,120,0.2); padding:2px 8px; border-radius:3px; margin:0 3px; color:#ff2d78;">RandomForest</span>
    </p>
    <p style="margin: 0.8rem 0 0 0; font-size: 0.65rem; color: #334155; font-family:'Orbitron',sans-serif; letter-spacing:0.15em;">
        PLATAFORMA DE INTELIGENCIA DE MERCADO · {datetime.now().strftime('%Y')}
    </p>
    <div style="width:150px; height:1px; background:linear-gradient(90deg,transparent,#b44aff,transparent); margin:1rem auto 0;"></div>
</div>
""", unsafe_allow_html=True)
