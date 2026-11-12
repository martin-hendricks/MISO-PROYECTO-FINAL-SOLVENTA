from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.application.relay import validar_esquema
from app.domain.modelos import EventoOutbox
from app.ports.publicador import PublicadorEventos


def crear_motor(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


class RepositorioOutboxSQL:
    """Lee `outbox_evento` de UN esquema productor y publica lo pendiente.

    `esquema` se valida en el constructor (nunca dentro de una query): el
    nombre se interpola en el SQL -- no puede ir como bind param -- así que
    todo el que construye este repositorio ya pasó por `validar_esquema`.
    Los VALORES (lote, ahora, ids) sí van siempre como bind params.
    """

    def __init__(self, motor: AsyncEngine, esquema: str) -> None:
        self._motor = motor
        self._esquema = validar_esquema(esquema)

    async def publicar_pendientes(
        self, publicador: PublicadorEventos, lote: int, ahora: datetime
    ) -> int:
        # Una sola transacción para el lote completo: si `publicador.publicar`
        # falla a mitad de camino, la excepción se propaga sin commit -- nada
        # de lo ya marcado en esta transacción queda confirmado, así que el
        # próximo ciclo reintenta el lote entero en vez de dejar huecos.
        async with self._motor.begin() as conn:
            filas = (
                await conn.execute(
                    text(
                        f"""
                        SELECT id, tipo, agregado_id, payload, creado_en
                        FROM {self._esquema}.outbox_evento
                        WHERE publicado_en IS NULL
                        ORDER BY creado_en ASC
                        LIMIT :lote
                        FOR UPDATE SKIP LOCKED
                        """
                    ),
                    {"lote": lote},
                )
            ).all()

            for fila in filas:
                evento = EventoOutbox(
                    evento_id=UUID(str(fila.id)),
                    esquema=self._esquema,
                    tipo=fila.tipo,
                    agregado_id=UUID(str(fila.agregado_id)),
                    payload=fila.payload,
                    creado_en=fila.creado_en,
                )
                await publicador.publicar(evento)
                await conn.execute(
                    text(
                        f"""
                        UPDATE {self._esquema}.outbox_evento
                        SET publicado_en = :ahora
                        WHERE id = :id
                        """
                    ),
                    {"ahora": ahora, "id": evento.evento_id},
                )

            return len(filas)
