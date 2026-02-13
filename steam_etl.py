import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import random

# 1. Configuración de conexiones (Capa de Integración)
# Solo mantenemos activa la URI de Supabase para estabilizar el proceso
DB_URI_SUPABASE = os.getenv('DB_URI')
# DB_URI_SINGLESTORE = os.getenv('DB_URI_BACKUP') # Comentado temporalmente

juegos_ids = [440, 550, 730, 218230, 252490, 578080, 1085660, 1172470, 1240440, 1938090]

def preparar_supabase(engine):
    """Maneja la limpieza y dimensiones en PostgreSQL (Idempotencia)"""
    hoy = datetime.now().date()
    with engine.connect() as conn:
        # Asegurar dimensión tiempo
        conn.execute(text("""
            INSERT INTO dim_tiempo (id_tiempo, mes, trimestre, anio)
            VALUES (:d, :m, :t, :a) ON CONFLICT (id_tiempo) DO NOTHING
        """), {"d": hoy, "m": hoy.month, "t": (hoy.month - 1) // 3 + 1, "a": hoy.year})
        
        # Limpieza preventiva para evitar duplicados en la carga diaria
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
    # Validamos solo la conexión a Supabase para evitar cierres inesperados
    if not DB_URI_SUPABASE:
        print("Falta configurar la URI de Supabase en los Secrets.")
    else:
        # Inicialización del motor de Supabase
        engine_sp = create_engine(DB_URI_SUPABASE)
        
        # --- SINGLESTORE COMENTADO PARA EVITAR ERROR SSL 1251 ---
        # engine_ss = create_engine(
        #     DB_URI_SINGLESTORE, 
        #     connect_args={"ssl": {"fake_flag": True}} 
        # )

        print("1. Preparando Capa Transaccional (Supabase)...")
        preparar_supabase(engine_sp)

        print("2. Iniciando proceso ETL de Steam...")
        datos = [extraer_datos(id) for id in juegos_ids]
        df = pd.DataFrame([d for d in datos if d is not None])

        if not df.empty:
            print("3. Cargando en Supabase (PostgreSQL)...")
            # Carga exitosa verificada en ejecuciones previas
            df.to_sql('hechos_resenas_steam', engine_sp, if_exists='append', index=False)
            
            # --- CARGA A SINGLESTORE COMENTADA ---
            # print("4. Cargando en SingleStore (Data Warehouse)...")
            # df.to_sql('hechos_resenas_steam', engine_ss, if_exists='append', index=False)
            
            print(f"¡Éxito! {len(df)} registros sincronizados en Supabase.")
        else:
            print("No se obtuvieron datos de la API.")
