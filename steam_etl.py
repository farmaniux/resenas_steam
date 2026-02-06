import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import random

# En GitHub usa la variable de entorno, en Colab puedes pegar tu URI directamente
DB_URI = os.getenv('DB_URI', "postgresql://postgres.asqucoulnhzpewoqpgyr:9619518453.papu@aws-0-us-west-2.pooler.supabase.com:6543/postgres")
juegos_ids = [440, 550, 730, 218230, 252490, 578080, 1085660, 1172470, 1240440, 1938090]

def asegurar_fecha_en_dimension(engine):
    """Inserta la fecha de hoy en dim_tiempo si no existe para evitar errores de FK"""
    hoy = datetime.now().date()
    query = text("""
        INSERT INTO dim_tiempo (id_tiempo, mes, trimestre, anio)
        VALUES (:d, :m, :t, :a)
        ON CONFLICT (id_tiempo) DO NOTHING
    """)
    with engine.connect() as conn:
        conn.execute(query, {
            "d": hoy, 
            "m": hoy.month, 
            "t": (hoy.month - 1) // 3 + 1, 
            "a": hoy.year
        })
        conn.commit()

def extraer_con_estimacion(appid):
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all"
    try:
        r = requests.get(url, timeout=10)
        stats = r.json()['query_summary']
        total_reviews = stats['total_reviews']
        
        # --- ALGORITMO DE ESTIMACIÓN PARA EL DASHBOARD ---
        ventas_estimadas = total_reviews * random.randint(30, 50)
        monto_usd = ventas_estimadas * 19.99
        descargas = int(ventas_estimadas * 1.15)
        
        return {
            'fk_juego': appid,
            'fk_tipo_resena': 1,
            'fk_tiempo': datetime.now().date(),
            'cantidad_descargas': descargas,
            'monto_ventas_usd': round(monto_usd, 2),
            'conteo_resenas': total_reviews
        }
    except Exception as e:
        print(f"Error en {appid}: {e}")
        return None

if __name__ == "__main__":
    engine = create_engine(DB_URI)
    
    print("Paso 1: Asegurando integridad de dimensiones...")
    asegurar_fecha_en_dimension(engine)
    
    print("Paso 2: Extrayendo datos de Steam...")
    datos = [extraer_con_estimacion(id) for id in juegos_ids]
    df = pd.DataFrame([d for d in datos if d is not None])
    
    if not df.empty:
        print("Paso 3: Cargando datos estimados a Supabase...")
        df.to_sql('hechos_resenas_steam', engine, if_exists='append', index=False)
        print("¡Éxito! Sistema alimentado correctamente.")
