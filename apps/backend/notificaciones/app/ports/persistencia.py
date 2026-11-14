from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.modelos import Difusion, DispositivoPush, Notificacion


class NotificacionDuplicada(Exception):
    """Carrera al crear por (evento_origen_id, canal): otro proceso ganó."""


class DispositivoDuplicado(Exception):
    """Carrera al registrar (usuario_id, token): otro proceso ganó."""


class RepositorioNotificaciones(Protocol):
    async def obtener(self, notificacion_id: UUID) -> Notificacion | None: ...

    async def obtener_por_evento_canal(
        self, evento_origen_id: UUID, canal: str
    ) -> Notificacion | None: ...

    async def listar(
        self, usuario_id: UUID, limite: int, antes_de: datetime | None = None
    ) -> list[Notificacion]: ...

    async def listar_pendientes_push(
        self, usuario_id: UUID | None = None, limite: int = 100
    ) -> list[Notificacion]: ...

    async def agregar(self, notificacion: Notificacion) -> None: ...

    async def actualizar(self, notificacion: Notificacion) -> None: ...


class RepositorioDispositivos(Protocol):
    async def obtener(self, dispositivo_id: UUID) -> DispositivoPush | None: ...

    async def obtener_por_usuario_token(
        self, usuario_id: UUID, token: str
    ) -> DispositivoPush | None: ...

    async def listar_activos(self, usuario_id: UUID) -> list[DispositivoPush]: ...

    async def agregar(self, dispositivo: DispositivoPush) -> None: ...

    async def actualizar(self, dispositivo: DispositivoPush) -> None: ...

    async def contar_activos(self, usuario_ids: list[UUID] | None) -> list[tuple[UUID, int]]: ...

    async def desactivar_de_usuario(self, usuario_id: UUID) -> None: ...


class RepositorioDifusiones(Protocol):
    async def agregar(self, difusion: Difusion) -> None: ...

    async def actualizar_totales(
        self, difusion_id: UUID, enviadas: int, fallidas: int, sin_dispositivo: int
    ) -> None: ...

    async def listar(self, limite: int, antes_de: datetime | None = None) -> list[Difusion]: ...


class RepositorioEventos(Protocol):
    async def consumir(self, evento_id: UUID, tipo: str) -> bool: ...


class UnidadDeTrabajo(Protocol):
    notificaciones: RepositorioNotificaciones
    dispositivos: RepositorioDispositivos
    difusiones: RepositorioDifusiones
    eventos: RepositorioEventos

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None: ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
