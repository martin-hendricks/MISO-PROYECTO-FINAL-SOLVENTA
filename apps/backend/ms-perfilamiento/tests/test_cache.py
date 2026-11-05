import asyncio
from decimal import Decimal

from app.application import casos_uso
from app.infrastructure.cache import AdaptadorConCache, CacheRedis


class ProveedorContado:
    def __init__(self, atributos: dict[str, Decimal]) -> None:
        self.atributos = atributos
        self.llamadas = 0

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        self.llamadas += 1
        return dict(self.atributos)


class ProveedorQueFalla:
    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        raise RuntimeError("proveedor caído")


class CacheEnMemoria:
    def __init__(self) -> None:
        self.datos: dict[str, dict[str, Decimal]] = {}
        self.ttls: dict[str, int] = {}

    async def leer(self, clave):
        return self.datos.get(clave)

    async def guardar(self, clave, atributos, ttl_segundos):
        self.datos[clave] = dict(atributos)
        self.ttls[clave] = ttl_segundos


class CacheCaida:
    async def leer(self, clave):
        raise ConnectionError("redis caído")

    async def guardar(self, clave, atributos, ttl_segundos):
        raise ConnectionError("redis caído")


class CacheLenta:
    async def leer(self, clave):
        await asyncio.sleep(1)

    async def guardar(self, clave, atributos, ttl_segundos):
        await asyncio.sleep(1)


class RedisFalso:
    def __init__(self) -> None:
        self.valores: dict[str, str] = {}
        self.expiraciones: dict[str, int] = {}

    async def get(self, clave):
        return self.valores.get(clave)

    async def set(self, clave, valor, ex):
        self.valores[clave] = valor
        self.expiraciones[clave] = ex


ATRIBUTOS = {"zona_riesgo": Decimal("0.731"), "antiguedad_documento": Decimal("0.120")}


def _con_cache(proveedor, cache, ttl=600, timeout_ms=50):
    return AdaptadorConCache(proveedor, cache, "od", ttl, timeout_ms)


async def test_segunda_consulta_del_mismo_cliente_sale_de_la_cache_sin_llamar_al_proveedor():
    proveedor = ProveedorContado(ATRIBUTOS)
    adaptador = _con_cache(proveedor, CacheEnMemoria())

    primera = await adaptador.obtener_atributos("cliente-1")
    segunda = await adaptador.obtener_atributos("cliente-1")

    assert primera == segunda == ATRIBUTOS
    assert proveedor.llamadas == 1


async def test_la_cache_separa_clientes_y_aplica_el_ttl_configurado():
    proveedor = ProveedorContado(ATRIBUTOS)
    cache = CacheEnMemoria()
    adaptador = _con_cache(proveedor, cache, ttl=300)

    await adaptador.obtener_atributos("cliente-1")
    await adaptador.obtener_atributos("cliente-2")

    assert proveedor.llamadas == 2
    assert cache.ttls == {"perfilamiento:od:cliente-1": 300, "perfilamiento:od:cliente-2": 300}


async def test_cache_caida_no_corta_el_perfilamiento_y_consulta_al_proveedor():
    proveedor = ProveedorContado(ATRIBUTOS)
    adaptador = _con_cache(proveedor, CacheCaida())

    assert await adaptador.obtener_atributos("cliente-1") == ATRIBUTOS
    assert await adaptador.obtener_atributos("cliente-1") == ATRIBUTOS
    assert proveedor.llamadas == 2


async def test_cache_lenta_no_suma_su_demora_al_proveedor():
    proveedor = ProveedorContado(ATRIBUTOS)
    adaptador = _con_cache(proveedor, CacheLenta(), timeout_ms=10)

    resultado = await asyncio.wait_for(adaptador.obtener_atributos("cliente-1"), timeout=0.5)

    assert resultado == ATRIBUTOS


async def test_un_fallo_del_proveedor_no_queda_en_cache():
    cache = CacheEnMemoria()
    adaptador = _con_cache(ProveedorQueFalla(), cache)

    try:
        await adaptador.obtener_atributos("cliente-1")
    except RuntimeError:
        pass

    assert cache.datos == {}


async def test_cache_redis_conserva_los_decimales_y_el_ttl():
    redis = RedisFalso()
    cache = CacheRedis(redis)

    await cache.guardar("clave", ATRIBUTOS, 600)

    assert await cache.leer("clave") == ATRIBUTOS
    assert redis.expiraciones == {"clave": 600}
    assert await cache.leer("otra") is None


async def test_perfilar_con_cache_degrada_igual_si_el_proveedor_falla(uow, config, adaptador_open_finance):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    open_data = _con_cache(ProveedorQueFalla(), CacheEnMemoria())

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, adaptador_open_finance, open_data, config, "clave-cache-falla", "cliente-1"
    )

    degradados = {a.origen.value for a in resultado.oferta.snapshot_atributos if a.degradado}
    assert degradados == {"open_data"}
