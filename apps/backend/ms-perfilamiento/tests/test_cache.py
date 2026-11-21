import asyncio
import json
from decimal import Decimal

from app.infrastructure.cache import CacheRedis, verificar_conexion
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
