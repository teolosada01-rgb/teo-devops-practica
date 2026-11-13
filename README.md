# Tienda online: API REST con FastAPI y Docker

**Autor:** Teo Losada Gándara
**Asignatura:** Arquitectura del Software (UIE)

Aplicación Python de una tienda online. Gestiona usuarios (clientes y administradores), productos (genéricos, electrónicos y de ropa) y pedidos con control de stock. La lógica de negocio (`TiendaService`) se expone como una API REST con FastAPI, y se puede usar desde la documentación interactiva `/docs`, desde un cliente Python con `requests` o desde un frontend web.

Este repositorio recoge la evolución del proyecto en las prácticas de la asignatura:

- **Práctica 2:** API REST, cliente Python y frontend (código en `src/`).
- **Práctica 3.1:** control de versiones con Git y GitHub (ramas `main` y `feature/docker`).
- **Práctica 3.2:** contenerización con Docker y publicación de la imagen en un registry.

## Estructura

```text
.
├── Dockerfile               imagen de la API
├── .dockerignore            lo que no entra en la imagen
├── docker-compose.yml       API + frontend juntos (extra)
├── requirements.txt         dependencias con versiones fijadas
├── .github/workflows/
│   └── docker.yml           CI: build -> run -> test -> push
└── src/
    ├── Tienda_online/       API FastAPI (lo que va dentro de la imagen)
    │   ├── main.py          endpoints y configuración
    │   ├── schemas.py       esquemas Pydantic
    │   ├── models/          Producto, Usuario, Pedido
    │   └── Services/        TiendaService y sus excepciones
    ├── cliente/
    │   └── cliente_api.py   cliente Python con requests
    └── frontend/
        ├── index.html       frontend web
        ├── config.js        URL de la API por defecto
        ├── Dockerfile       imagen del frontend con nginx (extra)
        └── nginx.conf
```

## Docker

Hace falta [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows o macOS) o Docker Engine (Linux). Todos los comandos se ejecutan desde la raíz del repositorio.

### Construir la imagen

```bash
docker build -t tienda-api:1.0 .
```

La imagen parte de `python:3.12-slim`, instala las dependencias de `requirements.txt`, copia `src/Tienda_online` y ejecuta la API con un usuario sin privilegios (`app`).

### Ejecutar el contenedor

```bash
# En primer plano (Ctrl + C para parar)
docker run --rm -p 8000:8000 tienda-api:1.0

# En segundo plano, con nombre
docker run -d --name tienda -p 8000:8000 tienda-api:1.0
docker logs -f tienda      # ver los logs
docker stop tienda         # parar
docker rm tienda           # borrar el contenedor

# Arrancar con la tienda vacía (sin datos de ejemplo)
docker run --rm -p 8000:8000 -e CARGAR_DATOS_EJEMPLO=false tienda-api:1.0

# Usar otro puerto en el ordenador (fuera:dentro)
docker run --rm -p 9000:8000 tienda-api:1.0        # http://localhost:9000
```

### Variables de entorno

| Variable | Por defecto | Descripción |
| --- | --- | --- |
| `CARGAR_DATOS_EJEMPLO` | `true` | Carga 4 usuarios, 5 productos y 2 pedidos al arrancar. Con `false` la tienda arranca vacía. |
| `CORS_ORIGINS` | `*` | Orígenes desde los que un frontend puede llamar a la API, separados por comas (por ejemplo `http://localhost:8080`). |
| `PORT` | `8000` | Puerto en el que escucha uvicorn dentro del contenedor. |

La API no usa contraseñas ni claves, así que no hay secretos que configurar.

### Probar que funciona

Con el contenedor en marcha:

1. Abre http://localhost:8000/docs y debería aparecer la documentación de la API (Swagger).
2. Prueba los endpoints:

   ```bash
   curl http://localhost:8000/                 # {"mensaje":"API de la tienda online en funcionamiento","docs":"/docs"}
   curl http://localhost:8000/productos        # lista con 5 productos de ejemplo
   curl http://localhost:8000/usuarios         # lista con 4 usuarios de ejemplo
   curl http://localhost:8000/productos/xxx    # {"detail":"No existe ningún producto con id xxx."} (404)
   ```

3. Ejecuta el cliente Python contra el contenedor (en tu ordenador, con las dependencias instaladas):

   ```bash
   pip install -r requirements.txt
   python src/cliente/cliente_api.py http://localhost:8000
   ```

   Debe terminar con `Flujo completado correctamente.` y todas las comprobaciones de errores en `[OK]`.

4. `docker ps` debe mostrar el contenedor como `healthy` (la imagen incluye un `HEALTHCHECK`).

En la terminal del contenedor aparece una línea por cada petición, por ejemplo:

```text
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     172.17.0.1:53422 - "GET /productos HTTP/1.1" 200 OK
```

### Descargar la imagen publicada (pull)

Cada vez que se fusiona un cambio en `main`, GitHub Actions construye la imagen, la prueba y la publica en GitHub Container Registry:

```bash
docker pull ghcr.io/teolosada01-rgb/teo-devops-practica:latest
docker run --rm -p 8000:8000 ghcr.io/teolosada01-rgb/teo-devops-practica:latest
```

Además de `latest`, cada versión se etiqueta con el hash corto del commit (por ejemplo `:a1b2c3d`).

### API + frontend con docker compose (extra)

```bash
docker compose up --build
```

- API: http://localhost:8000/docs
- Frontend: http://localhost:8080

El frontend corre en un contenedor nginx que reenvía las peticiones de `/api/` al contenedor `api` usando el nombre del servicio dentro de la red de Docker (`http://api:8000`). Para pararlo todo: `docker compose down`.

## Integración continua

El workflow `.github/workflows/docker.yml` se ejecuta en cada push a `feature/**`, en cada Pull Request hacia `main` y en cada push a `main`:

1. **Build:** `docker build`.
2. **Run:** arranca el contenedor.
3. **Test:** comprueba los endpoints y los códigos de error, ejecuta el cliente Python contra el contenedor y verifica que no corre como root. También levanta el `docker compose` y prueba el frontend y el proxy.
4. **Push:** solo en `main`, publica la imagen en `ghcr.io`.

## Ejecutar sin Docker

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cd src/Tienda_online
uvicorn main:app --reload           # o: python main.py
```

El frontend se abre con `src/frontend/index.html`, y el cliente se lanza con `python src/cliente/cliente_api.py`.

## Flujo de trabajo con Git

- `main`: rama principal, siempre con código que funciona.
- `feature/<nombre>`: una rama por tarea. Se integra en `main` mediante Pull Request.
- Mensajes de commit con prefijo (`feat`, `fix`, `docs`, `build`, `ci`, `chore`).
