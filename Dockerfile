# Imagen de la API REST de la tienda online (Práctica 2) con FastAPI.
#
#   docker build -t tienda-api .
#   docker run --rm -p 8000:8000 tienda-api
#
# Después: http://localhost:8000/docs

# a) Imagen base ligera de Python
FROM python:3.12-slim

# Python sin ficheros .pyc, con la salida sin búfer (logs al instante) y pip sin caché
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    CARGAR_DATOS_EJEMPLO=true \
    CORS_ORIGINS=*

WORKDIR /app

# Usuario sin privilegios para ejecutar la aplicación (no usar root)
RUN groupadd --system app && useradd --system --gid app --no-create-home app

# b) Se copian primero las dependencias: si solo cambia el código, Docker
#    reutiliza la capa de pip install y la construcción es mucho más rápida
COPY requirements.txt .

# c) Instalación de las librerías con las versiones fijadas
RUN pip install --no-cache-dir -r requirements.txt

# d) Código fuente de la API
COPY src/Tienda_online/ .

# e) Permisos: el usuario "app" es dueño del código y puede leerlo y ejecutarlo
RUN chown -R app:app /app && chmod -R u=rwX,go=rX /app
USER app

EXPOSE 8000

# Docker comprueba cada 30 s que la API responde
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/', timeout=3)" || exit 1

# f) Comando de inicio: uvicorn escuchando en todas las interfaces del contenedor
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
