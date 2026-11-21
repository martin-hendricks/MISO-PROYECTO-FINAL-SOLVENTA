from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal
from typing import Any

from app.ports.cache import PerfilGuardado

logger = logging.getLogger(__name__)


async def verificar_conexion(cliente: Any, timeout_ms: int) -> bool:
    """PING al arrancar. Nunca tumba el servicio (la cache es opcional), pero deja a la
    vista si quedo habilitada: sin esto, un host, un token o un TLS mal puestos solo se
    notan porque el adaptador con cache traga el error en cada peticion."""
    try:
        await asyncio.wait_for(cliente.ping(), timeout=timeout_ms / 1000)
    except Exception:
        logger.warning("cache redis no responde al arrancar; cada peticion consultara al proveedor", exc_info=True)
        return False
    logger.info("cache redis conectada")
    return True


def _indice_consentimiento(consentimiento_id: str) -> str:
    return f"perfilamiento:consentimiento:{consentimiento_id}"


class CacheRedis:
    """Cache compartida entre replicas. Guarda los atributos con la fecha de captura y, si se
    conoce el consentimiento, anota la clave en un conjunto por consentimiento: las entradas
    se indexan por cedula y quien revoca solo conoce el consentimiento."""

    def __init__(self, cliente: Any) -> None:
        self._cliente = cliente

    async def leer(self, clave: str) -> PerfilGuardado | None:
        crudo = await self._cliente.get(clave)
        if crudo is None:
            return None
        datos = json.loads(crudo)
        atributos = {nombre: Decimal(valor) for nombre, valor in datos["atributos"].items()}
        return PerfilGuardado(atributos, float(datos["capturado_en"]))

    async def guardar(
        self,
        clave: str,
        atributos: dict[str, Decimal],
        ttl_segundos: int,
        capturado_en: float,
        consentimiento_id: str | None = None,
    ) -> None:
        crudo = json.dumps(
            {"atributos": {nombre: str(valor) for nombre, valor in atributos.items()}, "capturado_en": capturado_en}
        )
        await self._cliente.set(clave, crudo, ex=ttl_segundos)
        if consentimiento_id:
            indice = _indice_consentimiento(consentimiento_id)
            await self._cliente.sadd(indice, clave)
            await self._cliente.expire(indice, ttl_segundos)

    async def invalidar_consentimiento(self, consentimiento_id: str) -> int:
        """Borra lo guardado bajo un consentimiento revocado. Devuelve cuantas entradas."""
        indice = _indice_consentimiento(consentimiento_id)
        claves = await self._cliente.smembers(indice)
        if claves:
            await self._cliente.delete(*claves)
        await self._cliente.delete(indice)
        return len(claves)
