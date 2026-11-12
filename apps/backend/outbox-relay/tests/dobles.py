from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import UUID

from app.domain.modelos import EventoOutbox
from app.ports.publicador import PublicadorEventos


class RepositorioOutboxDoble:
    """`RepositorioOutbox` en memoria: una lista de pendientes por esquema."""

    def __init__(self, esquema: str, pendientes: list[EventoOutbox] | None = None) -> None:
        self.esquema = esquema
        self.pendientes = list(pendientes or [])
        self.publicados: list[EventoOutbox] = []
        self.fallar: Exception | None = None
        # Señal real de sincronización para tests que esperan a que
        # bucle_relay (corriendo en background) ejecute al menos un ciclo --
        # evita dormir un tiempo fijo, no determinista y prohibido por el
        # gate de CI para tests unitarios.
        self.llamado = asyncio.Event()

    async def publicar_pendientes(
        self, publicador: PublicadorEventos, lote: int, ahora: datetime
    ) -> int:
        self.llamado.set()
        if self.fallar is not None:
            raise self.fallar

        a_publicar = self.pendientes[:lote]
        for evento in a_publicar:
            await publicador.publicar(evento)
            self.publicados.append(evento)
        self.pendientes = self.pendientes[len(a_publicar) :]
        return len(a_publicar)


class PublicadorDoble:
    """`PublicadorEventos` en memoria: guarda lo publicado, puede simular fallo."""

    def __init__(self) -> None:
        self.publicados: list[EventoOutbox] = []
        self.cerrado = False
        self.fallar: Exception | None = None

    async def publicar(self, evento: EventoOutbox) -> None:
        if self.fallar is not None:
            raise self.fallar
        self.publicados.append(evento)

    async def cerrar(self) -> None:
        self.cerrado = True


def evento_outbox(
    esquema: str = "ms_cotizacion",
    tipo: str = "PolizaEmitida",
    agregado_id: UUID | None = None,
    payload: dict | None = None,
) -> EventoOutbox:
    from uuid import uuid4

    return EventoOutbox(
        evento_id=uuid4(),
        esquema=esquema,
        tipo=tipo,
        agregado_id=agregado_id or uuid4(),
        payload=payload or {"usuario_id": str(uuid4())},
        creado_en=datetime.now(),
    )
