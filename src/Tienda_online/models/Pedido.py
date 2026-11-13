"""Modelo de pedido de la tienda online."""

import uuid
from datetime import datetime
from typing import Optional

from .Producto import Producto
from .Usuario import Cliente


class Pedido:
    """Pedido realizado por un cliente con una lista de productos y cantidades."""

    def __init__(
        self,
        cliente: Cliente,
        lineas: list[tuple[Producto, int]],
        fecha: Optional[datetime] = None,
    ) -> None:
        """Crea un pedido.

        Args:
            cliente: Cliente que realiza el pedido.
            lineas: Lista de tuplas (producto, cantidad).
            fecha: Fecha del pedido. Si no se indica, se usa la actual.
        """
        self.id: str = str(uuid.uuid4())
        self.cliente: Cliente = cliente
        self.lineas: list[tuple[Producto, int]] = list(lineas)
        self.fecha: datetime = fecha if fecha is not None else datetime.now()

    def calcular_total(self) -> float:
        """Calcula el importe total a partir de precios y cantidades."""
        return sum(producto.precio * cantidad for producto, cantidad in self.lineas)

    def __str__(self) -> str:
        """Devuelve un resumen legible del pedido."""
        texto = [
            f"Pedido [{self.id[:8]}] - {self.fecha:%d/%m/%Y %H:%M:%S}",
            f"Cliente: {self.cliente.nombre}",
        ]
        for producto, cantidad in self.lineas:
            subtotal = producto.precio * cantidad
            texto.append(
                f"  - {producto.nombre} x{cantidad} "
                f"({producto.precio:.2f} €/ud) = {subtotal:.2f} €"
            )
        texto.append(f"TOTAL: {self.calcular_total():.2f} €")
        return "\n".join(texto)
