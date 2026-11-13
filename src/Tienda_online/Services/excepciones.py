"""Excepciones de la lógica de negocio de la tienda.

Todas heredan de ``ValueError`` para seguir siendo compatibles con el código
de la Práctica 1 (que capturaba ``ValueError``). Al distinguir el tipo de
error, la capa de API (main.py) puede traducir cada uno al código HTTP
adecuado sin que el servicio tenga que saber nada de HTTP.
"""


class TiendaError(ValueError):
    """Error genérico de la tienda (petición incorrecta -> 400)."""


class NoEncontradoError(TiendaError):
    """El usuario o producto solicitado no existe (-> 404)."""


class ConflictoError(TiendaError):
    """La operación choca con el estado actual de la tienda (-> 409).

    Por ejemplo, registrar un email que ya está en uso.
    """


class StockInsuficienteError(ConflictoError):
    """No hay unidades suficientes de un producto para el pedido (-> 409)."""


class OperacionNoPermitidaError(TiendaError):
    """El usuario no puede realizar la operación, p. ej. un administrador
    intentando hacer un pedido (-> 400)."""
