"""Brazo B — cache-aside clásico: ante un acierto responde de inmediato;
ante un fallo invoca al proveedor y ESPERA el resultado antes de responder.
Aísla el efecto de la caché del efecto del desacople (brazo C)."""

import time

import orjson

from .. import adaptador_of
from ..cache import redis_client
from ..config import settings
from ..metrics import CACHE_HITS, CACHE_MISSES
from ..rating_engine import calcular_prima


def _key(cliente_id: int) -> str:
    return f"perfil:of:{cliente_id}"


async def resolver_oferta(cliente_id: int) -> tuple[float, str]:
    cached = await redis_client.get(_key(cliente_id))
    if cached is not None:
        CACHE_HITS.inc()
        perfil = orjson.loads(cached)
        prima = await calcular_prima(cliente_id, perfil)
        return prima, "cache"

    CACHE_MISSES.inc()
    perfil = await adaptador_of.consultar_perfil(cliente_id)
    if perfil is not None:
        payload = orjson.dumps({**perfil, "cacheado_en": time.time()})
        await redis_client.set(_key(cliente_id), payload, ex=settings.cache_ttl_seconds)
        prima = await calcular_prima(cliente_id, perfil)
        return prima, "fresco"

    prima = await calcular_prima(cliente_id, None)
    return prima, "respaldo_default"
