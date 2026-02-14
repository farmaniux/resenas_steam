import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import random

# 1. Configuración de conexiones (Capa de Integración)
# Se recomienda usar la URI de IPv4 en los Secrets de GitHub para evitar errores de red
DB_URI_SUPABASE = os.getenv('DB_URI')

juegos_ids = [440, 550, 730, 218230, 252490, 578080, 1085660, 1172470, 1240440, 1938090]

def preparar_supabase(engine):
    """Maneja la limpieza y dimensiones en PostgreSQL (Idempotencia)"""
    hoy = datetime.now().date()
    try:
        with engine.connect() as conn:
            # Asegurar dimensión tiempo
            conn.execute(text("""
                INSERT INTO dim_tiempo (id_tiempo, mes, trimestre, anio)
                VALUES (:d, :m, :t, :a) ON CONFLICT (id_tiempo) DO NOTHING
            """), {"d": hoy, "m": hoy.month, "t": (hoy.month - 1) // 3 + 1, "a": hoy.year})
            
            # Limpieza preventiva para evitar duplicados en la carga diaria
            conn.execute(text("DELETE FROM hechos_resenas_steam WHERE fk_tiempo = :d"), {"d": hoy})
            conn.commit()
            print("   - Capa transaccional lista (Tiempo asegurado y limpieza completada).")
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
        
        # Simulación de métricas de negocio
        ventas = total_reviews * random.randint(30, 50)
        
        return {
            'fk_juego': appid,
            'fk_tipo_resena': 1,
            'fk_tiempo': datetime.now().date(),
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
        # Corrección de protocolo para SQLAlchemy
        uri_final = DB_URI_SUPABASE
        if uri_final.startswith("postgres://"):
            uri_final = uri_final.replace("postgres://", "postgresql+psycopg2://", 1)

        # Inicialización del motor con parámetros de estabilidad para Nube/Docker
        engine_sp = create_engine(
            uri_final,
            pool_pre_ping=True,  # Verifica si la conexión cayó antes de intentar usarla
            connect_args={
                "options": "-c client_encoding=utf8",
                "sslmode": "require"  # Forzar SSL para evitar bloqueos de red
            }
        )
        
        try:
            print("🚀 Iniciando proceso ETL de Steam-BI...")
            
            print("1. Preparando Capa Transaccional (Supabase)...")
            preparar_supabase(engine_sp)
            
            print("2. Extrayendo datos de la API de Steam...")
            datos = [extraer_datos(id) for id in juegos_ids]
            df = pd.DataFrame([d for d in datos if d is not None])
            
            if not df.empty:
                print(f"3. Cargando {len(df)} registros en Supabase (PostgreSQL)...")
                # method='multi' acelera la carga en bases de datos remotas
                df.to_sql('hechos_resenas_steam', engine_sp, if_exists='append', index=False, method='multi')
                print("✅ ¡Éxito! Sincronización completada correctamente.")
            else:
                print("⚠️ No se obtuvieron datos válidos para cargar.")
                
        except Exception as e:
            print(f"❌ ERROR CRÍTICO: El proceso falló debido a: {e}")
