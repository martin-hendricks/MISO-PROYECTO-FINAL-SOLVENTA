import asyncio
from decimal import Decimal

import pytest
from prometheus_client import REGISTRY

from app.domain.modelos import CausaDegradacion
from app.infrastructure.resiliencia import (
    ABIERTO,
    CERRADO,
    SEMIABIERTO,
    AdaptadorResiliente,
    CircuitoAbierto,
    InterruptorCircuito,
)
from app.ports.adaptadores import consentimiento_en_curso
from app.ports.cache import PerfilGuardado

ATRIBUTOS = {"nivel_ingresos_estimado": Decimal("1.25"), "score_comportamiento": Decimal("0.4")}
ANTIGUOS = {"nivel_ingresos_estimado": Decimal("0.9"), "score_comportamiento": Decimal("0.3")}


def _valor(nombre: str, **etiquetas: str) -> float:
    return REGISTRY.get_sample_value(nombre, etiquetas) or 0.0


class Reloj:
    def __init__(self) -> None:
        self.ahora = 1000.0

    def __call__(self) -> float:
        return self.ahora

    def avanzar(self, segundos: float) -> None:
        self.ahora += segundos


class CacheDoble:
    def __init__(self, reloj: Reloj) -> None:
        self.reloj = reloj
        self.datos: dict[str, PerfilGuardado] = {}
        self.guardados: list[tuple[str, int, float, str | None]] = []
        self.actualizada = asyncio.Event()
        self.falla_leer = False
        self.falla_guardar = False
        self.lenta = False

    def sembrar(self, clave: str, atributos: dict[str, Decimal], edad_s: float) -> None:
        self.datos[clave] = PerfilGuardado(atributos, self.reloj() - edad_s)

    async def leer(self, clave):
        if self.lenta:
            await asyncio.Event().wait()
        if self.falla_leer:
            raise ConnectionError("redis caido")
        return self.datos.get(clave)

    async def guardar(self, clave, atributos, ttl_segundos, capturado_en, consentimiento_id=None):
        if self.lenta:
            await asyncio.Event().wait()
        if self.falla_guardar:
            raise ConnectionError("redis caido")
        self.datos[clave] = PerfilGuardado(dict(atributos), capturado_en)
        self.guardados.append((clave, ttl_segundos, capturado_en, consentimiento_id))
        self.actualizada.set()

    async def invalidar_consentimiento(self, consentimiento_id):
        return 0


class Proveedor:
    """Responde cuando se abre la puerta; `falla` hace que lance en vez de responder."""

    def __init__(self, abierta: bool = True) -> None:
        self.puerta = asyncio.Event()
        if abierta:
            self.puerta.set()
        self.iniciada = asyncio.Event()
        self.llamadas = 0
        self.falla: Exception | None = None

    async def obtener_atributos(self, cliente_id):
        self.llamadas += 1
        self.iniciada.set()
        await self.puerta.wait()
        if self.falla is not None:
            raise self.falla
        return dict(ATRIBUTOS)


def _armar(proveedor, *, presupuesto_ms=200, timeout_proveedor_ms=700, timeout_cache_ms=50, interruptor=None):
    reloj = Reloj()
    cache = CacheDoble(reloj)
    adaptador = AdaptadorResiliente(
        proveedor,
        cache,
        "of",
        ttl_suave_s=600,
        ttl_duro_s=86400,
        presupuesto_ms=presupuesto_ms,
        timeout_proveedor_ms=timeout_proveedor_ms,
        timeout_cache_ms=timeout_cache_ms,
        interruptor=interruptor or InterruptorCircuito("of", reloj=reloj),
        ahora=reloj,
    )
    return adaptador, cache, reloj


# --- circuit breaker -------------------------------------------------------------------


def _interruptor(reloj=None, **kwargs):
    reloj = reloj or Reloj()
    return InterruptorCircuito("of", ventana_s=10, umbral_tasa=0.5, min_muestras=4, apertura_s=5, reloj=reloj, **kwargs), reloj


