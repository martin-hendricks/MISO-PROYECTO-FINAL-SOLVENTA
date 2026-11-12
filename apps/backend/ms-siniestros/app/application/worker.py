"""Worker de evaluación asíncrona del siniestro asistido.

Corre dentro del proceso del servicio (tarea de fondo del lifespan). La "cola" es la propia
tabla `siniestro` (avisos asistidos en RECIBIDO) leída con FOR UPDATE SKIP LOCKED, así que
funciona igual con varias réplicas y no depende del publicador del outbox (N12), que aún no
existe. Cuando exista el bus, este disparador puede pasar a consumir AvisoSiniestroRecibido
sin tocar el caso de uso.
"""

from __future__ import annotations

import asyncio
import logging

from app.application.avisos import evaluar_pendientes
from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import FabricaUnidadDeTrabajo

log = logging.getLogger(__name__)


async def ciclo_de_evaluacion(
    uow: FabricaUnidadDeTrabajo,
    adaptador_desembolso: AdaptadorDesembolso,
    intervalo_segundos: float,
    detener: asyncio.Event,
    lote: int = 20,
) -> None:
    while not detener.is_set():
        try:
            procesados = await evaluar_pendientes(uow, adaptador_desembolso, lote)
            if procesados:
                log.info("Worker de siniestros evaluó %d aviso(s)", procesados)
        except Exception:  # noqa: BLE001 - p. ej. base caída: se reintenta en el próximo ciclo
            log.exception("Ciclo del worker de siniestros falló")
        try:
            await asyncio.wait_for(detener.wait(), timeout=intervalo_segundos)
        except TimeoutError:
            pass
