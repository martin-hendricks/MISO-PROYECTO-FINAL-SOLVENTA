import orjson
from .. import cache
from ..config import settings
from ..metrics import CACHE_HITS, CACHE_MISSES
from . import arm_b

def key(siniestro_id: int) -> str:
    return f"siniestro:estado:{siniestro_id}"

async def get_estado(siniestro_id: int) -> dict | None:
    cached = await cache.redis_client.get(key(siniestro_id))
    if cached is not None:
        CACHE_HITS.inc()
        return orjson.loads(cached)

    CACHE_MISSES.inc()
    data = await arm_b.get_estado(siniestro_id)
    if data is not None and settings.cache_ttl_seconds > 0:
        # TTL <= 0 equivale a "sin caché" (punto de sensibilidad 2 del
        # diseño): Redis rechaza EX <= 0 en SET, así que se omite la
        # escritura en vez de propagar el error.
        await cache.redis_client.set(
            key(siniestro_id), orjson.dumps(data),
            ex=settings.cache_ttl_seconds,
        )
    return data


async def get_estado_raw(siniestro_id: int) -> bytes | None:
    """Brazo C': devuelve bytes JSON sin re-serializar (bypass de Pydantic)."""
    cached = await cache.redis_client.get(key(siniestro_id))
    if cached is not None:
        CACHE_HITS.inc()
        return cached
    CACHE_MISSES.inc()
    data = await arm_b.get_estado(siniestro_id)
    if data is None:
        return None
    raw = orjson.dumps(data)
    if settings.cache_ttl_seconds > 0:
        await cache.redis_client.set(key(siniestro_id), raw, ex=settings.cache_ttl_seconds)
    return raw
