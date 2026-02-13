import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import random

# 1. Configuración de conexiones (Capa de Integración)
DB_URI_SUPABASE = os.getenv('DB_URI')
DB_URI_SINGLESTORE = os.getenv('DB_URI_BACKUP')

juegos_ids = [440, 550, 730, 218230, 252490, 578080, 1085660, 1172470, 1240440, 1938090]

def preparar_supabase(engine):
    """Maneja la limpieza y dimensiones en PostgreSQL (Idempotencia)"""
    hoy = datetime.now().date()
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO dim_tiempo (id_tiempo, mes, trimestre, anio)
            VALUES (:d, :m, :t, :a) ON CONFLICT (id_tiempo) DO NOTHING
        """), {"d": hoy, "m": hoy.month, "t": (hoy.month - 1) // 3 + 1, "a": hoy.year})
        
        conn.execute(text("DELETE FROM hechos_resenas_steam WHERE fk_tiempo = :d"), {"d": hoy})
        conn.commit()

def extraer_datos(appid):
    """Fase de Extracción y Transformación básica (ETL)"""
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        stats = data['query_summary']
        total_reviews = stats['total_reviews']
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
        print(f"Error extrayendo appid {appid}: {e}")
        return None

if __name__ == "__main__":
    if not DB_URI_SUPABASE or not DB_URI_SINGLESTORE:
        print("Faltan configurar las URIs de las bases de datos en los Secrets.")
    else:
        # Inicialización de motores
        engine_sp = create_engine(DB_URI_SUPABASE)
        
        # --- AJUSTE PARA SINGLESTORE CON SSL (ETAPA 5: IMPLEMENTACIÓN) ---
        engine_ss = create_engine(
    DB_URI_SINGLESTORE, 
    connect_args={"ssl": {"fake_flag": True}} 
)

        print("1. Preparando Capa Transaccional (Supabase)...")
        preparar_supabase(engine_sp)

        print("2. Iniciando proceso ETL de Steam...")
        datos = [extraer_datos(id) for id in juegos_ids]
        df = pd.DataFrame([d for d in datos if d is not None])

        if not df.empty:
            print("3. Cargando en Supabase (PostgreSQL)...")
            df.to_sql('hechos_resenas_steam', engine_sp, if_exists='append', index=False)
            
            print("4. Cargando en SingleStore (Data Warehouse)...")
            # Con el motor configurado con SSL, esto ya no debería dar error 1251
            df.to_sql('hechos_resenas_steam', engine_ss, if_exists='append', index=False)
            
            print(f"¡Éxito! {len(df)} registros sincronizados en ambas bases de datos.")
        else:
            print("No se obtuvieron datos de la API.")

