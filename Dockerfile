# Usa una imagen base de Selenium con Chrome
FROM selenium/standalone-chrome:latest

# Cambia el directorio de trabajo
WORKDIR /app

# Instala dependencias de Python para el backend
RUN apt-get update && apt-get install -y python3-pip python3-venv && apt-get clean

# Crea un entorno virtual en /opt/venv
RUN python3 -m venv /opt/venv

# Activa el entorno virtual y actualiza pip
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip

# Copia el archivo requirements.txt al contenedor
COPY requirements.txt /app/requirements.txt

# Instala las dependencias en el entorno virtual
RUN /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Añade el entorno virtual al PATH
ENV PATH="/opt/venv/bin:$PATH"

# Configura el PYTHONPATH para incluir /app/scripts
ENV PYTHONPATH="/app/scripts:${PYTHONPATH}"

# Copia todo el código fuente al contenedor
COPY . /app

# Exponer los puertos: 
# - 4444: puerto interno de Selenium Grid
# - 5002: puerto del backend
EXPOSE 4444
EXPOSE 5002

# Comando para correr tanto Selenium como el backend Flask
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5002 server:app"]