def test_el_interruptor_abre_cuando_la_tasa_de_fallo_de_la_ventana_llega_al_umbral():
    interruptor, _ = _interruptor()
    interruptor.exito()
    interruptor.exito()
    interruptor.fallo()
    assert interruptor.estado == CERRADO
    interruptor.fallo()

    assert interruptor.estado == ABIERTO
    assert interruptor.permitir() is False


def test_el_interruptor_no_abre_con_pocas_muestras_ni_por_debajo_del_umbral():
    interruptor, _ = _interruptor()
    for _ in range(3):
        interruptor.fallo()
    assert interruptor.estado == CERRADO

    interruptor, _ = _interruptor()
    for _ in range(3):
        interruptor.exito()
    interruptor.fallo()
    assert interruptor.estado == CERRADO


def test_los_eventos_fuera_de_la_ventana_no_cuentan():
    interruptor, reloj = _interruptor()
    for _ in range(3):
        interruptor.fallo()
    reloj.avanzar(11)
    interruptor.exito()
    interruptor.exito()
    interruptor.exito()
    interruptor.fallo()

    assert interruptor.estado == CERRADO


def test_abierto_corta_hasta_cumplirse_el_tiempo_y_deja_pasar_una_sola_sonda():
    interruptor, reloj = _interruptor()
    for _ in range(4):
        interruptor.fallo()
    reloj.avanzar(4.9)
    assert interruptor.permitir() is False

    reloj.avanzar(0.2)
    assert interruptor.permitir() is True
    assert interruptor.estado == SEMIABIERTO
    assert interruptor.permitir() is False


def test_una_sonda_exitosa_cierra_y_empieza_con_la_ventana_limpia():
    interruptor, reloj = _interruptor()
    for _ in range(4):
        interruptor.fallo()
    reloj.avanzar(6)
    interruptor.permitir()

    interruptor.exito()

    assert interruptor.estado == CERRADO
    interruptor.fallo()
    interruptor.fallo()
    interruptor.fallo()
    assert interruptor.estado == CERRADO


def test_una_sonda_fallida_reabre_y_reinicia_la_espera():
    interruptor, reloj = _interruptor()
    for _ in range(4):
        interruptor.fallo()
    reloj.avanzar(6)
    interruptor.permitir()

    interruptor.fallo()

    assert interruptor.estado == ABIERTO
    reloj.avanzar(4)
    assert interruptor.permitir() is False


def test_un_exito_tardio_con_el_interruptor_abierto_no_lo_cierra():
    interruptor, _ = _interruptor()
    for _ in range(4):
        interruptor.fallo()

    interruptor.exito()

    assert interruptor.estado == ABIERTO


def test_cada_cambio_de_estado_se_cuenta():
    antes = _valor("perfilamiento_circuito_transiciones_total", fuente="of", estado="abierto")
    interruptor, _ = _interruptor()
    for _ in range(4):
        interruptor.fallo()

    assert _valor("perfilamiento_circuito_transiciones_total", fuente="of", estado="abierto") == antes + 1


# --- adaptador con cache ---------------------------------------------------------------


async def test_un_perfil_fresco_sale_de_la_cache_sin_llamar_al_proveedor():
    proveedor = Proveedor()
    adaptador, cache, _ = _armar(proveedor)
    cache.sembrar("perfilamiento:of:123", ANTIGUOS, edad_s=100)

    resuelto = await adaptador.obtener_resuelto("123")

    assert (resuelto.atributos, resuelto.origen, resuelto.causa) == (ANTIGUOS, "cache", None)
    assert resuelto.edad_segundos == 100
    assert proveedor.llamadas == 0


