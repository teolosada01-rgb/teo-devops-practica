"""Esquemas Pydantic de la API REST de la tienda.

Los esquemas definen el *contrato* de la API:

* Los esquemas ``...Create`` describen lo que el cliente envía en el cuerpo
  de una petición. FastAPI los usa para validar la entrada automáticamente y,
  si algo no cuadra, responde con un 422 sin llegar a ejecutar el endpoint.
* Los esquemas ``...Read`` describen lo que la API devuelve. FastAPI los usa
  para serializar la respuesta a JSON y para documentarla en /docs.

Los esquemas son independientes de las clases de dominio (models/): las
clases de dominio contienen la lógica, los esquemas solo describen datos que
viajan por HTTP. Los métodos ``desde_modelo`` traducen de una cosa a la otra.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models import (
    Pedido,
    Producto,
    ProductoElectronico,
    ProductoRopa,
    Usuario,
)

PATRON_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

TipoUsuario = Literal["cliente", "administrador"]
TipoProducto = Literal["generico", "electronico", "ropa"]


class EsquemaBase(BaseModel):
    """Configuración común: elimina espacios sobrantes en los textos."""

    model_config = ConfigDict(str_strip_whitespace=True)


class MensajeError(BaseModel):
    """Formato de las respuestas de error de la API."""

    detail: str = Field(examples=["No existe ningún producto con id 1234."])


# ======================================================================
# 1.1 Usuarios
# ======================================================================
class UsuarioCreate(EsquemaBase):
    """Datos necesarios para registrar un usuario."""

    nombre: str = Field(min_length=1, max_length=100, examples=["Ana López"])
    email: str = Field(pattern=PATRON_EMAIL, examples=["ana@mail.com"])
    tipo: TipoUsuario = Field(examples=["cliente"])
    direccion: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Obligatoria para clientes. Se ignora en administradores.",
        examples=["Rúa do Príncipe 12, Vigo"],
    )

    @model_validator(mode="after")
    def comprobar_direccion(self) -> "UsuarioCreate":
        """Un cliente debe tener dirección postal."""
        if self.tipo == "cliente" and not self.direccion:
            raise ValueError("La dirección es obligatoria para los clientes.")
        return self


class UsuarioRead(BaseModel):
    """Información de un usuario que devuelve la API."""

    id: str
    nombre: str
    email: str
    es_admin: bool

    @classmethod
    def desde_modelo(cls, usuario: Usuario) -> "UsuarioRead":
        """Convierte un objeto Usuario (Cliente o Administrador) en esquema."""
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            es_admin=usuario.is_admin(),
        )


# ======================================================================
# 1.2 Productos
# ======================================================================
class ProductoCreate(EsquemaBase):
    """Datos para dar de alta un producto.

    Según el ``tipo`` se exigen unos atributos u otros:

    * ``generico``: solo nombre, precio y stock.
    * ``electronico``: además ``meses_garantia``.
    * ``ropa``: además ``talla`` y ``color``.
    """

    tipo: TipoProducto = Field(examples=["electronico"])
    nombre: str = Field(min_length=1, max_length=100, examples=["Portátil Lenovo"])
    precio: float = Field(ge=0, examples=[799.99])
    stock: int = Field(ge=0, examples=[10])
    meses_garantia: Optional[int] = Field(default=None, ge=0, examples=[24])
    talla: Optional[str] = Field(default=None, min_length=1, max_length=10)
    color: Optional[str] = Field(default=None, min_length=1, max_length=30)

    @model_validator(mode="after")
    def comprobar_atributos_del_tipo(self) -> "ProductoCreate":
        """Exige los atributos propios del tipo y rechaza los que no le corresponden."""
        es_electronico = self.tipo == "electronico"
        es_ropa = self.tipo == "ropa"

        if es_electronico and self.meses_garantia is None:
            raise ValueError("Un producto electrónico necesita 'meses_garantia'.")
        if es_ropa and (self.talla is None or self.color is None):
            raise ValueError("Un producto de ropa necesita 'talla' y 'color'.")

        if not es_electronico and self.meses_garantia is not None:
            raise ValueError("'meses_garantia' solo se usa en productos electrónicos.")
        if not es_ropa and (self.talla is not None or self.color is not None):
            raise ValueError("'talla' y 'color' solo se usan en productos de ropa.")
        return self

    def a_modelo(self) -> Producto:
        """Crea el objeto de dominio que corresponde al tipo indicado."""
        if self.tipo == "electronico":
            return ProductoElectronico(
                self.nombre, self.precio, self.stock, self.meses_garantia
            )
        if self.tipo == "ropa":
            return ProductoRopa(
                self.nombre, self.precio, self.stock, self.talla, self.color
            )
        return Producto(self.nombre, self.precio, self.stock)


class ProductoRead(BaseModel):
    """Información de un producto que devuelve la API."""

    id: str
    tipo: TipoProducto
    nombre: str
    precio: float
    stock: int
    meses_garantia: Optional[int] = None
    talla: Optional[str] = None
    color: Optional[str] = None

    @classmethod
    def desde_modelo(cls, producto: Producto) -> "ProductoRead":
        """Convierte un objeto Producto (o subclase) en esquema."""
        datos = {
            "id": producto.id,
            "nombre": producto.nombre,
            "precio": producto.precio,
            "stock": producto.stock,
        }
        if isinstance(producto, ProductoElectronico):
            return cls(tipo="electronico", meses_garantia=producto.meses_garantia, **datos)
        if isinstance(producto, ProductoRopa):
            return cls(tipo="ropa", talla=producto.talla, color=producto.color, **datos)
        return cls(tipo="generico", **datos)


# ======================================================================
# 1.3 Pedidos
# ======================================================================
class PedidoItemCreate(EsquemaBase):
    """Una línea del pedido: qué producto y cuántas unidades."""

    producto_id: str = Field(min_length=1)
    cantidad: int = Field(gt=0, examples=[1])


class PedidoCreate(EsquemaBase):
    """Datos para crear un pedido."""

    cliente_id: str = Field(min_length=1)
    items: list[PedidoItemCreate] = Field(min_length=1)

    def items_como_diccionario(self) -> dict[str, int]:
        """Agrupa las líneas en {producto_id: cantidad}, el formato que
        espera TiendaService. Si un producto aparece dos veces se suman
        sus cantidades."""
        agrupado: dict[str, int] = {}
        for item in self.items:
            agrupado[item.producto_id] = agrupado.get(item.producto_id, 0) + item.cantidad
        return agrupado


class PedidoItemRead(BaseModel):
    """Línea de un pedido tal y como la devuelve la API."""

    producto_id: str
    nombre: str
    precio_unitario: float
    cantidad: int
    subtotal: float


class PedidoRead(BaseModel):
    """Pedido completo que devuelve la API."""

    id: str
    fecha: datetime
    cliente: UsuarioRead
    items: list[PedidoItemRead]
    total: float

    @classmethod
    def desde_modelo(cls, pedido: Pedido) -> "PedidoRead":
        """Convierte un objeto Pedido en esquema."""
        items = [
            PedidoItemRead(
                producto_id=producto.id,
                nombre=producto.nombre,
                precio_unitario=producto.precio,
                cantidad=cantidad,
                subtotal=round(producto.precio * cantidad, 2),
            )
            for producto, cantidad in pedido.lineas
        ]
        return cls(
            id=pedido.id,
            fecha=pedido.fecha,
            cliente=UsuarioRead.desde_modelo(pedido.cliente),
            items=items,
            total=round(pedido.calcular_total(), 2),
        )
