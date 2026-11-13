"""Capa de servicios que gestiona las operaciones de la tienda."""

from typing import Optional

from models import Administrador, Cliente, Pedido, Producto, Usuario

from .excepciones import (
    ConflictoError,
    NoEncontradoError,
    OperacionNoPermitidaError,
    StockInsuficienteError,
    TiendaError,
)


class TiendaService:
    """Intermediario entre usuarios, productos y pedidos de la tienda.

    Los datos se guardan en memoria: al reiniciar el servidor se pierden.
    """

    def __init__(self) -> None:
        """Inicializa la tienda vacía."""
        self.usuarios: dict[str, Usuario] = {}
        self.productos: dict[str, Producto] = {}
        self.pedidos: list[Pedido] = []

    # ------------------------------------------------------------------
    # Usuarios
    # ------------------------------------------------------------------
    def registrar_usuario(
        self,
        tipo: str,
        nombre: str,
        email: str,
        direccion: Optional[str] = None,
    ) -> Usuario:
        """Registra un nuevo usuario de tipo cliente o administrador.

        Args:
            tipo: "cliente" o "administrador".
            nombre: Nombre del usuario.
            email: Correo electrónico (debe ser único en la tienda).
            direccion: Dirección postal, obligatoria para clientes.

        Returns:
            El usuario creado.

        Raises:
            ConflictoError: Si el email ya está registrado.
            TiendaError: Si el tipo no es válido o falta la dirección de un cliente.
        """
        if any(u.email.lower() == email.lower() for u in self.usuarios.values()):
            raise ConflictoError(f"Ya existe un usuario con el email {email}.")

        tipo = tipo.strip().lower()
        if tipo == "cliente":
            if not direccion:
                raise TiendaError("Un cliente necesita una dirección postal.")
            usuario: Usuario = Cliente(nombre, email, direccion)
        elif tipo == "administrador":
            usuario = Administrador(nombre, email)
        else:
            raise TiendaError(
                f"Tipo de usuario no válido: '{tipo}'. "
                "Usa 'cliente' o 'administrador'."
            )

        self.usuarios[usuario.id] = usuario
        return usuario

    def obtener_usuario(self, usuario_id: str) -> Usuario:
        """Devuelve un usuario a partir de su id.

        Raises:
            NoEncontradoError: Si el usuario no existe.
        """
        if usuario_id not in self.usuarios:
            raise NoEncontradoError(f"No existe ningún usuario con id {usuario_id}.")
        return self.usuarios[usuario_id]

    def listar_usuarios(self) -> list[Usuario]:
        """Devuelve todos los usuarios registrados."""
        return list(self.usuarios.values())

    # ------------------------------------------------------------------
    # Productos
    # ------------------------------------------------------------------
    def anadir_producto(self, producto: Producto) -> Producto:
        """Añade al inventario un producto de cualquier categoría.

        Returns:
            El producto añadido.
        """
        self.productos[producto.id] = producto
        return producto

    def obtener_producto(self, producto_id: str) -> Producto:
        """Devuelve un producto a partir de su id.

        Raises:
            NoEncontradoError: Si el producto no existe.
        """
        if producto_id not in self.productos:
            raise NoEncontradoError(f"No existe ningún producto con id {producto_id}.")
        return self.productos[producto_id]

    def eliminar_producto(self, producto_id: str) -> Producto:
        """Elimina un producto del inventario a partir de su id.

        Los pedidos ya realizados conservan la referencia al producto, por lo
        que el histórico sigue mostrándose correctamente.

        Returns:
            El producto eliminado.

        Raises:
            NoEncontradoError: Si el producto no existe.
        """
        producto = self.obtener_producto(producto_id)
        del self.productos[producto_id]
        return producto

    def listar_productos(self) -> list[Producto]:
        """Devuelve todos los productos del inventario."""
        return list(self.productos.values())

    # ------------------------------------------------------------------
    # Pedidos
    # ------------------------------------------------------------------
    def realizar_pedido(self, usuario_id: str, items: dict[str, int]) -> Pedido:
        """Crea un pedido si el usuario existe y hay stock de todo lo pedido.

        Primero se valida el pedido completo y solo después se descuenta
        el stock, para no dejar el inventario a medias si algo falla.

        Args:
            usuario_id: Id del cliente que hace el pedido.
            items: Diccionario {id_producto: cantidad}.

        Returns:
            El pedido creado.

        Raises:
            NoEncontradoError: Si el usuario o algún producto no existe.
            OperacionNoPermitidaError: Si el usuario no es cliente.
            TiendaError: Si el pedido está vacío o alguna cantidad no es válida.
            StockInsuficienteError: Si no hay stock suficiente de algún producto.
        """
        usuario = self.obtener_usuario(usuario_id)
        if not isinstance(usuario, Cliente):
            raise OperacionNoPermitidaError(
                f"{usuario.nombre} no es cliente y no puede hacer pedidos."
            )
        if not items:
            raise TiendaError("El pedido no contiene productos.")

        # 1. Validación completa
        lineas: list[tuple[Producto, int]] = []
        for producto_id, cantidad in items.items():
            producto = self.obtener_producto(producto_id)
            if cantidad <= 0:
                raise TiendaError(
                    f"Cantidad no válida para '{producto.nombre}': {cantidad}."
                )
            if not producto.hay_stock(cantidad):
                raise StockInsuficienteError(
                    f"Stock insuficiente de '{producto.nombre}': "
                    f"hay {producto.stock} y se piden {cantidad}."
                )
            lineas.append((producto, cantidad))

        # 2. Descuento de stock y creación del pedido
        for producto, cantidad in lineas:
            producto.actualizar_stock(-cantidad)

        pedido = Pedido(usuario, lineas)
        self.pedidos.append(pedido)
        return pedido

    def listar_pedidos_usuario(self, usuario_id: str) -> list[Pedido]:
        """Devuelve los pedidos de un usuario ordenados por fecha (más antiguo primero).

        Raises:
            NoEncontradoError: Si el usuario no existe.
        """
        self.obtener_usuario(usuario_id)
        pedidos = [p for p in self.pedidos if p.cliente.id == usuario_id]
        return sorted(pedidos, key=lambda p: p.fecha)