async def test_sin_valor_guardado_invoca_al_proveedor_y_guarda_con_la_vigencia_maxima():
    proveedor = Proveedor()
    adaptador, cache, reloj = _armar(proveedor)
    token = consentimiento_en_curso.set("consentimiento-1")
    try:
        resuelto = await adaptador.obtener_resuelto("123")
    finally:
        consentimiento_en_curso.reset(token)

    assert (resuelto.atributos, resuelto.origen) == (ATRIBUTOS, "proveedor")
    assert cache.guardados == [("perfilamiento:of:123", 86400, reloj(), "consentimiento-1")]


async def test_un_perfil_vencido_con_proveedor_rapido_se_refresca():
    proveedor = Proveedor()
    adaptador, cache, _ = _armar(proveedor)
    cache.sembrar("perfilamiento:of:123", ANTIGUOS, edad_s=700)

    resuelto = await adaptador.obtener_resuelto("123")

    assert (resuelto.atributos, resuelto.origen) == (ATRIBUTOS, "proveedor")
    assert cache.datos["perfilamiento:of:123"].atributos == ATRIBUTOS


async def test_un_perfil_vencido_con_proveedor_lento_responde_con_el_vencido_y_el_refresco_sigue():
    proveedor = Proveedor(abierta=False)
    adaptador, cache, _ = _armar(proveedor, presupuesto_ms=10)
    cache.sembrar("perfilamiento:of:123", ANTIGUOS, edad_s=700)
    antes = _valor("perfilamiento_respaldos_total", fuente="of", origen="cache_vencido")

    resuelto = await adaptador.obtener_resuelto("123")

    assert (resuelto.atributos, resuelto.origen) == (ANTIGUOS, "vencido")
    assert resuelto.causa == CausaDegradacion.TIMEOUT
    assert resuelto.edad_segundos == 700
    assert _valor("perfilamiento_respaldos_total", fuente="of", origen="cache_vencido") == antes + 1

    proveedor.puerta.set()
    await asyncio.wait_for(cache.actualizada.wait(), timeout=1)
    assert cache.datos["perfilamiento:of:123"].atributos == ATRIBUTOS


async def test_un_perfil_vencido_con_proveedor_que_falla_responde_con_el_vencido_por_fallo():
    proveedor = Proveedor()
    proveedor.falla = RuntimeError("proveedor caido")
    adaptador, cache, _ = _armar(proveedor)
    cache.sembrar("perfilamiento:of:123", ANTIGUOS, edad_s=700)

    resuelto = await adaptador.obtener_resuelto("123")

    assert (resuelto.origen, resuelto.causa) == ("vencido", CausaDegradacion.FALLO)


async def test_el_timeout_del_proveedor_cuenta_como_timeout_y_tambien_sirve_el_vencido():
    proveedor = Proveedor(abierta=False)
    adaptador, cache, _ = _armar(proveedor, presupuesto_ms=500, timeout_proveedor_ms=10)
    cache.sembrar("perfilamiento:of:123", ANTIGUOS, edad_s=700)
    antes = _valor("perfilamiento_proveedor_llamadas_total", fuente="of", resultado="timeout")

    resuelto = await adaptador.obtener_resuelto("123")

    assert (resuelto.origen, resuelto.causa) == ("vencido", CausaDegradacion.TIMEOUT)
    assert _valor("perfilamiento_proveedor_llamadas_total", fuente="of", resultado="timeout") == antes + 1


async def test_sin_valor_guardado_y_proveedor_lento_o_caido_se_propaga_para_que_el_caso_de_uso_degrade():
    lento, _ = Proveedor(abierta=False), None
    adaptador, _, _ = _armar(lento, presupuesto_ms=10)
    antes = _valor("perfilamiento_respaldos_total", fuente="of", origen="sin_valor")
    with pytest.raises(TimeoutError):
        await adaptador.obtener_resuelto("123")
    assert _valor("perfilamiento_respaldos_total", fuente="of", origen="sin_valor") == antes + 1

    caido = Proveedor()
    caido.falla = RuntimeError("proveedor caido")
    adaptador, cache, _ = _armar(caido)
    with pytest.raises(RuntimeError):
        await adaptador.obtener_resuelto("123")
    assert cache.datos == {}


