"""Cliente Python de la API de la tienda online (Práctica 2, parte 2).

Este script es totalmente independiente del servidor: NO importa
TiendaService, ni los modelos, ni nada de la carpeta Tienda_online.
Toda la comunicación se hace con peticiones HTTP usando ``requests``.

Uso:
    python cliente_api.py                              # usa BASE_URL
    python cliente_api.py http://192.168.1.34:8000     # otra dirección

Para probarlo contra el ordenador de un compañero basta con cambiar
BASE_URL por la IP de su equipo (o pasarla como argumento).
"""

import sys
import uuid
from typing import Any, Optional

import requests

# ----------------------------------------------------------------------
# Configuración: dirección base de la API
# ----------------------------------------------------------------------
BASE_URL = "http://localhost:8000"
TIMEOUT = 5  # segundos máximos de espera por petición


class ErrorAPI(Exception):
    """La API respondió con un código distinto del esperado."""

    def __init__(self, codigo: int, detalle: Any) -> None:
        super().__init__(f"HTTP {codigo}: {detalle}")
        self.codigo = codigo
        self.detalle = detalle


# ----------------------------------------------------------------------
# Función común para todas las peticiones
# ----------------------------------------------------------------------
def peticion(
    metodo: str,
    ruta: str,
    esperado: int = 200,
    datos: Optional[dict] = None,
) -> Any:
    """Hace una petición HTTP a la API y comprueba el código de estado.

    Args:
        metodo: "GET", "POST", "DELETE"...
        ruta: Ruta del endpoint, por ejemplo "/usuarios".
        esperado: Código HTTP que se espera si todo va bien.
        datos: Cuerpo JSON a enviar (para POST).

    Returns:
        La respuesta JSON ya convertida a dict/list (o None si no hay cuerpo).

    Raises:
        ErrorAPI: Si el código recibido no es el esperado.
    """
    url = f"{BASE_URL}{ruta}"
    respuesta = requests.request(metodo, url, json=datos, timeout=TIMEOUT)

    print(f"  {metodo} {ruta} -> {respuesta.status_code}")

    # Algunas respuestas (204) no tienen cuerpo
    cuerpo = respuesta.json() if respuesta.content else None

    if respuesta.status_code != esperado:
        raise ErrorAPI(respuesta.status_code, texto_error(cuerpo))
    return cuerpo


def texto_error(cuerpo: Any) -> str:
    """Extrae un mensaje legible del campo "detail" de una respuesta de error.

    Los errores de la tienda traen un texto ({"detail": "..."}), mientras que
    los errores de validación de FastAPI (422) traen una lista de errores.
    """
    detalle = cuerpo.get("detail") if isinstance(cuerpo, dict) else cuerpo
    if isinstance(detalle, list):
        return "; ".join(
            str(e.get("msg", e)).removeprefix("Value error, ") for e in detalle
        )
    return str(detalle)


# ----------------------------------------------------------------------
# Una función por endpoint
# ----------------------------------------------------------------------
def crear_usuario(nombre: str, email: str, tipo: str, direccion: Optional[str] = None) -> dict:
    datos = {"nombre": nombre, "email": email, "tipo": tipo, "direccion": direccion}
    return peticion("POST", "/usuarios", esperado=201, datos=datos)


def listar_usuarios() -> list[dict]:
    return peticion("GET", "/usuarios")


def obtener_usuario(usuario_id: str) -> dict:
    return peticion("GET", f"/usuarios/{usuario_id}")


def crear_producto(datos: dict) -> dict:
    return peticion("POST", "/productos", esperado=201, datos=datos)


def listar_productos() -> list[dict]:
    return peticion("GET", "/productos")


def crear_pedido(cliente_id: str, items: list[tuple[str, int]]) -> dict:
    datos = {
        "cliente_id": cliente_id,
        "items": [{"producto_id": pid, "cantidad": cant} for pid, cant in items],
    }
    return peticion("POST", "/pedidos", esperado=201, datos=datos)


def listar_pedidos_cliente(cliente_id: str) -> list[dict]:
    return peticion("GET", f"/usuarios/{cliente_id}/pedidos")


# ----------------------------------------------------------------------
# Utilidades para mostrar los resultados
# ----------------------------------------------------------------------
def titulo(texto: str) -> None:
    print("\n" + "=" * 70)
    print(texto)
    print("=" * 70)


def mostrar_usuarios(usuarios: list[dict]) -> None:
    for u in usuarios:
        rol = "Administrador" if u["es_admin"] else "Cliente"
        print(f"  - [{u['id'][:8]}] {u['nombre']} <{u['email']}> ({rol})")


