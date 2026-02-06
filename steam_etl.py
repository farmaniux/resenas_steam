import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import random

# Configuración de conexión
DB_URI = os.getenv('DB_URI', "tu_uri_aqui")
juegos_ids = [440, 550, 730, 218230, 252490, 578080, 1085660, 1172470, 1240440, 1938090]

def preparar_base_de_datos(engine):
    """Asegura la fecha de hoy y limpia datos previos del mismo día para no acumular IDs"""
    hoy = datetime.now().date()
    with engine.connect() as conn:
        # 1. Asegurar dimensión tiempo
        conn.execute(text("""
            INSERT INTO dim_tiempo (id_tiempo, mes, trimestre, anio)
            VALUES (:d, :m, :t, :a) ON CONFLICT (id_tiempo) DO NOTHING
        """), {"d": hoy, "m": hoy.month, "t": (hoy.month - 1) // 3 + 1, "a": hoy.year})
        
        # 2. LIMPIEZA: Borrar registros previos de hoy para que el ID sea ordenado
        conn.execute(text("DELETE FROM hechos_resenas_steam WHERE fk_tiempo = :d"), {"d": hoy})
        conn.commit()

def extraer_con_estimacion(appid):
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all"
    try:
        r = requests.get(url, timeout=10)
        stats = r.json()['query_summary']
        total_reviews = stats['total_reviews']
        
        # Algoritmo de mercado (BI)
        ventas = total_reviews * random.randint(30, 50)
        
        return {
            'fk_juego': appid,
            'fk_tipo_resena': 1,
            'fk_tiempo': datetime.now().date(),
            'cantidad_descargas': int(ventas * 1.15),
            'monto_ventas_usd': round(ventas * 19.99, 2),
            'conteo_resenas': total_reviews
        }
    except: return None

if __name__ == "__main__":
    engine = create_engine(DB_URI)
    
    print("Limpiando registros de hoy para mantener orden...")
    preparar_base_de_datos(engine)
    
    print("Capturando nuevos datos de Steam...")
    datos = [extraer_con_estimacion(id) for id in juegos_ids]
    df = pd.DataFrame([d for d in datos if d is not None])
    
    if not df.empty:
        df.to_sql('hechos_resenas_steam', engine, if_exists='append', index=False)
        print("¡Éxito! Tabla actualizada con IDs limpios.")
