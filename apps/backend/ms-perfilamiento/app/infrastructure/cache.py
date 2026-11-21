from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal
from typing import Any, Protocol

from app.ports.cache import CacheAtributos

logger = logging.getLogger(__name__)


async def verificar_conexion(cliente: Any, timeout_ms: int) -> bool:
    """PING al arrancar. Nunca tumba el servicio (la cache es opcional), pero deja a la
    vista si quedo habilitada: sin esto, un host, un token o un TLS mal puestos solo se
    notan porque el AdaptadorConCache traga el error en cada peticion."""
    try:
        await asyncio.wait_for(cliente.ping(), timeout=timeout_ms / 1000)
    except Exception:
        logger.warning("cache redis no responde al arrancar; cada peticion consultara al proveedor", exc_info=True)
        return False
    logger.info("cache redis conectada")
    return True


class _AdaptadorAtributos(Protocol):
    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]: ...


class CacheRedis:
    def __init__(self, cliente: Any) -> None:
        self._cliente = cliente

    async def leer(self, clave: str) -> dict[str, Decimal] | None:
        crudo = await self._cliente.get(clave)
        if crudo is None:
            return None
        return {nombre: Decimal(valor) for nombre, valor in json.loads(crudo).items()}

    async def guardar(self, clave: str, atributos: dict[str, Decimal], ttl_segundos: int) -> None:
        crudo = json.dumps({nombre: str(valor) for nombre, valor in atributos.items()})
        await self._cliente.set(clave, crudo, ex=ttl_segundos)


class AdaptadorConCache:
    def __init__(
        self,
        adaptador: _AdaptadorAtributos,
        cache: CacheAtributos,
        prefijo: str,
        ttl_segundos: int,
        timeout_ms: int,
    ) -> None:
        self._adaptador = adaptador
        self._cache = cache
        self._prefijo = prefijo
        self._ttl_segundos = ttl_segundos
        self._timeout = timeout_ms / 1000

    def _clave(self, cliente_id: str) -> str:
        return f"perfilamiento:{self._prefijo}:{cliente_id}"

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        clave = self._clave(cliente_id)
        try:
            en_cache = await asyncio.wait_for(self._cache.leer(clave), timeout=self._timeout)
        except Exception:
            logger.warning("cache %s no disponible al leer; se consulta al proveedor", self._prefijo)
            en_cache = None
        if en_cache is not None:
            return en_cache

        atributos = await self._adaptador.obtener_atributos(cliente_id)
        try:
            await asyncio.wait_for(self._cache.guardar(clave, atributos, self._ttl_segundos), timeout=self._timeout)
        except Exception:
            logger.warning("cache %s no disponible al guardar", self._prefijo)
        return atributos
