# Usa una imagen base de Selenium compatible con ARM o x86
FROM seleniarm/standalone-chromium:latest

# Cambia temporalmente al usuario root para instalar paquetes y configurar permisos
USER root

# Cambia el directorio de trabajo
WORKDIR /app

# Otorga permisos al usuario `seluser` para que pueda escribir en /app
RUN chown -R seluser:seluser /app

# Instala dependencias de Python para el backend
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Cambia al usuario predeterminado de Selenium por seguridad
USER seluser

# Crea un entorno virtual en /app/venv
RUN python3 -m venv /app/venv

# Activa el entorno virtual y actualiza pip
RUN /app/venv/bin/pip install --no-cache-dir --upgrade pip

# Copia el archivo requirements.txt al contenedor
COPY requirements.txt /app/requirements.txt

# Instala las dependencias en el entorno virtual
RUN /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Añade el entorno virtual al PATH
ENV PATH="/app/venv/bin:$PATH"

# Configura el PYTHONPATH para incluir /app/scripts
ENV PYTHONPATH="/app/scripts"

# Copia todo el código fuente al contenedor
COPY . /app

# Exponer los puertos:
# - 4444: puerto interno de Selenium Grid
# - 5002: puerto del backend
EXPOSE 4444
EXPOSE 5002

# Comando para correr tanto Selenium como el backend Flask
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5002 server:app"]