# STM-15: Instancia PostgreSQL creada en Supabase con conexion segura
# Sprint 2 - Data Warehouse Supabase | TecNM Ingeniería Informática
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import pytz
import os
import random

# 1. Configuración de conexiones (Capa de Integración)
DB_URI_SUPABASE = os.getenv('DB_URI')

juegos_ids = [440, 550, 730, 218230, 252490, 578080, 1085660, 1172470, 1240440, 1938090]

# Fecha correcta en zona horaria de México (no UTC)
tz_mexico = pytz.timezone('America/Mexico_City')
hoy = datetime.now(tz_mexico).date()

def preparar_supabase(engine):
    """Maneja la limpieza y dimensiones en PostgreSQL (Idempotencia)"""
    try:
        with engine.connect() as conn:
            # Asegurar dimensión tiempo con la fecha correcta de México
            conn.execute(text("""
                INSERT INTO dim_tiempo (id_tiempo, mes, trimestre, anio)
                VALUES (:d, :m, :t, :a) ON CONFLICT (id_tiempo) DO NOTHING
            """), {"d": hoy, "m": hoy.month, "t": (hoy.month - 1) // 3 + 1, "a": hoy.year})

            # Limpieza preventiva para evitar duplicados en la carga diaria
            conn.execute(text("DELETE FROM hechos_resenas_steam WHERE fk_tiempo = :d"), {"d": hoy})
            conn.commit()
            print(f"   - Capa transaccional lista. Fecha México: {hoy}")
    except Exception as e:
        print(f"   - Error en preparar_supabase: {e}")
        raise

def extraer_datos(appid):
    """Fase de Extracción y Transformación básica (ETL)"""
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        stats = data['query_summary']
        total_reviews = stats['total_reviews']

        # Simulación de métricas de negocio (método Boxleiter)
        ventas = total_reviews * random.randint(30, 50)

        return {
            'fk_juego': appid,
            'fk_tipo_resena': 1,
            'fk_tiempo': hoy,  # ← fecha México correcta
            'votos_positivos': stats['total_positive'],
            'votos_negativos': stats['total_negative'],
            'cantidad_descargas': int(ventas * 1.15),
            'monto_ventas_usd': round(ventas * 19.99, 2),
            'conteo_resenas': total_reviews
        }
    except Exception as e:
        print(f"   - Error extrayendo appid {appid}: {e}")
        return None

if __name__ == "__main__":
    if not DB_URI_SUPABASE:
        print("❌ ERROR: Falta configurar la URI de Supabase en los Secrets.")
    else:
        uri_final = DB_URI_SUPABASE
        if uri_final.startswith("postgres://"):
            uri_final = uri_final.replace("postgres://", "postgresql+psycopg2://", 1)

        engine_sp = create_engine(
            uri_final,
            pool_pre_ping=True,
            connect_args={
                "options": "-c client_encoding=utf8",
                "sslmode": "require"
            }
        )

        try:
            print("🚀 Iniciando proceso ETL de Steam-BI...")
            print(f"   Fecha México: {hoy}")

            print("1. Preparando Capa Transaccional (Supabase)...")
            preparar_supabase(engine_sp)

            print("2. Extrayendo datos de la API de Steam...")
            datos = [extraer_datos(id) for id in juegos_ids]
            df = pd.DataFrame([d for d in datos if d is not None])

            if not df.empty:
                print(f"3. Cargando {len(df)} registros en Supabase (PostgreSQL)...")
                df.to_sql('hechos_resenas_steam', engine_sp, if_exists='append', index=False, method='multi')
                print("✅ ¡Éxito! Sincronización completada correctamente.")
            else:
                print("⚠️ No se obtuvieron datos válidos para cargar.")

        except Exception as e:
            print(f"❌ ERROR CRÍTICO: El proceso falló debido a: {e}")