async def test_con_el_interruptor_abierto_no_se_invoca_al_proveedor_y_se_sirve_el_vencido():
    proveedor = Proveedor()
    reloj = Reloj()
    interruptor = InterruptorCircuito("of", min_muestras=1, umbral_tasa=0.5, reloj=reloj)
    interruptor.fallo()
    adaptador, cache, _ = _armar(proveedor, interruptor=interruptor)
    cache.sembrar("perfilamiento:of:123", ANTIGUOS, edad_s=700)
    antes = _valor("perfilamiento_proveedor_llamadas_total", fuente="of", resultado="circuito_abierto")

    resuelto = await adaptador.obtener_resuelto("123")

    assert (resuelto.origen, resuelto.causa) == ("vencido", CausaDegradacion.FALLO)
    assert proveedor.llamadas == 0
    assert _valor("perfilamiento_proveedor_llamadas_total", fuente="of", resultado="circuito_abierto") == antes + 1

    cache.datos.clear()
    with pytest.raises(CircuitoAbierto):
        await adaptador.obtener_resuelto("999")


async def test_las_peticiones_concurrentes_por_la_misma_clave_comparten_una_invocacion():
    proveedor = Proveedor(abierta=False)
    adaptador, _, _ = _armar(proveedor, presupuesto_ms=500)
    antes = _valor("perfilamiento_coalescidas_total", fuente="of")

    tareas = [asyncio.ensure_future(adaptador.obtener_resuelto("123")) for _ in range(5)]
    # Cuando el proveedor arranca, las cinco peticiones ya pasaron por el registro de en vuelo.
    await asyncio.wait_for(proveedor.iniciada.wait(), timeout=1)
    proveedor.puerta.set()
    resultados = await asyncio.gather(*tareas)

    assert proveedor.llamadas == 1
    assert all(r.atributos == ATRIBUTOS for r in resultados)
    assert _valor("perfilamiento_coalescidas_total", fuente="of") == antes + 4


async def test_claves_distintas_no_se_coalescen():
    proveedor = Proveedor()
    adaptador, _, _ = _armar(proveedor)

    await asyncio.gather(adaptador.obtener_resuelto("1"), adaptador.obtener_resuelto("2"))

    assert proveedor.llamadas == 2


async def test_cancelar_la_invocacion_en_vuelo_cuenta_como_fallo_del_interruptor():
    proveedor = Proveedor(abierta=False)
    reloj = Reloj()
    interruptor = InterruptorCircuito("of", min_muestras=1, umbral_tasa=0.5, reloj=reloj)
    adaptador, _, _ = _armar(proveedor, presupuesto_ms=10, interruptor=interruptor)

    with pytest.raises(TimeoutError):
        await adaptador.obtener_resuelto("123")
    en_vuelo = list(adaptador._en_vuelo.values())
    assert len(en_vuelo) == 1
    en_vuelo[0].cancel()
    await asyncio.gather(*en_vuelo, return_exceptions=True)

    assert interruptor.estado == ABIERTO
    assert adaptador._en_vuelo == {}


async def test_terminar_una_tarea_que_ya_no_es_la_registrada_no_toca_la_registrada():
    adaptador, _, _ = _armar(Proveedor())
    bucle = asyncio.get_running_loop()
    registrada, ajena = bucle.create_future(), bucle.create_future()
    registrada.set_result(ATRIBUTOS)
    ajena.set_result(ATRIBUTOS)
    adaptador._en_vuelo["k"] = registrada

    adaptador._terminar("k", ajena)

    assert adaptador._en_vuelo == {"k": registrada}


async def test_obtener_atributos_devuelve_solo_los_atributos():
    adaptador, _, _ = _armar(Proveedor())

    assert await adaptador.obtener_atributos("123") == ATRIBUTOS


