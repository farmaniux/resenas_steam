#!/usr/bin/env python
# coding: utf-8
# =============================================================================
# STEAM-BI | Motor de Extracción + NLP Híbrido (VADER + TextBlob)
# Autor: Farid Rodriguez Puc
# Descripción: Extrae reseñas de Steam, aplica análisis de sentimiento híbrido
#              y genera CSV para Pentaho (local) o carga directo a Supabase (nube).
# =============================================================================

import requests
from lxml import html
import pandas as pd
import time
import datetime
import nltk
import os
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter
from textblob import TextBlob
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# 1. INICIALIZACIÓN DE MODELOS NLP
# ---------------------------------------------------------------------------

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
sia = SentimentIntensityAnalyzer()

def calcular_polaridad(texto):
    """
    Análisis de sentimiento híbrido VADER + TextBlob.
    - Zona ambigua (-0.15 a 0.15): promedia ambos modelos
    - Fuera de zona ambigua: usa VADER directo
    """
    score_vader = sia.polarity_scores(texto)['compound']
    if -0.15 < score_vader < 0.15:
        score_tb = TextBlob(texto).sentiment.polarity
        return (score_vader + score_tb) / 2
    return score_vader

# ---------------------------------------------------------------------------
# 2. CONFIGURACIÓN GENERAL
# ---------------------------------------------------------------------------

stopwords = set([
    'the', 'and', 'to', 'of', 'a', 'in', 'it', 'is', 'for', 'that', 'this',
    'game', 'play', 'playing', 'on', 'with', 'as', 'but', 'not', 'are', 'you',
    'i', 'my', 'they', 'be', 'have', 'was', 'will', 'can', 'like', 'just',
    'get', 'so', 'if', 'its', 'has', 'all', 'out', 'from', 'up', 'about',
    'more', 'your', 'when', 'one', 'would', 'even', 'really', 'only', 'do',
    'no', 'there', 'what', 'which', 'their', 'some', 'time', 'good', 'because',
    'much', 'very', 'now', 'we', 'me', 'than', 'or', 'by', 'an', 'at',
    'people', 'make', 'how', 'why', 'been', 'got', 'did', 'too', 'also',
    'well', 'way', 'could', 'should', 'them', 'who', 'had', 'then', 'after',
    'still', 'off', 'getting', 'being', 'every', 'someone', 'looking',
    'into', 'https', 'new', 'left'
])

appids = [440, 550, 730, 218230, 252490, 578080, 1085660, 1172470, 1240440, 1938090]
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
fecha_hoy = datetime.date.today()
resumen_diario = []

# ---------------------------------------------------------------------------
# 3. LOOP PRINCIPAL DE EXTRACCIÓN
# ---------------------------------------------------------------------------

print("=======================================================================")
print("🚀 INICIANDO MOTOR PREMIUM STEAM-BI (EXTRACCIÓN + VADER/TextBlob NLP)")
print("=======================================================================")

