# 1. Traemos una mini-computadora que ya tiene Python 3.10 instalado
FROM python:3.10-slim

# 2. Creamos una carpeta dentro de esa computadora llamada /app
WORKDIR /app

# 3. Copiamos nuestra "lista de compras" a la carpeta /app
COPY requirements.txt .

# 4. Le decimos a la computadora que instale todo lo de la lista
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos TODO nuestro código (el script .py) adentro de la computadora
COPY . .

# 6. El botón de "ENCENDIDO": Qué comando debe ejecutarse al arrancar
CMD ["python", "steam_etl.py"]
