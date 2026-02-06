import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import random

# Configuración de conexión
# En GitHub Actions leerá el secreto, en local puedes poner tu URL si pruebas
DB_URI = os.getenv('DB_URI')

# Tus 10 juegos
juegos_ids = [440, 550, 730, 218230, 252490, 578080, 1085660, 1172470, 1240440, 1938090]

def preparar_base_de_datos(engine):
    """Asegura la fecha de hoy y limpia datos previos del mismo día para no acumular IDs"""
    hoy = datetime.now().date()
    with engine.connect() as conn:
        # 1. Asegurar dimensión tiempo (Evita error de Foreign Key)
        conn.execute(text("""
            INSERT INTO dim_tiempo (id_tiempo, mes, trimestre, anio)
            VALUES (:d, :m, :t, :a) ON CONFLICT (id_tiempo) DO NOTHING
        """), {"d": hoy, "m": hoy.month, "t": (hoy.month - 1) // 3 + 1, "a": hoy.year})
        
        # 2. LIMPIEZA: Borrar registros previos de HOY para que no se dupliquen si corres el script varias veces
        conn.execute(text("DELETE FROM hechos_resenas_steam WHERE fk_tiempo = :d"), {"d": hoy})
        conn.commit()

def extraer_con_estimacion(appid):
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        stats = data['query_summary']
        
        # --- EXTRACCIÓN REAL DE METRICAS ---
        total_reviews = stats['total_reviews']
        positivos = stats['total_positive']  # Dato directo de Steam
        negativos = stats['total_negative']  # Dato directo de Steam
        
        # --- ESTIMACIÓN DE BI (MERCADO) ---
        # Estimamos ventas basándonos en el volumen total
        ventas = total_reviews * random.randint(30, 50)
        
        return {
            'fk_juego': appid,
            'fk_tipo_resena': 1,
            'fk_tiempo': datetime.now().date(),
            'votos_positivos': positivos,        # Columna Nueva
            'votos_negativos': negativos,        # Columna Nueva
            'cantidad_descargas': int(ventas * 1.15),
            'monto_ventas_usd': round(ventas * 19.99, 2),
            'conteo_resenas': total_reviews
        }
    except Exception as e:
        print(f"Error en juego {appid}: {e}")
        return None

if __name__ == "__main__":
    if not DB_URI:
        print("Error: No hay DB_URI configurada.")
    else:
        engine = create_engine(DB_URI)
        
        print("1. Preparando base de datos (Limpieza diaria)...")
        preparar_base_de_datos(engine)
        
        print("2. Extrayendo métricas de sentimiento y mercado...")
        datos = [extraer_con_estimacion(id) for id in juegos_ids]
        df = pd.DataFrame([d for d in datos if d is not None])
        
        if not df.empty:
            # El orden de columnas en el DataFrame se ajusta solo al SQL
            df.to_sql('hechos_resenas_steam', engine, if_exists='append', index=False)
            print(f"¡Éxito! {len(df)} registros cargados con votos Positivos y Negativos.")
        else:
            print("No se encontraron datos.")
