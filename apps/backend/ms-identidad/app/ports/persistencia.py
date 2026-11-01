from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from app.domain.modelos import Usuario


class CuentaYaExiste(Exception):
    """El repositorio SQL la levanta cuando el commit choca contra
    uq_usuario_documento o uq_usuario_email; el caso de uso la traduce a
    CuentaDuplicada (error de dominio) sin exponer cuál constraint chocó."""


class RepositorioUsuarios(Protocol):
    async def obtener_por_email(self, email: str) -> Usuario | None: ...

    async def obtener_por_documento(self, tipo_documento: str, numero_documento: str) -> Usuario | None: ...

    async def agregar(self, usuario: Usuario) -> None: ...


class UnidadDeTrabajo(Protocol):
    usuarios: RepositorioUsuarios

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None: ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
