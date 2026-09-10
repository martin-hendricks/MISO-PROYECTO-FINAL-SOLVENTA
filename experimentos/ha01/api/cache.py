"""`:CacheOF` — copia local del perfil de Open Finance con su marca de tiempo.

Dos reglas que deciden la validez del brazo C:

1. La entrada NO lleva `EX`. Si expirara en Redis no quedaria ultimo valor
   conocido y la degradacion elegante dejaria de existir. La edad se evalua
   en la aplicacion contra TTL (cuando conviene refrescar) y MAX_AGE (hasta
   cuando sigue siendo utilizable como respaldo).

2. El perfil almacenado NO guarda su `origen`. El origen depende de COMO se
   resolvio esta peticion, no de como se obtuvo el dato: un perfil escrito
   por el adaptador y leido despues de la cache es un acierto de cache, no
   una invocacion. Guardarlo dentro del blob hacia que el camino caliente se
   etiquetara como frio y que la edad se reportara como cero.
"""
from datetime import datetime, timezone

import orjson
import redis.asyncio as redis

from . import config
from .metrics import CACHE_ERRORS


def edad_segundos(perfil: dict | None) -> float:
    """Antiguedad del perfil en segundos. inf si no tiene marca de tiempo."""
    if not perfil or not perfil.get("obtenido_en"):
        return float("inf")
    try:
        t = datetime.fromisoformat(perfil["obtenido_en"])
    except (TypeError, ValueError):
        return float("inf")
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - t).total_seconds())


class CacheOF:
    def __init__(self, url: str | None = None) -> None:
        self._r = redis.from_url(url or config.REDIS_URL, decode_responses=False)

    async def aclose(self) -> None:
        await self._r.aclose()

    @staticmethod
    def clave(customer_id: str) -> str:
        return f"{config.CACHE_KEY_PREFIX}{customer_id}"

    async def leer(self, customer_id: str) -> dict | None:
        try:
            crudo = await self._r.get(self.clave(customer_id))
        except Exception:
            CACHE_ERRORS.inc()
            return None
        if crudo is None:
            return None
        try:
            return orjson.loads(crudo)
        except orjson.JSONDecodeError:
            CACHE_ERRORS.inc()
            return None

    async def escribir(self, customer_id: str, perfil: dict) -> None:
        try:
            # Sin EX. Ver la nota del encabezado.
            await self._r.set(self.clave(customer_id), orjson.dumps(perfil))
        except Exception:
            CACHE_ERRORS.inc()

    async def ping(self) -> bool:
        try:
            return bool(await self._r.ping())
        except Exception:
            return False

    async def info_memoria(self) -> dict:
        try:
            info = await self._r.info("stats")
            mem = await self._r.info("memory")
            return {
                "evicted_keys": int(info.get("evicted_keys", 0)),
                "used_memory_human": mem.get("used_memory_human"),
                "claves": int(await self._r.dbsize()),
            }
        except Exception:
            return {}
