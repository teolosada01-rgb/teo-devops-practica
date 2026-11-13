# Imagen de la API REST de la tienda online (Práctica 2) con FastAPI.

# a) Imagen base ligera de Python
FROM python:3.12-slim

WORKDIR /app

# b) Dependencias
COPY requirements.txt .

# c) Instalación de las librerías
RUN pip install --no-cache-dir -r requirements.txt

# d) Código fuente de la API
COPY src/Tienda_online/ .

EXPOSE 8000

# f) Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
