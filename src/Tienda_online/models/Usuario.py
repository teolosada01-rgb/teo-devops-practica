"""Modelos de usuario de la tienda online."""

import uuid


class Usuario:
    """Representa a cualquier persona que interactúa con la tienda."""

    def __init__(self, nombre: str, email: str) -> None:
        """Crea un usuario con un identificador único.

        Args:
            nombre: Nombre del usuario.
            email: Correo electrónico del usuario.
        """
        if "@" not in email:
            raise ValueError(f"Email no válido: {email}")

        self.id: str = str(uuid.uuid4())
        self.nombre: str = nombre
        self.email: str = email

    def is_admin(self) -> bool:
        """Indica si el usuario es administrador (por defecto, no)."""
        return False

    def __str__(self) -> str:
        """Devuelve una descripción legible del usuario."""
        return f"[{self.id[:8]}] {self.nombre} <{self.email}>"


class Cliente(Usuario):
    """Usuario que realiza compras en la tienda."""

    def __init__(self, nombre: str, email: str, direccion: str) -> None:
        """Crea un cliente.

        Args:
            direccion: Dirección postal de envío.
        """
        super().__init__(nombre, email)
        self.direccion: str = direccion

    def __str__(self) -> str:
        """Añade el tipo y la dirección a la descripción."""
        return f"Cliente {super().__str__()} | Dirección: {self.direccion}"


class Administrador(Usuario):
    """Usuario que gestiona la tienda."""

    def is_admin(self) -> bool:
        """Los administradores siempre tienen permisos de administración."""
        return True

    def __str__(self) -> str:
        """Añade el tipo a la descripción."""
        return f"Administrador {super().__str__()}"
