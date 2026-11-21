import asyncio
import json
from decimal import Decimal

from redis.asyncio.connection import Connection, SSLConnection

from app.infrastructure.cache import CacheRedis, calentar_conexiones, crear_cliente_redis, verificar_conexion
from app.ports.cache import PerfilGuardado


class RedisFalso:
    """Lo minimo de redis.asyncio que usa CacheRedis, con los valores como bytes igual que
    el cliente real (sin decode_responses)."""

    def __init__(self) -> None:
        self.valores: dict[str, str] = {}
        self.expiraciones: dict[str, int] = {}
        self.conjuntos: dict[str, set[bytes]] = {}

    async def get(self, clave):
        return self.valores.get(clave)

    async def set(self, clave, valor, ex):
        self.valores[clave] = valor
        self.expiraciones[clave] = ex

    async def sadd(self, clave, miembro):
        self.conjuntos.setdefault(clave, set()).add(miembro.encode())

    async def expire(self, clave, segundos):
        self.expiraciones[clave] = segundos

    async def smembers(self, clave):
        return set(self.conjuntos.get(clave, set()))

    async def delete(self, *claves):
        for clave in claves:
            nombre = clave.decode() if isinstance(clave, bytes) else clave
            self.valores.pop(nombre, None)
            self.conjuntos.pop(nombre, None)


ATRIBUTOS = {"zona_riesgo": Decimal("0.731"), "antiguedad_documento": Decimal("0.120")}


async def test_guardar_conserva_los_decimales_la_fecha_y_el_ttl():
    redis = RedisFalso()
    cache = CacheRedis(redis)

    await cache.guardar("clave", ATRIBUTOS, 600, 1_700_000_000.5)

    assert await cache.leer("clave") == PerfilGuardado(ATRIBUTOS, 1_700_000_000.5)
    assert redis.expiraciones == {"clave": 600}
    assert redis.conjuntos == {}
    assert await cache.leer("otra") is None


async def test_guardar_bajo_un_consentimiento_anota_la_clave_en_su_indice_con_el_mismo_ttl():
    redis = RedisFalso()
    cache = CacheRedis(redis)

    await cache.guardar("perfilamiento:of:123", ATRIBUTOS, 86400, 10.0, "consentimiento-1")

    assert redis.conjuntos == {"perfilamiento:consentimiento:consentimiento-1": {b"perfilamiento:of:123"}}
    assert redis.expiraciones["perfilamiento:consentimiento:consentimiento-1"] == 86400


async def test_invalidar_el_consentimiento_borra_sus_entradas_y_el_indice_sin_tocar_las_de_otro():
    redis = RedisFalso()
    cache = CacheRedis(redis)
    await cache.guardar("perfilamiento:of:123", ATRIBUTOS, 600, 1.0, "consentimiento-1")
    await cache.guardar("perfilamiento:od:123", ATRIBUTOS, 600, 1.0, "consentimiento-1")
    await cache.guardar("perfilamiento:of:999", ATRIBUTOS, 600, 1.0, "consentimiento-2")

    borradas = await cache.invalidar_consentimiento("consentimiento-1")

    assert borradas == 2
    assert await cache.leer("perfilamiento:of:123") is None
    assert await cache.leer("perfilamiento:od:123") is None
    assert await cache.leer("perfilamiento:of:999") is not None
    assert "perfilamiento:consentimiento:consentimiento-1" not in redis.conjuntos


async def test_invalidar_un_consentimiento_sin_entradas_no_falla():
    assert await CacheRedis(RedisFalso()).invalidar_consentimiento("desconocido") == 0


async def test_una_entrada_con_el_formato_anterior_no_se_interpreta():
    redis = RedisFalso()
    redis.valores["vieja"] = json.dumps({"zona_riesgo": "0.5"})

    try:
        await CacheRedis(redis).leer("vieja")
    except KeyError:
        pass
    else:
        raise AssertionError("debia rechazar el formato sin fecha de captura")


async def test_verificar_conexion_responde_true_si_el_ping_funciona():
    class Vivo:
        async def ping(self):
            return True

    assert await verificar_conexion(Vivo(), 100) is True


