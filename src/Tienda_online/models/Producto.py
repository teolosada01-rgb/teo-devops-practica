"""Modelos de producto de la tienda online."""

import uuid


class Producto:
    """Clase base para todos los productos de la tienda."""

    def __init__(self, nombre: str, precio: float, stock: int) -> None:
        """Crea un producto con un identificador único generado automáticamente.

        Args:
            nombre: Nombre del producto.
            precio: Precio unitario en euros (no puede ser negativo).
            stock: Unidades disponibles (no puede ser negativo).
        """
        if precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        if stock < 0:
            raise ValueError("El stock no puede ser negativo.")

        self.id: str = str(uuid.uuid4())
        self.nombre: str = nombre
        self.precio: float = precio
        self.stock: int = stock

    def hay_stock(self, cantidad: int) -> bool:
        """Indica si hay stock suficiente para la cantidad solicitada."""
        return 0 < cantidad <= self.stock

    def actualizar_stock(self, cantidad: int) -> None:
        """Modifica el stock del producto.

        Args:
            cantidad: Unidades a sumar (reposición, valor positivo)
                o a restar (compra, valor negativo).

        Raises:
            ValueError: Si el stock resultante quedara por debajo de cero.
        """
        nuevo_stock = self.stock + cantidad
        if nuevo_stock < 0:
            raise ValueError(
                f"Stock insuficiente de '{self.nombre}': "
                f"hay {self.stock} y se piden {-cantidad}."
            )
        self.stock = nuevo_stock

    def __str__(self) -> str:
        """Devuelve las características principales del producto."""
        return (
            f"[{self.id[:8]}] {self.nombre} | "
            f"{self.precio:.2f} € | Stock: {self.stock}"
        )


class ProductoElectronico(Producto):
    """Producto electrónico con meses de garantía."""

    def __init__(
        self, nombre: str, precio: float, stock: int, meses_garantia: int
    ) -> None:
        """Crea un producto electrónico.

        Args:
            meses_garantia: Duración de la garantía en meses.
        """
        super().__init__(nombre, precio, stock)
        self.meses_garantia: int = meses_garantia

    def __str__(self) -> str:
        """Añade la garantía a la descripción del producto."""
        return f"{super().__str__()} | Garantía: {self.meses_garantia} meses"


class ProductoRopa(Producto):
    """Prenda de ropa con talla y color."""

    def __init__(
        self, nombre: str, precio: float, stock: int, talla: str, color: str
    ) -> None:
        """Crea un producto de ropa.

        Args:
            talla: Talla de la prenda (por ejemplo "M" o "42").
            color: Color de la prenda.
        """
        super().__init__(nombre, precio, stock)
        self.talla: str = talla
        self.color: str = color

    def __str__(self) -> str:
        """Añade la talla y el color a la descripción del producto."""
        return f"{super().__str__()} | Talla: {self.talla} | Color: {self.color}"
