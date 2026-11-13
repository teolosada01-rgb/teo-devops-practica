# Imagen del frontend (extra): nginx sirve index.html y reenvía /api/ al
# contenedor de la API. Se levanta junto a la API con docker compose.

FROM nginx:1.27-alpine

# Configuración de nginx: ficheros estáticos + proxy /api/ -> http://api:8000/
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Página del frontend
COPY index.html /usr/share/nginx/html/index.html

# Dentro de Docker el frontend habla con la API a través del proxy /api
RUN echo 'window.API_URL_POR_DEFECTO = window.location.origin + "/api";' \
        > /usr/share/nginx/html/config.js \
    && chmod 644 /usr/share/nginx/html/index.html /usr/share/nginx/html/config.js

EXPOSE 80
