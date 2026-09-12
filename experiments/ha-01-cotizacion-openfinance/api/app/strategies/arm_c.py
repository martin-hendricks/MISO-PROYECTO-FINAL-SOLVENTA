"""Brazo C — actualización oportunista: la invocación al proveedor se
lanza con un presupuesto de 120 ms; al agotarse, la respuesta se resuelve
con el último valor conocido (aunque vencido) o con el valor por defecto,
y la invocación CONTINÚA en segundo plano hasta su timeout duro,
repoblando la caché si llega a completarse. La respuesta nunca espera al
proveedor más allá del presupuesto.

Brazo C' — igual que C, añadiendo coalescencia por clave (single-flight):
varias peticiones concurrentes con fallo sobre el mismo perfil comparten
una única invocación al proveedor en vez de disparar N invocaciones
idénticas (punto de sensibilidad 5, estampida)."""

import asyncio
import time

import orjson

from .. import adaptador_of
from ..cache import redis_client
from ..config import settings
from ..metrics import CACHE_HITS, CACHE_MISSES, FALLBACK_RESPONSES
from ..rating_engine import calcular_prima

# Coalescencia por clave (solo brazo C'): futuros compartidos por
# cliente_id para que un fallo concurrente dispare una sola invocación.
_in_flight: dict[int, asyncio.Future] = {}


def _key(cliente_id: int) -> str:
    return f"perfil:of:{cliente_id}"


async def _refrescar_en_segundo_plano(cliente_id: int) -> dict | None:
    perfil = await adaptador_of.consultar_perfil(cliente_id)
    if perfil is not None:
        payload = orjson.dumps({**perfil, "cacheado_en": time.time()})
        await redis_client.set(_key(cliente_id), payload, ex=settings.cache_ttl_seconds)
    return perfil


async def _refrescar_coalescido(cliente_id: int) -> dict | None:
    existing = _in_flight.get(cliente_id)
    if existing is not None and not existing.done():
        return await existing

    loop = asyncio.get_event_loop()
    fut: asyncio.Future = loop.create_future()
    _in_flight[cliente_id] = fut
    try:
        perfil = await _refrescar_en_segundo_plano(cliente_id)
        if not fut.done():
            fut.set_result(perfil)
        return perfil
    finally:
        _in_flight.pop(cliente_id, None)


async def _resolver(cliente_id: int, *, coalesce: bool) -> tuple[float, str]:
    cached_raw = await redis_client.get(_key(cliente_id))
    cached = orjson.loads(cached_raw) if cached_raw is not None else None

    if cached is not None:
        CACHE_HITS.inc()
    else:
        CACHE_MISSES.inc()

    refresh_coro = (
        _refrescar_coalescido(cliente_id) if coalesce
        else _refrescar_en_segundo_plano(cliente_id)
    )
    task = asyncio.ensure_future(refresh_coro)

    try:
        perfil_fresco = await asyncio.wait_for(
            asyncio.shield(task), timeout=settings.dependency_budget_ms / 1000.0
        )
    except asyncio.TimeoutError:
        perfil_fresco = None
        # La tarea de refresco sigue viva y repobla la caché si completa
        # (no se cancela): es la esencia de la actualización oportunista.

    if perfil_fresco is not None:
        prima = await calcular_prima(cliente_id, perfil_fresco)
        return prima, "fresco"

    if cached is not None:
        prima = await calcular_prima(cliente_id, cached)
        FALLBACK_RESPONSES.labels(origin="stale_cache").inc()
        return prima, "cache"

    prima = await calcular_prima(cliente_id, None)
    FALLBACK_RESPONSES.labels(origin="default_value").inc()
    return prima, "respaldo_default"


async def resolver_oferta(cliente_id: int) -> tuple[float, str]:
    return await _resolver(cliente_id, coalesce=False)


async def resolver_oferta_coalescida(cliente_id: int) -> tuple[float, str]:
    return await _resolver(cliente_id, coalesce=True)
