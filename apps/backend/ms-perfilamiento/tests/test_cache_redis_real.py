"""Integracion contra un Redis real: los tests unitarios usan fakes, asi que nada probaba el
cliente de verdad (serializacion, TTL, conjuntos por consentimiento, autenticacion).

    REDIS_TEST_HOST=localhost REDIS_TEST_PORT=6379 pytest -m integration tests/test_cache_redis_real.py
    REDIS_TEST_AUTH_HOST=localhost REDIS_TEST_AUTH_PORT=6380 REDIS_TEST_AUTH_PASSWORD=... (Redis con requirepass)
    REDIS_TEST_TLS_HOST=localhost REDIS_TEST_TLS_PORT=6381 REDIS_TEST_TLS_PASSWORD=... (Redis con TLS y certificado
    autofirmado, ver README)

El TLS de ElastiCache (certificado de Amazon, token) solo se valida al desplegar, con el PING de arranque."""

import asyncio
import os
import ssl
from decimal import Decimal

import pytest
from redis.asyncio import Redis

from app.infrastructure.cache import CacheRedis, calentar_conexiones, crear_cliente_redis, verificar_conexion
from app.infrastructure.resiliencia import AdaptadorResiliente, InterruptorCircuito

pytestmark = pytest.mark.integration

ATRIBUTOS = {"nivel_ingresos_estimado": Decimal("1.25"), "zona_riesgo": Decimal("0.4")}


class Proveedor:
    def __init__(self) -> None:
        self.llamadas = 0
        self.caido = False

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        self.llamadas += 1
        if self.caido:
            raise ConnectionError("proveedor caido")
        return dict(ATRIBUTOS)


@pytest.fixture
async def redis():
    host = os.environ.get("REDIS_TEST_HOST")
    if not host:
        pytest.skip("requiere REDIS_TEST_HOST")
    cliente = Redis(host=host, port=int(os.environ.get("REDIS_TEST_PORT", "6379")))
    yield cliente
    await cliente.flushdb()
    await cliente.aclose()


def _adaptador(redis, proveedor, reloj):
    return AdaptadorResiliente(
        proveedor,
        CacheRedis(redis),
        "of",
        ttl_suave_s=600,
        ttl_duro_s=86400,
        presupuesto_ms=500,
        timeout_proveedor_ms=700,
        timeout_cache_ms=500,
        interruptor=InterruptorCircuito("of"),
        ahora=reloj,
    )


async def test_guarda_y_lee_los_atributos_con_su_fecha_y_su_ttl(redis):
    cache = CacheRedis(redis)

    await cache.guardar("perfilamiento:test:c1", ATRIBUTOS, 60, 1_700_000_000.5)

    guardado = await cache.leer("perfilamiento:test:c1")
    assert (guardado.atributos, guardado.capturado_en) == (ATRIBUTOS, 1_700_000_000.5)
    assert 0 < await redis.ttl("perfilamiento:test:c1") <= 60
    assert await cache.leer("perfilamiento:test:no-existe") is None


async def test_el_segundo_pedido_sale_de_la_cache_sin_llamar_al_proveedor(redis):
    proveedor = Proveedor()
    adaptador = _adaptador(redis, proveedor, lambda: 1000.0)

    primero = await adaptador.obtener_resuelto("cliente-1")
    segundo = await adaptador.obtener_resuelto("cliente-1")

    assert (primero.origen, segundo.origen) == ("proveedor", "cache")
    assert segundo.atributos == ATRIBUTOS
    assert proveedor.llamadas == 1


async def test_con_el_proveedor_caido_se_sirve_el_perfil_vencido_guardado(redis):
    proveedor = Proveedor()
    tiempo = [1000.0]
    adaptador = _adaptador(redis, proveedor, lambda: tiempo[0])
    await adaptador.obtener_resuelto("cliente-1")

    tiempo[0] += 700  # pasada la vigencia fresca, antes de la maxima
    proveedor.caido = True
    resuelto = await adaptador.obtener_resuelto("cliente-1")

    assert (resuelto.origen, resuelto.atributos) == ("vencido", ATRIBUTOS)
    assert resuelto.edad_segundos == 700
    assert await redis.ttl("perfilamiento:of:cliente-1") > 600  # sigue guardado hasta la vigencia maxima


