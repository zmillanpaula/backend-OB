# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo requirements.txt al contenedor
COPY requirements.txt /app/requirements.txt

# Instala las dependencias de Python directamente
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
  
# Copia el código fuente del backend al contenedor
COPY . /app

# Exponer el puerto del backend Flask
EXPOSE 5002

# Comando para correr el backend Flask con gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--timeout", "120", "server:app"]