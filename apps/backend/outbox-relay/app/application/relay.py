from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from app.ports.persistencia import RepositorioOutbox
from app.ports.publicador import PublicadorEventos

logger = logging.getLogger(__name__)

# Allowlist de esquemas con outbox_evento. El nombre del esquema se interpola
# en SQL (no puede ir como bind param), así que además del patrón se exige
# pertenecer a este conjunto: cualquier valor inesperado —de configuración o
# de un JSON manipulado— falla cerrado antes de tocar la base.
ESQUEMAS_PERMITIDOS = frozenset(
    {
        "ms_cotizacion",
        "ms_suscripcion",
        "ms_pagos",
        "ms_perfilamiento",
        "ms_polizas",
        "ms_siniestros",
        "ms_identidad",
    }
)
_PATRON_ESQUEMA = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class FuenteOutbox:
    esquema: str
    database_url: str


def validar_esquema(nombre: str) -> str:
    if not isinstance(nombre, str) or not _PATRON_ESQUEMA.fullmatch(nombre):
        raise ValueError(f"Esquema de outbox inválido: {nombre!r}")
    if nombre not in ESQUEMAS_PERMITIDOS:
        raise ValueError(f"Esquema de outbox no permitido: {nombre!r}")
    return nombre


async def ejecutar_ciclo(
    repositorios: Sequence[RepositorioOutbox],
    publicador: PublicadorEventos,
    lote: int,
    ahora: datetime,
) -> int:
    total = 0
    for repositorio in repositorios:
        try:
            total += await repositorio.publicar_pendientes(publicador, lote, ahora)
        except Exception:
            # Una base caída o un fallo de Kafka en un esquema no debe frenar
            # los demás: cada fuente es una transacción independiente.
            logger.exception("Falló la publicación de una fuente de outbox; se continúa")
    return total


async def bucle_relay(
    repositorios: Sequence[RepositorioOutbox],
    publicador: PublicadorEventos,
    lote: int,
    intervalo_segundos: float,
    parar: asyncio.Event,
) -> None:
    while not parar.is_set():
        try:
            await ejecutar_ciclo(repositorios, publicador, lote, datetime.now(UTC))
        except Exception:
            # ejecutar_ciclo ya aísla por fuente; esto cubre cualquier fallo
            # inesperado del propio ciclo para que la tarea nunca muera.
            logger.exception("Ciclo de relay falló; se reintenta en el próximo intervalo")

        try:
            await asyncio.wait_for(parar.wait(), timeout=intervalo_segundos)
        except TimeoutError:
            continue
