"""Punto de entrada de la API REST de la tienda online (FastAPI).

Este fichero es la *capa de exposición* del servicio: define los endpoints
HTTP y delega toda la lógica en ``TiendaService`` (Práctica 1).

Flujo de una petición:

    Cliente (navegador, /docs, requests, frontend)
        -> main.py      endpoint HTTP, códigos de respuesta
        -> schemas.py   validación de la entrada y formato de la salida
        -> Services/    lógica de negocio (TiendaService)
        -> models/      clases de dominio (Producto, Usuario, Pedido)

Ejecución (desde la carpeta src/Tienda_online):

    uvicorn main:app --reload                      # solo este equipo
    uvicorn main:app --reload --host 0.0.0.0       # accesible desde la red local

o con Docker (desde la raíz del repositorio, ver README):

    docker build -t tienda-api .
    docker run -p 8000:8000 tienda-api

Variables de entorno:

    CARGAR_DATOS_EJEMPLO  "true" (por defecto) carga usuarios, productos y pedidos
                          de ejemplo al arrancar; "false" arranca la tienda vacía.
    CORS_ORIGINS          orígenes permitidos para el frontend, separados por comas
                          (por defecto "*", cualquiera).
    HOST / PORT           solo al ejecutar "python main.py" (por defecto 127.0.0.1:8000).
"""

import os
from typing import Optional

from fastapi import Body, Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import Producto, ProductoElectronico, ProductoRopa
from schemas import (
    MensajeError,
    PedidoCreate,
    PedidoRead,
    ProductoCreate,
    ProductoRead,
    TipoProducto,
    UsuarioCreate,
    UsuarioRead,
)
from Services import (
    ConflictoError,
    NoEncontradoError,
    TiendaError,
    TiendaService,
)

# ----------------------------------------------------------------------
# Configuración por variables de entorno
# ----------------------------------------------------------------------
def leer_booleano(nombre: str, por_defecto: bool) -> bool:
    """Lee una variable de entorno de tipo sí/no ("true", "1", "si"...)."""
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in {"1", "true", "si", "sí", "yes", "on"}


CARGAR_DATOS_EJEMPLO = leer_booleano("CARGAR_DATOS_EJEMPLO", True)
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]


# ----------------------------------------------------------------------
# Aplicación
# ----------------------------------------------------------------------
app = FastAPI(
    title="API Tienda online",
    description=(
        "API REST de la tienda online de la Práctica 2 de Arquitectura del Software. "
        "Expone la lógica de `TiendaService` para gestionar usuarios, productos y pedidos."
    ),
    version="2.0.0",
    openapi_tags=[
        {"name": "Usuarios", "description": "Registro y consulta de clientes y administradores."},
        {"name": "Productos", "description": "Gestión del inventario."},
        {"name": "Pedidos", "description": "Creación de pedidos e historial de cada cliente."},
    ],
)

# CORS: permite que el frontend (otra página/origen) llame a la API desde
# el navegador. Sin esto el navegador bloquearía las peticiones.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------
# Servicio (una única instancia compartida por todas las peticiones)
# ----------------------------------------------------------------------
tienda = TiendaService()


def cargar_datos_ejemplo(servicio: TiendaService) -> None:
    """Rellena la tienda con usuarios, productos y pedidos de ejemplo.

    Como los datos están en memoria, se vuelven a cargar cada vez que
    arranca (o se reinicia) el servidor.
    """
    ana = servicio.registrar_usuario("cliente", "Ana López", "ana@mail.com", "Rúa do Príncipe 12, Vigo")
    luis = servicio.registrar_usuario("cliente", "Luis Pérez", "luis@mail.com", "Calle Mayor 5, Madrid")
    servicio.registrar_usuario("cliente", "Marta Gómez", "marta@mail.com", "Av. Diagonal 100, Barcelona")
    servicio.registrar_usuario("administrador", "Carlos Admin", "admin@tienda.com")

    portatil = servicio.anadir_producto(ProductoElectronico("Portátil Lenovo", 799.99, 10, 24))
    auriculares = servicio.anadir_producto(ProductoElectronico("Auriculares Sony", 129.50, 25, 12))
    camiseta = servicio.anadir_producto(ProductoRopa("Camiseta básica", 14.99, 50, "M", "Blanco"))
    vaqueros = servicio.anadir_producto(ProductoRopa("Pantalón vaquero", 39.95, 30, "42", "Azul"))
    libro = servicio.anadir_producto(Producto("Libro 'Clean Code'", 35.00, 15))

    servicio.realizar_pedido(ana.id, {portatil.id: 1, auriculares.id: 2})
    servicio.realizar_pedido(luis.id, {camiseta.id: 3, vaqueros.id: 1, libro.id: 1})


