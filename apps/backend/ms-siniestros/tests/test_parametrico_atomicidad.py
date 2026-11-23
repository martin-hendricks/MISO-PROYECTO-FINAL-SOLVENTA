"""Atomicidad de la cadena paramétrica y desembolso después del commit.

Cada prueba cubre un defecto concreto de la versión anterior, que confirmaba hasta
siete transacciones por evento y desembolsaba antes del commit:

- una falla a mitad de la cadena dejaba el siniestro en EN_EVALUACION sin evaluación,
  y cada reingesta respondía 500 para siempre;
- se desembolsaba antes del commit, así que una transacción que luego fallaba dejaba
  un desembolso sin pago registrado.

Los adaptadores de estas pruebas cuentan TODAS las llamadas: el stub productivo es
idempotente y escondería una doble llamada. La carrera concurrente real (varias
entregas mientras el ganador está en ENRUTADO) se prueba contra PostgreSQL en
test_repositorio_sql.py.
"""

from decimal import Decimal

import pytest

from app.application import casos_uso
from app.domain.modelos import EstadoSiniestro

from .dobles import _RepoEventosParametricos


class AdaptadorQueCuenta:
    def __init__(self, fallos: int = 0) -> None:
        self.llamadas: list[tuple[str, Decimal]] = []
        self._fallos = fallos

    async def desembolsar(self, evento_id: str, monto: Decimal) -> None:
        self.llamadas.append((evento_id, monto))
        if self._fallos > 0:
            self._fallos -= 1
            raise ConnectionError("pasarela caída")


async def _ingerir(uow, adaptador, evento_id="evt-1", valor="100"):
    return await casos_uso.recibir_evento_parametrico(
        uow, adaptador, evento_id, Decimal(valor), Decimal("80"), True, Decimal("500.00")
    )


def _siniestro_de(almacen, evento_id):
    return next(s for s in almacen.siniestros.values() if s.evento_id == evento_id)


async def test_falla_a_mitad_de_la_cadena_no_persiste_nada(uow, almacen, monkeypatch):
    adaptador = AdaptadorQueCuenta()

    async def evaluacion_rota(*_args, **_kwargs):
        raise RuntimeError("caída en plena evaluación")

    monkeypatch.setattr(casos_uso, "_evaluar", evaluacion_rota)
    with pytest.raises(RuntimeError):
        await _ingerir(uow, adaptador)

    assert almacen.eventos_parametricos == {}
    assert almacen.siniestros == {}
    assert almacen.evaluaciones == {}
    assert almacen.eventos == []  # tampoco quedan eventos de outbox huérfanos
    assert adaptador.llamadas == []


async def test_tras_una_falla_la_reingesta_procesa_desde_cero_y_paga_una_vez(uow, almacen, monkeypatch):
    adaptador = AdaptadorQueCuenta()

    async def evaluacion_rota(*_args, **_kwargs):
        raise RuntimeError("caída en plena evaluación")

    monkeypatch.setattr(casos_uso, "_evaluar", evaluacion_rota)
    with pytest.raises(RuntimeError):
        await _ingerir(uow, adaptador)
    monkeypatch.undo()

    resultado = await _ingerir(uow, adaptador)

    assert resultado.procesado is True
    assert resultado.siniestro.estado is EstadoSiniestro.PAGADO
    assert adaptador.llamadas == [("evt-1", Decimal("500.00"))]
    assert len(almacen.pagos) == 1


async def test_entrega_que_llega_tras_el_pago_lee_al_ganador_sin_desembolsar(uow, almacen, monkeypatch):
    adaptador = AdaptadorQueCuenta()
    ganador = await _ingerir(uow, adaptador)

    # La segunda entrega no ve al ganador en la lectura previa (llegó a la vez) y
    # choca recién al escribir, como pasa con dos réplicas concurrentes.
    original = _RepoEventosParametricos.obtener_por_clave
    vistas = {"n": 0}

    async def ciega_la_primera_vez(self, evento_id):
        vistas["n"] += 1
        return None if vistas["n"] == 1 else await original(self, evento_id)

    monkeypatch.setattr(_RepoEventosParametricos, "obtener_por_clave", ciega_la_primera_vez)
    perdedor = await _ingerir(uow, adaptador)

    assert perdedor.procesado is False
    assert perdedor.pago.id == ganador.pago.id
    assert adaptador.llamadas == [("evt-1", Decimal("500.00"))]  # solo el ganador, ya en PAGADO
    assert len(almacen.pagos) == 1
    assert len(almacen.siniestros) == 1


async def test_si_el_desembolso_falla_el_siniestro_queda_enrutado_con_el_pago(uow, almacen):
    adaptador = AdaptadorQueCuenta(fallos=1)

    with pytest.raises(ConnectionError):
        await _ingerir(uow, adaptador)

    siniestro = _siniestro_de(almacen, "evt-1")
    assert siniestro.estado is EstadoSiniestro.ENRUTADO
    assert "evt-1" in almacen.pagos
    assert "evt-1" in almacen.evaluaciones


async def test_la_reingesta_completa_un_pago_que_quedo_a_medias(uow, almacen):
    adaptador = AdaptadorQueCuenta(fallos=1)
    with pytest.raises(ConnectionError):
        await _ingerir(uow, adaptador)

    resultado = await _ingerir(uow, adaptador)

    assert resultado.procesado is False
    assert resultado.siniestro.estado is EstadoSiniestro.PAGADO
    assert _siniestro_de(almacen, "evt-1").estado is EstadoSiniestro.PAGADO
    # Un intento fallido y uno exitoso: el pago se completó, no se duplicó.
    assert adaptador.llamadas == [("evt-1", Decimal("500.00"))] * 2
    assert len(almacen.pagos) == 1


async def test_reingesta_de_un_evento_ya_pagado_no_vuelve_a_desembolsar(uow, almacen):
    adaptador = AdaptadorQueCuenta()
    await _ingerir(uow, adaptador)

    await _ingerir(uow, adaptador)

    assert adaptador.llamadas == [("evt-1", Decimal("500.00"))]


async def test_umbral_no_cumplido_queda_decidido_en_una_sola_transaccion(uow, almacen):
    adaptador = AdaptadorQueCuenta()

    resultado = await _ingerir(uow, adaptador, valor="10")

    assert resultado.siniestro.estado is EstadoSiniestro.DECIDIDO
    estados = [t.estado for t in _siniestro_de(almacen, "evt-1").historial]
    assert estados == [EstadoSiniestro.RECIBIDO, EstadoSiniestro.EN_EVALUACION, EstadoSiniestro.DECIDIDO]
    assert adaptador.llamadas == []


async def test_el_origen_de_la_ingesta_queda_en_la_traza(uow, almacen):
    await casos_uso.recibir_evento_parametrico(
        uow,
        AdaptadorQueCuenta(),
        "evt-t",
        Decimal("100"),
        Decimal("80"),
        True,
        Decimal("500.00"),
        origen=casos_uso.ORIGEN_TOPICO_TELEMETRIA,
    )

    assert _siniestro_de(almacen, "evt-t").historial[0].origen == "topico-telemetria"
