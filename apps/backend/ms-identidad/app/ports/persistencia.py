from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.domain.modelos import EventoDominio, Usuario

TAMANO_PAGINA_CLIENTES = 20


class CuentaYaExiste(Exception):
    """El repositorio SQL la levanta cuando el commit choca contra
    uq_usuario_documento o uq_usuario_email; el caso de uso la traduce a
    CuentaDuplicada (error de dominio) sin exponer cuál constraint chocó."""


class RepositorioUsuarios(Protocol):
    async def obtener_por_email(self, email: str) -> Usuario | None: ...

    async def obtener_por_documento(self, tipo_documento: str, numero_documento: str) -> Usuario | None: ...

    async def obtener_por_id(self, usuario_id) -> Usuario | None: ...

    async def agregar(self, usuario: Usuario) -> None: ...

    async def actualizar(self, usuario: Usuario) -> None: ...

    async def listar_clientes(
        self,
        estado: str | None,
        q: str | None,
        ids: list[UUID] | None,
        pagina: int,
    ) -> tuple[list[Usuario], bool]: ...


class Outbox(Protocol):
    async def agregar(self, evento: EventoDominio) -> None: ...


class UnidadDeTrabajo(Protocol):
    usuarios: RepositorioUsuarios
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None: ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
