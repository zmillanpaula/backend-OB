# Usa una imagen base de Python
FROM python:3.9

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo requirements.txt desde scripts al contenedor
COPY requirements.txt /app/requirements.txt

# Instala python3-venv para crear entornos virtuales
RUN apt-get update && \
    apt-get install -y python3-venv && \
    apt-get clean

# Crea un entorno virtual en /opt/venv
RUN python3 -m venv /opt/venv

# Activa el entorno virtual y actualiza pip
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip

# Instala las dependencias dentro del entorno virtual
RUN /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Añade el entorno virtual al PATH
ENV PATH="/opt/venv/bin:$PATH"

# Configura el PYTHONPATH para incluir /app/scripts
ENV PYTHONPATH="/app/scripts:${PYTHONPATH}"

# Copia todo el código fuente al contenedor
COPY . /app

# Expone el puerto donde corre Flask
EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "server:app"]