if CARGAR_DATOS_EJEMPLO:
    cargar_datos_ejemplo(tienda)


def get_tienda() -> TiendaService:
    """Dependencia de FastAPI que entrega el servicio a cada endpoint."""
    return tienda


# ----------------------------------------------------------------------
# Traducción de errores del servicio a códigos HTTP
# ----------------------------------------------------------------------
@app.exception_handler(TiendaError)
def manejar_error_tienda(request: Request, error: TiendaError) -> JSONResponse:
    """Convierte las excepciones de TiendaService en respuestas HTTP.

    * NoEncontradoError                     -> 404 Not Found
    * ConflictoError / StockInsuficiente    -> 409 Conflict
    * Resto de TiendaError                  -> 400 Bad Request
    """
    if isinstance(error, NoEncontradoError):
        codigo = status.HTTP_404_NOT_FOUND
    elif isinstance(error, ConflictoError):
        codigo = status.HTTP_409_CONFLICT
    else:
        codigo = status.HTTP_400_BAD_REQUEST
    return JSONResponse(status_code=codigo, content={"detail": str(error)})


# Respuestas de error que se documentan en /docs
ERROR_400 = {400: {"model": MensajeError, "description": "Petición no válida para la tienda"}}
ERROR_404 = {404: {"model": MensajeError, "description": "Recurso no encontrado"}}
ERROR_409 = {409: {"model": MensajeError, "description": "Conflicto con el estado actual"}}


# ----------------------------------------------------------------------
# Raíz
# ----------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def raiz() -> dict:
    """Comprobación rápida de que la API está en marcha."""
    return {"mensaje": "API de la tienda online en funcionamiento", "docs": "/docs"}


# ======================================================================
# Usuarios
# ======================================================================
@app.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Usuarios"],
    summary="Crear un usuario",
    responses={**ERROR_400, **ERROR_409},
)
def crear_usuario(
    datos: UsuarioCreate,
    servicio: TiendaService = Depends(get_tienda),
) -> UsuarioRead:
    """Registra un cliente o un administrador. Devuelve **409** si el email ya existe."""
    usuario = servicio.registrar_usuario(
        datos.tipo, datos.nombre, datos.email, datos.direccion
    )
    return UsuarioRead.desde_modelo(usuario)


@app.get(
    "/usuarios",
    response_model=list[UsuarioRead],
    tags=["Usuarios"],
    summary="Listar usuarios",
)
def listar_usuarios(servicio: TiendaService = Depends(get_tienda)) -> list[UsuarioRead]:
    """Devuelve todos los usuarios registrados."""
    return [UsuarioRead.desde_modelo(u) for u in servicio.listar_usuarios()]


@app.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioRead,
    tags=["Usuarios"],
    summary="Consultar un usuario",
    responses=ERROR_404,
)
def obtener_usuario(
    usuario_id: str,
    servicio: TiendaService = Depends(get_tienda),
) -> UsuarioRead:
    """Devuelve un usuario concreto. Devuelve **404** si no existe."""
    return UsuarioRead.desde_modelo(servicio.obtener_usuario(usuario_id))