def mostrar_productos(productos: list[dict]) -> None:
    for p in productos:
        extra = ""
        if p["tipo"] == "electronico":
            extra = f" | Garantía: {p['meses_garantia']} meses"
        elif p["tipo"] == "ropa":
            extra = f" | Talla: {p['talla']} | Color: {p['color']}"
        print(
            f"  - [{p['id'][:8]}] {p['nombre']} ({p['tipo']}) | "
            f"{p['precio']:.2f} € | Stock: {p['stock']}{extra}"
        )


def mostrar_pedido(pedido: dict) -> None:
    print(f"  Pedido [{pedido['id'][:8]}] - {pedido['fecha']} - Cliente: {pedido['cliente']['nombre']}")
    for item in pedido["items"]:
        print(
            f"    * {item['nombre']} x{item['cantidad']} "
            f"({item['precio_unitario']:.2f} €/ud) = {item['subtotal']:.2f} €"
        )
    print(f"    TOTAL: {pedido['total']:.2f} €")


# ----------------------------------------------------------------------
# Flujo de prueba
# ----------------------------------------------------------------------
def main() -> None:
    print(f"Conectando con la API en {BASE_URL}")

    # Sufijo aleatorio para que los emails no se repitan si se ejecuta varias veces
    sufijo = uuid.uuid4().hex[:6]

    # 1. Crear usuarios
    titulo("1. CREAR USUARIOS")
    ana = crear_usuario("Ana López", f"ana.{sufijo}@mail.com", "cliente", "Rúa do Príncipe 12, Vigo")
    print(f"  Creado cliente: {ana['nombre']} (id {ana['id']})")
    admin = crear_usuario("Carlos Admin", f"admin.{sufijo}@tienda.com", "administrador")
    print(f"  Creado administrador: {admin['nombre']} (id {admin['id']})")

    # 2. Consultar la lista de usuarios
    titulo("2. LISTA DE USUARIOS")
    mostrar_usuarios(listar_usuarios())

    # 3. Crear productos de los tres tipos
    titulo("3. CREAR PRODUCTOS")
    portatil = crear_producto({"tipo": "electronico", "nombre": "Portátil Lenovo",
                               "precio": 799.99, "stock": 10, "meses_garantia": 24})
    camiseta = crear_producto({"tipo": "ropa", "nombre": "Camiseta básica",
                               "precio": 14.99, "stock": 50, "talla": "M", "color": "Blanco"})
    libro = crear_producto({"tipo": "generico", "nombre": "Libro 'Clean Code'",
                            "precio": 35.0, "stock": 15})
    print("  Creados: " + ", ".join(p["nombre"] for p in (portatil, camiseta, libro)))

    # 4. Consultar la lista de productos
    titulo("4. LISTA DE PRODUCTOS")
    mostrar_productos(listar_productos())

    # 5. Crear un pedido para el cliente
    titulo("5. CREAR PEDIDO")
    pedido = crear_pedido(ana["id"], [(portatil["id"], 1), (camiseta["id"], 3), (libro["id"], 2)])
    mostrar_pedido(pedido)

    # 6. Consultar los pedidos del cliente
    titulo(f"6. PEDIDOS DE {ana['nombre'].upper()}")
    for p in listar_pedidos_cliente(ana["id"]):
        mostrar_pedido(p)

    print("\n  Stock tras el pedido:")
    mostrar_productos(listar_productos())

    # 7. Comprobación de que los errores llegan con el código HTTP correcto
    titulo("7. COMPROBACIÓN DE ERRORES")
    pruebas = [
        ("Pedido con más unidades que el stock (409)", 409,
         lambda: crear_pedido(ana["id"], [(portatil["id"], 1000)])),
        ("Pedido hecho por un administrador (400)", 400,
         lambda: crear_pedido(admin["id"], [(libro["id"], 1)])),
        ("Usuario que no existe (404)", 404,
         lambda: obtener_usuario("id-inexistente")),
        ("Email repetido (409)", 409,
         lambda: crear_usuario("Ana bis", ana["email"], "cliente", "Vigo")),
        ("Producto de ropa sin talla ni color (422)", 422,
         lambda: crear_producto({"tipo": "ropa", "nombre": "Pantalón", "precio": 20, "stock": 5})),
    ]
    for descripcion, codigo_esperado, prueba in pruebas:
        try:
            prueba()
            print(f"  [FALLO] {descripcion}: la API no devolvió error")
        except ErrorAPI as error:
            estado = "OK" if error.codigo == codigo_esperado else "FALLO"
            print(f"  [{estado}] {descripcion}: {error}")

    print("\nFlujo completado correctamente.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1].rstrip("/")
    try:
        main()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print(
            f"\nNo se pudo conectar con {BASE_URL}.\n"
            "Comprueba que el servidor está arrancado, que la IP y el puerto son "
            "correctos y que el cortafuegos permite la conexión."
        )
        sys.exit(1)
    except ErrorAPI as error:
        print(f"\nLa API devolvió un error inesperado: {error}")
        sys.exit(1)
