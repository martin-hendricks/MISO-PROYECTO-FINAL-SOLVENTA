"""Integracion contra un Redis real: los tests unitarios de la cache usan fakes, asi que
nada probaba el cliente de verdad (serializacion, TTL, autenticacion).

    REDIS_TEST_HOST=localhost REDIS_TEST_PORT=6379 pytest -m integration tests/test_cache_redis_real.py
    REDIS_TEST_AUTH_HOST=localhost REDIS_TEST_AUTH_PORT=6380 REDIS_TEST_AUTH_PASSWORD=... (Redis con requirepass)

TLS no se prueba aqui: ElastiCache lo exige y un Redis local con certificados no aporta
al contrato; se valida al desplegar con el PING de arranque (ver README)."""

import os
from decimal import Decimal

import pytest
from redis.asyncio import Redis

from app.infrastructure.cache import AdaptadorConCache, CacheRedis, verificar_conexion

pytestmark = pytest.mark.integration

ATRIBUTOS = {"nivel_ingresos_estimado": Decimal("1.25"), "zona_riesgo": Decimal("0.4")}


class ProveedorContado:
    def __init__(self) -> None:
        self.llamadas = 0

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        self.llamadas += 1
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


async def test_guarda_y_lee_los_atributos_con_su_ttl(redis):
    cache = CacheRedis(redis)

    await cache.guardar("perfilamiento:test:c1", ATRIBUTOS, 60)

    assert await cache.leer("perfilamiento:test:c1") == ATRIBUTOS
    assert 0 < await redis.ttl("perfilamiento:test:c1") <= 60
    assert await cache.leer("perfilamiento:test:no-existe") is None


async def test_el_segundo_pedido_sale_de_la_cache_sin_llamar_al_proveedor(redis):
    proveedor = ProveedorContado()
    adaptador = AdaptadorConCache(proveedor, CacheRedis(redis), "test", 60, 500)

    primero = await adaptador.obtener_atributos("cliente-1")
    segundo = await adaptador.obtener_atributos("cliente-1")

    assert primero == segundo == ATRIBUTOS
    assert proveedor.llamadas == 1


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