# ======================================================================
# Productos
# ======================================================================
EJEMPLOS_PRODUCTO = {
    "electronico": {
        "summary": "Producto electrónico",
        "value": {"tipo": "electronico", "nombre": "Portátil Lenovo", "precio": 799.99,
                  "stock": 10, "meses_garantia": 24},
    },
    "ropa": {
        "summary": "Producto de ropa",
        "value": {"tipo": "ropa", "nombre": "Camiseta básica", "precio": 14.99,
                  "stock": 50, "talla": "M", "color": "Blanco"},
    },
    "generico": {
        "summary": "Producto genérico",
        "value": {"tipo": "generico", "nombre": "Libro 'Clean Code'", "precio": 35.0,
                  "stock": 15},
    },
}


@app.post(
    "/productos",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
    summary="Crear un producto",
)
def crear_producto(
    datos: ProductoCreate = Body(openapi_examples=EJEMPLOS_PRODUCTO),
    servicio: TiendaService = Depends(get_tienda),
) -> ProductoRead:
    """Añade un producto genérico, electrónico o de ropa al inventario.

    Los atributos extra dependen del tipo (`meses_garantia` para electrónicos,
    `talla` y `color` para ropa). Si no cuadran se devuelve **422**.
    """
    producto = servicio.anadir_producto(datos.a_modelo())
    return ProductoRead.desde_modelo(producto)


@app.get(
    "/productos",
    response_model=list[ProductoRead],
    tags=["Productos"],
    summary="Listar productos",
)
def listar_productos(
    tipo: Optional[TipoProducto] = None,
    servicio: TiendaService = Depends(get_tienda),
) -> list[ProductoRead]:
    """Devuelve el inventario. Admite filtrar por `tipo` (?tipo=ropa)."""
    productos = [ProductoRead.desde_modelo(p) for p in servicio.listar_productos()]
    if tipo is not None:
        productos = [p for p in productos if p.tipo == tipo]
    return productos


@app.get(
    "/productos/{producto_id}",
    response_model=ProductoRead,
    tags=["Productos"],
    summary="Consultar un producto",
    responses=ERROR_404,
)
def obtener_producto(
    producto_id: str,
    servicio: TiendaService = Depends(get_tienda),
) -> ProductoRead:
    """Devuelve un producto concreto. Devuelve **404** si no existe."""
    return ProductoRead.desde_modelo(servicio.obtener_producto(producto_id))


@app.delete(
    "/productos/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Productos"],
    summary="Eliminar un producto",
    responses=ERROR_404,
)
def eliminar_producto(
    producto_id: str,
    servicio: TiendaService = Depends(get_tienda),
) -> Response:
    """Elimina un producto del inventario. Responde **204** sin contenido."""
    servicio.eliminar_producto(producto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ======================================================================
# Pedidos
# ======================================================================
@app.post(
    "/pedidos",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Pedidos"],
    summary="Crear un pedido",
    responses={**ERROR_400, **ERROR_404, **ERROR_409},
)
def crear_pedido(
    datos: PedidoCreate,
    servicio: TiendaService = Depends(get_tienda),
) -> PedidoRead:
    """Crea un pedido y descuenta el stock.

    * **404** si el cliente o algún producto no existe.
    * **400** si el usuario es administrador.
    * **409** si no hay stock suficiente (en ese caso no se descuenta nada).
    """
    pedido = servicio.realizar_pedido(datos.cliente_id, datos.items_como_diccionario())
    return PedidoRead.desde_modelo(pedido)


@app.get(
    "/usuarios/{cliente_id}/pedidos",
    response_model=list[PedidoRead],
    tags=["Pedidos"],
    summary="Historial de pedidos de un cliente",
    responses=ERROR_404,
)
def listar_pedidos_cliente(
    cliente_id: str,
    servicio: TiendaService = Depends(get_tienda),
) -> list[PedidoRead]:
    """Devuelve los pedidos del cliente ordenados por fecha. **404** si no existe."""
    return [PedidoRead.desde_modelo(p) for p in servicio.listar_pedidos_usuario(cliente_id)]


# ----------------------------------------------------------------------
# Ejecución con el botón ▶ de VS Code (equivale a "uvicorn main:app --reload")
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    # Trabajar siempre desde la carpeta de este fichero, se lance desde donde se lance
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # HOST "127.0.0.1" -> solo este ordenador
    # HOST "0.0.0.0"   -> accesible desde otros equipos de la red
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