async def test_cache_caida_no_corta_la_respuesta_y_se_consulta_al_proveedor():
    proveedor = Proveedor()
    adaptador, cache, _ = _armar(proveedor)
    cache.falla_leer = True
    cache.falla_guardar = True
    antes = _valor("perfilamiento_cache_errores_total", fuente="of", operacion="lectura")

    resuelto = await adaptador.obtener_resuelto("123")

    assert (resuelto.atributos, resuelto.origen) == (ATRIBUTOS, "proveedor")
    assert _valor("perfilamiento_cache_errores_total", fuente="of", operacion="lectura") == antes + 1
    assert _valor("perfilamiento_cache_errores_total", fuente="of", operacion="escritura") >= 1


async def test_cache_lenta_no_suma_su_demora_a_la_respuesta():
    adaptador, cache, _ = _armar(Proveedor(), timeout_cache_ms=10)
    cache.lenta = True

    resuelto = await asyncio.wait_for(adaptador.obtener_resuelto("123"), timeout=1)

    assert resuelto.origen == "proveedor"


# --- integracion con el caso de uso ----------------------------------------------------


from app.application import casos_uso  # noqa: E402
from tests.dobles import AdaptadorConfigurable  # noqa: E402


def _modos(resultado, origen: str) -> set[tuple[str, str | None, bool]]:
    return {
        (a.modo, a.causa.value if a.causa else None, a.degradado)
        for a in resultado.oferta.snapshot_atributos
        if a.origen.value == origen
    }


async def test_el_caso_de_uso_marca_live_si_el_dato_vino_del_proveedor(uow, config, adaptador_open_data):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    adaptador, cache, _ = _armar(Proveedor())

    resultado = await casos_uso.perfilar_y_ofertar(uow, adaptador, adaptador_open_data, config, "k1", "cliente-1")

    assert _modos(resultado, "open_finance") == {("LIVE", None, False)}
    assert cache.guardados[0][3] is not None  # el consentimiento viaja a la cache compartida


async def test_el_caso_de_uso_marca_cache_si_el_perfil_fresco_salio_de_la_cache(uow, config, adaptador_open_data):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    proveedor = Proveedor()
    adaptador, cache, _ = _armar(proveedor)
    cache.sembrar("perfilamiento:of:cliente-1", ATRIBUTOS, edad_s=30)

    resultado = await casos_uso.perfilar_y_ofertar(uow, adaptador, adaptador_open_data, config, "k2", "cliente-1")

    assert _modos(resultado, "open_finance") == {("CACHE", None, False)}
    assert proveedor.llamadas == 0


async def test_el_caso_de_uso_marca_cache_con_la_causa_si_se_sirvio_un_perfil_vencido(uow, config, adaptador_open_data):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    adaptador, cache, _ = _armar(Proveedor(abierta=False), presupuesto_ms=10)
    cache.sembrar("perfilamiento:of:cliente-1", ATRIBUTOS, edad_s=900)

    resultado = await casos_uso.perfilar_y_ofertar(uow, adaptador, adaptador_open_data, config, "k3", "cliente-1")

    assert _modos(resultado, "open_finance") == {("CACHE", "timeout", False)}


async def test_sin_ningun_valor_el_caso_de_uso_degrada_al_respaldo_con_su_causa(uow, config, adaptador_open_data):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    adaptador, _, _ = _armar(Proveedor(abierta=False), presupuesto_ms=10)

    resultado = await casos_uso.perfilar_y_ofertar(uow, adaptador, adaptador_open_data, config, "k4", "cliente-1")

    assert _modos(resultado, "open_finance") == {("DEFAULT", "timeout", True)}


async def test_un_adaptador_directo_se_sigue_tratando_como_respuesta_del_proveedor(uow, config, adaptador_open_data):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    directo = AdaptadorConfigurable(ATRIBUTOS)

    resultado = await casos_uso.perfilar_y_ofertar(uow, directo, adaptador_open_data, config, "k5", "cliente-1")

    assert _modos(resultado, "open_finance") == {("LIVE", None, False)}
