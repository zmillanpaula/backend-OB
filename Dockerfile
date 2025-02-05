# Usa una imagen base de Python optimizada
FROM python:3.9-slim

# Evita que Python cree archivos de caché `.pyc`
ENV PYTHONDONTWRITEBYTECODE 1
# Habilita el modo unbuffered para logs en contenedores
ENV PYTHONUNBUFFERED 1

# Establece el directorio de trabajo
WORKDIR /app

# Copia y actualiza dependencias de Python
COPY requirements.txt /app/requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    apt-get purge -y --auto-remove python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copia el código fuente del backend al contenedor
COPY . /app

# Expone el puerto del backend Flask
EXPOSE 5002

# Comando para correr el backend Flask con gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "3", "--timeout", "600", "server:app"]