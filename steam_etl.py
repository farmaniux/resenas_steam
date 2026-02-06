import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import os

# GitHub Actions leerá estas variables de forma segura
DB_URI = os.getenv('DB_URI') 

juegos = [440, 550, 730, 218230, 252490, 578080, 1085660, 1172470, 1240440, 1938090]

def extraer_datos(appid):
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        stats = data['query_summary']
        return {
            'fk_juego': appid,
            'fk_tipo_resena': 1,
            'fk_tiempo': datetime.now().date(),
            'cantidad_descargas': 0, 
            'monto_ventas_usd': 0.0,
            'conteo_resenas': stats['total_reviews']
        }
    except Exception as e:
        print(f"Error en {appid}: {e}")
        return None

if __name__ == "__main__":
    engine = create_engine(DB_URI)
    lista_datos = [extraer_datos(id) for id in juegos]
    df = pd.DataFrame([d for d in lista_datos if d is not None])
    
    if not df.empty:
        # Cargamos a la tabla de hechos
        df.to_sql('hechos_resenas_steam', engine, if_exists='append', index=False)
        print(f"ETL Exitoso: {datetime.now()}")