for appid in appids:
    print(f"\n🎮 [Iniciando Análisis] AppID: {appid}")
    print("   ├─ 📡 Consultando APIs oficiales de Steam...")

    en_oferta = 0
    hubo_actualizacion = 0
    jugadores_activos = 0

    # API 1: Jugadores activos
    try:
        url_players = (
            f"https://api.steampowered.com/ISteamUserStats/"
            f"GetNumberOfCurrentPlayers/v1/?appid={appid}"
        )
        jugadores_activos = (
            requests.get(url_players, headers=headers, timeout=10)
            .json()
            .get('response', {})
            .get('player_count', 0)
        )
        print(f"   │  └─ Jugadores activos detectados: {jugadores_activos:,}")
    except Exception as e:
        print(f"   │  └─ ⚠️  API Jugadores falló: {e}")

    # API 2: Oferta activa
    try:
        url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        res_store = requests.get(url_store, headers=headers, timeout=10).json()
        if (
            res_store
            and res_store[str(appid)]['success']
            and res_store[str(appid)]['data']
            .get('price_overview', {})
            .get('discount_percent', 0) > 0
        ):
            en_oferta = 1
            print("   │  └─ 💰 ¡Juego en oferta hoy!")
    except Exception as e:
        print(f"   │  └─ ⚠️  API Store falló: {e}")

    # API 3: Parche del día
    try:
        url_news = (
            f"https://api.steampowered.com/ISteamNews/"
            f"GetNewsForApp/v0002/?appid={appid}&count=5"
        )
        noticias = (
            requests.get(url_news, headers=headers, timeout=10)
            .json()
            .get('appnews', {})
            .get('newsitems', [])
        )
        for noticia in noticias:
            if (
                datetime.date.fromtimestamp(noticia['date']) == fecha_hoy
                and noticia.get('feedtype') == 1
            ):
                hubo_actualizacion = 1
                print("   │  └─ 🛠️  ¡Actualización/Parche detectado hoy!")
                break
    except Exception as e:
        print(f"   │  └─ ⚠️  API News falló: {e}")

    # Scraping + NLP
    print("   ├─ 🕷️  Iniciando minería de texto y evaluación de sentimientos...")

    resenas_validas = 0
    suma_polaridad = 0
    positivas_hoy = 0
    negativas_hoy = 0
    neutrales_hoy = 0
    todas_las_palabras = []

    for scroll in range(1, 11):
        url = (
            f"https://steamcommunity.com/app/{appid}/homecontent/"
            f"?userreviewsoffset={(scroll-1)*10}&p={scroll}"
            f"&workshopitemspage={scroll}&readytouse=12"
            f"&mt=all&filter=recent&validity=all"
        )
        try:
            response = requests.get(url, headers=headers, timeout=15)
            bloques = html.fromstring(response.content).xpath(
                '//div[contains(@class, "apphub_Card")]'
            )

            if not bloques:
                print(f"   │  └─ ⚠️  Sin bloques en scroll {scroll}")
                time.sleep(1)
                continue

            for bloque in bloques:
                texto = " ".join(
                    bloque.xpath('.//div[@class="apphub_CardTextContent"]/text()')
                ).strip()

                if len(texto) > 10:
                    polaridad = calcular_polaridad(texto)

                    if polaridad > 0.05:
                        positivas_hoy += 1
                    elif polaridad < -0.05:
                        negativas_hoy += 1
                    else:
                        neutrales_hoy += 1

                    suma_polaridad += polaridad
                    resenas_validas += 1

                    palabras_limpias = re.findall(r'\b[a-z]{3,}\b', texto.lower())
                    todas_las_palabras.extend(
                        [w for w in palabras_limpias if w not in stopwords]
                    )

        except Exception as e:
            print(f"   │  └─ ⚠️  Error en scroll {scroll}: {e}")

        print(f"   │  └─ Procesando bloque {scroll}/10...", end="\r")
        time.sleep(1)

    print(f"   │  └─ Procesamiento completado. {resenas_validas} reseñas evaluadas.    ")

    # Agregación
    if resenas_validas > 0:
        polaridad_promedio = suma_polaridad / resenas_validas

        if positivas_hoy > negativas_hoy and positivas_hoy > neutrales_hoy:
            sentimiento_pred = "POSITIVO"
        elif negativas_hoy > positivas_hoy and negativas_hoy > neutrales_hoy:
            sentimiento_pred = "NEGATIVO"
        else:
            sentimiento_pred = "MIXTO/NEUTRAL"

        top_3 = Counter(todas_las_palabras).most_common(3)
        tema_principal = ", ".join([p[0] for p in top_3]) if top_3 else "Ninguno"

        resumen_diario.append({
            'fk_juego': appid,
            'fecha_extraccion': fecha_hoy.strftime('%Y-%m-%d'),
            'total_resenas_analizadas': resenas_validas,
            'resenas_positivas_nlp': positivas_hoy,
            'resenas_negativas_nlp': negativas_hoy,
            'polaridad_roberta': round(polaridad_promedio, 4),  # nombre legacy, valor = VADER híbrido
            'sentimiento_predominante': sentimiento_pred,
            'en_oferta': en_oferta,
            'hubo_actualizacion': hubo_actualizacion,
            'jugadores_activos': jugadores_activos,
            'tema_principal': tema_principal
        })

        print(
            f"   └─ 🧠 RESULTADO: {sentimiento_pred} "
            f"(Pol: {polaridad_promedio:+.2f}) | "
            f"Temas Clave: '{tema_principal.upper()}'"
        )
    else:
        print(f"   └─ ⚠️  Sin reseñas válidas para AppID {appid} — se omite")

# ---------------------------------------------------------------------------
# 4. CARGA DE DATOS — LÓGICA DUAL LOCAL vs NUBE
# ---------------------------------------------------------------------------

print("\n=======================================================================")
print("💾 FASE ETL: GUARDANDO / CARGANDO DATOS")
print("=======================================================================")

df_final = pd.DataFrame(resumen_diario)
DB_URI = os.getenv('DB_URI')

if DB_URI:
    # -----------------------------------------------------------------------
    # MODO NUBE (GitHub Actions / Docker)
    # DB_URI existe como variable de entorno → carga directo a Supabase
    # -----------------------------------------------------------------------
    print("☁️  Modo Nube detectado — cargando directo a Supabase...")
    try:
        uri_final = DB_URI.replace("postgres://", "postgresql+psycopg2://", 1)
        engine = create_engine(
            uri_final,
            connect_args={
                "sslmode": "require",
                "options": "-c client_encoding=utf8"
            },
            pool_pre_ping=True,
            pool_recycle=3600
        )

        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM hechos_sentimiento WHERE fecha_extraccion = :d"),
                {"d": fecha_hoy}
            )
            conn.commit()
            print("   └─ 🧹 Limpieza del día completada (idempotencia)")

        df_final.to_sql(
            'hechos_sentimiento',
            engine,
            if_exists='append',
            index=False,
            method='multi'
        )
        print(f"   └─ ✅ {len(df_final)} registros cargados exitosamente a Supabase")
        print(f"   └─ Columnas: {list(df_final.columns)}")

    except Exception as e:
        print(f"   └─ ❌ Error al cargar a Supabase: {e}")
        raise

else:
    # -----------------------------------------------------------------------
    # MODO LOCAL (Windows + Pentaho)
    # DB_URI no existe → genera CSV para que Pentaho lo tome como siempre
    # -----------------------------------------------------------------------
    print("💻 Modo Local detectado — generando CSV para Pentaho...")
    try:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        directorio_actual = os.getcwd()

    ruta_csv = os.path.join(directorio_actual, 'resumen_sentimiento_diario.csv')
    df_final.to_csv(ruta_csv, index=False, encoding='utf-8')
    print(f"   └─ ✨ Archivo listo para Pentaho en: {ruta_csv}")
    print(f"   └─ Registros guardados: {len(df_final)}")
    print(f"   └─ Columnas: {list(df_final.columns)}")
