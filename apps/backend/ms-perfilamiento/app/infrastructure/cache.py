from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal
from typing import Any

from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.connection import SSLConnection

from app.ports.cache import PerfilGuardado

logger = logging.getLogger(__name__)


def _conexion_ssl_con_contexto_compartido() -> type[SSLConnection]:
    """redis-py crea un contexto SSL nuevo por cada conexion, y construirlo (cargar las CA del
    sistema) cuesta unos 70 ms de CPU en el pod, que ademas bloquean el event loop. Medido contra
    ElastiCache: abrir una conexion tarda ~79 ms; con un contexto ya creado, ~8 ms. Las conexiones
    de un mismo pool comparten el primero que se construya."""
    compartido: dict[str, Any] = {}

    class ConexionSSLCompartida(SSLConnection):
        def __init__(self, **opciones: Any) -> None:
            super().__init__(**opciones)
            self.ssl_context = compartido.setdefault("contexto", self.ssl_context)

    return ConexionSSLCompartida


def crear_cliente_redis(
    host: str,
    port: int,
    password: str | None,
    ssl: bool,
    max_connections: int,
    health_check_interval: int,
    **opciones_ssl: Any,
) -> Redis:
    """Cliente de la cache: pool acotado, con keepalive y verificacion de las conexiones
    inactivas, y con el contexto SSL compartido si hay TLS. Al cerrarlo hay que pedir
    `aclose(close_connection_pool=True)`: el cliente no cierra un pool que le pasan. `opciones_ssl`
    solo se usa en los tests (por ejemplo `ssl_cert_reqs="none"` con un certificado autofirmado)."""
    opciones = {
        "host": host,
        "port": port,
        "password": password or None,
        "socket_keepalive": True,
        "health_check_interval": health_check_interval,
    }
    if ssl:
        pool = ConnectionPool(
            connection_class=_conexion_ssl_con_contexto_compartido(),
            max_connections=max_connections,
            **opciones,
            **opciones_ssl,
        )
    else:
        pool = ConnectionPool(max_connections=max_connections, **opciones)
    return Redis(connection_pool=pool)


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


async def calentar_conexiones(cliente: Any, cantidad: int, timeout_ms: int) -> int:
    """Deja `cantidad` conexiones abiertas en el pool. Abrir una conexion a ElastiCache (TCP +
    TLS + token) tarda mas que el timeout de una operacion de cache: sin esto, la primera
    operacion de cada conexion nueva expira y esa peticion se queda sin cache ni perfil vencido
    de respaldo. Se toman del pool y se devuelven (no con PING en paralelo: los rapidos terminan
    y sus conexiones se reutilizan, asi que el pool no llega a `cantidad`). Devuelve cuantas
    abrio; si alguna falla solo se registra."""
    if cantidad <= 0:
        return 0
    pool = cliente.connection_pool
    resultados = await asyncio.gather(
        *(asyncio.wait_for(pool.get_connection(), timeout=timeout_ms / 1000) for _ in range(cantidad)),
        return_exceptions=True,
    )
    abiertas = [resultado for resultado in resultados if not isinstance(resultado, BaseException)]
    for conexion in abiertas:
        await pool.release(conexion)
    if len(abiertas) < cantidad:
        logger.warning("cache redis: solo se abrieron %d de %d conexiones al arrancar", len(abiertas), cantidad)
    else:
        logger.info("cache redis: %d conexiones abiertas al arrancar", len(abiertas))
    return len(abiertas)


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
