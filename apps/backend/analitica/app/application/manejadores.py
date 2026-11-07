from __future__ import annotations

import logging

from app.domain.eventos import EventoBus
from app.domain.modelos import TIPOS_SOPORTADOS
from app.ports.persistencia import EventoYaProcesado, FabricaUnidadDeTrabajo

logger = logging.getLogger(__name__)


async def manejar_evento(uow: FabricaUnidadDeTrabajo, evento: EventoBus) -> bool:
    """Incrementa el contador agregado (tipo, fecha de `ocurrido_en`) por evento del bus.

    Idempotente por `evento_id` (ver RepositorioMetricas.incrementar): repetir
    el mensaje no duplica el conteo. Nunca propaga excepciones para no
    detener el consumo de la partición.
    """
    if evento.tipo not in TIPOS_SOPORTADOS:
        logger.warning(
            "evento_ignorado", extra={"evento_id": str(evento.evento_id), "tipo": evento.tipo}
        )
        return False

    fecha = evento.ocurrido_en.date() if evento.ocurrido_en is not None else None
    if fecha is None:
        logger.warning(
            "evento_sin_fecha", extra={"evento_id": str(evento.evento_id), "tipo": evento.tipo}
        )
        return False

    try:
        async with uow() as tx:
            await tx.metricas.incrementar(str(evento.evento_id), evento.tipo, fecha)
            await tx.confirmar()
        return True
    except EventoYaProcesado:
        logger.info(
            "evento_ya_procesado", extra={"evento_id": str(evento.evento_id), "tipo": evento.tipo}
        )
        return False
    except Exception:
        logger.exception(
            "error_manejando_evento",
            extra={"evento_id": str(evento.evento_id), "tipo": evento.tipo},
        )
        return False