async def test_verificar_conexion_responde_false_si_el_ping_falla_o_se_agota():
    class Caido:
        async def ping(self):
            raise ConnectionError("rechazada")

    class Lento:
        async def ping(self):
            await asyncio.Event().wait()

    assert await verificar_conexion(Caido(), 100) is False
    assert await verificar_conexion(Lento(), 1) is False


class PoolDoble:
    """Pool que reparte conexiones distintas y recuerda cuantas siguen en uso."""

    def __init__(self, fallan_desde: int | None = None) -> None:
        self.tomadas = 0
        self.liberadas: list[object] = []
        self._fallan_desde = fallan_desde

    async def get_connection(self):
        self.tomadas += 1
        if self._fallan_desde is not None and self.tomadas >= self._fallan_desde:
            raise ConnectionError("rechazada")
        return object()

    async def release(self, conexion):
        self.liberadas.append(conexion)


class ClienteDoble:
    def __init__(self, pool: PoolDoble) -> None:
        self.connection_pool = pool


async def test_calentar_conexiones_toma_n_distintas_del_pool_y_las_devuelve_todas():
    pool = PoolDoble()

    assert await calentar_conexiones(ClienteDoble(pool), 5, 1000) == 5
    assert pool.tomadas == 5
    assert len({id(c) for c in pool.liberadas}) == 5  # cinco conexiones distintas, todas devueltas


async def test_calentar_conexiones_cuenta_las_que_abrio_y_avisa_de_las_que_no(caplog):
    pool = PoolDoble(fallan_desde=4)

    with caplog.at_level("WARNING"):
        abiertas = await calentar_conexiones(ClienteDoble(pool), 5, 1000)

    assert abiertas == 3
    assert len(pool.liberadas) == 3
    assert "solo se abrieron 3 de 5 conexiones" in caplog.text


async def test_calentar_conexiones_no_espera_mas_que_el_timeout():
    class PoolLento(PoolDoble):
        async def get_connection(self):
            await asyncio.Event().wait()

    assert await calentar_conexiones(ClienteDoble(PoolLento()), 2, 1) == 0


async def test_calentar_cero_conexiones_no_toca_el_pool():
    pool = PoolDoble()

    assert await calentar_conexiones(ClienteDoble(pool), 0, 1000) == 0
    assert pool.tomadas == 0


async def test_el_cliente_sin_tls_usa_un_pool_acotado_con_keepalive_y_verificacion():
    cliente = crear_cliente_redis("cache", 6379, None, False, 16, 30)
    pool = cliente.connection_pool

    assert pool.connection_class is Connection
    assert pool.max_connections == 16
    assert pool.connection_kwargs["socket_keepalive"] is True
    assert pool.connection_kwargs["health_check_interval"] == 30
    assert pool.connection_kwargs["password"] is None
    await cliente.aclose(close_connection_pool=True)


async def test_el_cliente_pasa_el_token_y_cierra_su_pool_al_cerrarse():
    cliente = crear_cliente_redis("cache", 6379, "token", False, 4, 30)
    pool = cliente.connection_pool

    assert pool.connection_kwargs["password"] == "token"
    await cliente.aclose(close_connection_pool=True)
    assert pool._in_use_connections == set() and pool._available_connections == []


async def test_las_conexiones_tls_de_un_mismo_pool_comparten_el_contexto_ssl():
    pool = crear_cliente_redis("cache", 6379, "token", True, 4, 30).connection_pool
    primera, segunda = pool.make_connection(), pool.make_connection()

    assert issubclass(pool.connection_class, SSLConnection)
    assert primera.ssl_context is segunda.ssl_context


async def test_dos_clientes_tls_no_comparten_el_contexto():
    uno = crear_cliente_redis("cache", 6379, None, True, 4, 30).connection_pool.make_connection()
    otro = crear_cliente_redis("cache", 6379, None, True, 4, 30).connection_pool.make_connection()

    assert uno.ssl_context is not otro.ssl_context


async def test_las_opciones_tls_llegan_al_contexto_compartido():
    pool = crear_cliente_redis("cache", 6379, None, True, 4, 30, ssl_cert_reqs="none").connection_pool

    assert pool.make_connection().ssl_context.cert_reqs.name == "CERT_NONE"