async def test_revocar_el_consentimiento_borra_lo_guardado_bajo_el(redis):
    cache = CacheRedis(redis)
    await cache.guardar("perfilamiento:of:123", ATRIBUTOS, 600, 1.0, "consentimiento-1")
    await cache.guardar("perfilamiento:od:123", ATRIBUTOS, 600, 1.0, "consentimiento-1")
    await cache.guardar("perfilamiento:of:999", ATRIBUTOS, 600, 1.0, "consentimiento-2")

    borradas = await cache.invalidar_consentimiento("consentimiento-1")

    assert borradas == 2
    assert await cache.leer("perfilamiento:of:123") is None
    assert await cache.leer("perfilamiento:od:123") is None
    assert await cache.leer("perfilamiento:of:999") is not None
    assert await redis.exists("perfilamiento:consentimiento:consentimiento-1") == 0


async def test_calentar_deja_las_conexiones_abiertas_y_una_rafaga_no_abre_mas(redis):
    cliente = Redis(
        host=os.environ["REDIS_TEST_HOST"],
        port=int(os.environ.get("REDIS_TEST_PORT", "6379")),
        max_connections=10,
        socket_keepalive=True,
        health_check_interval=30,
    )
    try:
        async def conectados() -> int:
            return (await redis.info("clients"))["connected_clients"]

        inicial = await conectados()
        assert await calentar_conexiones(cliente, 5, 2000) == 5
        tras_calentar = await conectados()
        assert tras_calentar - inicial == 5

        await asyncio.gather(*(cliente.get("perfilamiento:rafaga") for _ in range(5)))

        assert await conectados() == tras_calentar  # la rafaga uso las conexiones ya abiertas
    finally:
        await cliente.aclose()


async def test_el_ping_de_arranque_responde_con_un_redis_vivo(redis):
    assert await verificar_conexion(redis, 2000) is True


async def test_con_token_conecta_con_la_clave_correcta_y_no_sin_ella():
    host = os.environ.get("REDIS_TEST_AUTH_HOST")
    clave = os.environ.get("REDIS_TEST_AUTH_PASSWORD")
    if not host or not clave:
        pytest.skip("requiere REDIS_TEST_AUTH_HOST y REDIS_TEST_AUTH_PASSWORD")
    puerto = int(os.environ.get("REDIS_TEST_AUTH_PORT", "6379"))
    con_clave = Redis(host=host, port=puerto, password=clave)
    sin_clave = Redis(host=host, port=puerto)
    try:
        assert await verificar_conexion(con_clave, 2000) is True
        assert await verificar_conexion(sin_clave, 2000) is False
    finally:
        await con_clave.aclose()
        await sin_clave.aclose()


@pytest.fixture
def tls():
    host = os.environ.get("REDIS_TEST_TLS_HOST")
    if not host:
        pytest.skip("requiere REDIS_TEST_TLS_HOST")
    return {
        "host": host,
        "port": int(os.environ.get("REDIS_TEST_TLS_PORT", "6379")),
        "password": os.environ.get("REDIS_TEST_TLS_PASSWORD"),
    }


def _contar_contextos_ssl(monkeypatch) -> list[int]:
    creados: list[int] = []
    original = ssl.create_default_context

    def contado(*args, **kwargs):
        creados.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(ssl, "create_default_context", contado)
    return creados


async def test_con_tls_el_pool_crea_el_contexto_ssl_una_sola_vez(tls, monkeypatch):
    creados = _contar_contextos_ssl(monkeypatch)
    cliente = crear_cliente_redis(**tls, ssl=True, max_connections=10, health_check_interval=30, ssl_cert_reqs="none")
    try:
        assert await verificar_conexion(cliente, 2000) is True
        assert await calentar_conexiones(cliente, 5, 2000) == 5
        await asyncio.gather(*(cliente.ping() for _ in range(5)))
    finally:
        await cliente.aclose(close_connection_pool=True)

    assert len(creados) == 1


async def test_control_el_cliente_sin_contexto_compartido_crea_uno_por_conexion(tls, monkeypatch):
    """Documenta la causa del costo: el cliente de redis-py por defecto construye un contexto SSL
    nuevo en cada conexion."""
    creados = _contar_contextos_ssl(monkeypatch)
    cliente = Redis(**tls, ssl=True, ssl_cert_reqs="none", max_connections=10)
    try:
        assert await calentar_conexiones(cliente, 5, 2000) == 5
    finally:
        await cliente.aclose(close_connection_pool=True)

    assert len(creados) == 5

