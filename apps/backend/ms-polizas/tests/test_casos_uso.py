from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import Cobertura, EstadoPoliza, Poliza

from .dobles import coberturas, solicitud


async def test_emision_tras_cobro_exitoso(uow, almacen, suscripciones, cobros):
    # Dado una suscripción aceptada con el cobro de prima exitoso
    pedido = solicitud()

    # Cuando el núcleo emite la póliza
    emision = await casos_uso.emitir_poliza(uow, suscripciones, cobros, pedido)

    # Entonces la póliza tiene número único, vigencia, coberturas y estado vigente
    poliza = emision.poliza
    assert emision.creada
    assert poliza.numero.startswith("POL-") and poliza.numero.endswith("00000001")
    assert poliza.fin_vigencia > poliza.inicio_vigencia
    assert len(poliza.coberturas) == 2
    assert poliza.estado is EstadoPoliza.VIGENTE
    assert suscripciones.consultas == [pedido.solicitud_id]
    assert [e.tipo for e in almacen.eventos] == ["PolizaEmitida"]
    # Y queda consultable de inmediato por el cliente
    assert (await casos_uso.consultar_poliza(uow, poliza.id)).numero == poliza.numero


async def test_reintento_no_duplica_la_poliza(uow, almacen, suscripciones, cobros):
    # Dado una póliza ya emitida para esa oferta aceptada
    pedido = solicitud()
    primera = await casos_uso.emitir_poliza(uow, suscripciones, cobros, pedido)

    # Cuando se reintenta la emisión
    segunda = await casos_uso.emitir_poliza(uow, suscripciones, cobros, pedido)

    # Entonces no se genera una segunda póliza ni un nuevo número
    assert not segunda.creada
    assert len(almacen.polizas) == 1
    assert almacen.secuencia == 1
    assert len(almacen.eventos) == 1
    # Y se devuelve la póliza existente
    assert (segunda.poliza.id, segunda.poliza.numero) == (primera.poliza.id, primera.poliza.numero)


async def test_ofertas_distintas_reciben_numeros_distintos(uow, suscripciones, cobros):
    primera = await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud())
    segunda = await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud())

    assert primera.poliza.numero != segunda.poliza.numero


async def test_sin_suscripcion_aceptada_no_se_emite(uow, almacen, suscripciones, cobros):
    suscripciones.respuesta = False

    with pytest.raises(ReglaDeNegocioViolada) as error:
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud())

    assert error.value.codigo == "suscripcion_no_aceptada"
    assert almacen.polizas == {} and almacen.secuencia == 0


async def test_sin_cobro_exitoso_no_se_emite(uow, almacen, suscripciones, cobros):
    cobros.respuesta = False

    with pytest.raises(ReglaDeNegocioViolada) as error:
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud())

    assert error.value.codigo == "cobro_no_exitoso"
    assert almacen.polizas == {} and almacen.secuencia == 0


async def test_emision_concurrente_devuelve_la_poliza_ganadora(uow, almacen, suscripciones, cobros):
    pedido = solicitud()
    ganadora = Poliza.emitir(pedido.oferta_id, pedido.usuario_id, "POL-2026-00000099", coberturas(), pedido_hoy())
    almacen.chocar_en_proximo_commit = ganadora

    emision = await casos_uso.emitir_poliza(uow, suscripciones, cobros, pedido)

    assert not emision.creada
    assert emision.poliza.numero == "POL-2026-00000099"
    assert almacen.eventos == []


async def test_choque_sin_ganadora_visible_falla(uow, almacen, suscripciones, cobros):
    almacen.chocar_en_proximo_commit = Poliza.emitir(uuid4(), uuid4(), "POL-X", coberturas(), pedido_hoy())

    with pytest.raises(RuntimeError, match="sin póliza visible"):
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud())


async def test_consultar_poliza_inexistente(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_poliza(uow, uuid4())


def pedido_hoy():
    return casos_uso._hoy()


async def _emitida(uow, suscripciones, cobros) -> Poliza:
    emision = await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud())
    return emision.poliza


# --- renovar_poliza (HU-59) ------------------------------------------------


async def test_renovar_poliza_extiende_la_vigencia_y_publica_evento(uow, almacen, suscripciones, cobros):
    poliza = await _emitida(uow, suscripciones, cobros)
    nueva_fecha = date(poliza.fin_vigencia.year + 1, poliza.fin_vigencia.month, poliza.fin_vigencia.day)

    renovada = await casos_uso.renovar_poliza(uow, poliza.id, nueva_fecha)

    assert renovada.fin_vigencia == nueva_fecha
    assert renovada.estado is EstadoPoliza.VIGENTE
    assert [e.tipo for e in almacen.eventos][-1] == "PolizaRenovada"
    # Y el cambio quedó persistido, no solo en el objeto devuelto.
    consultada = await casos_uso.consultar_poliza(uow, poliza.id)
    assert consultada.fin_vigencia == nueva_fecha


async def test_renovar_poliza_inexistente_lanza_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.renovar_poliza(uow, uuid4(), date(2030, 1, 1))


async def test_renovar_poliza_cancelada_lanza_transicion_invalida(uow, suscripciones, cobros):
    poliza = await _emitida(uow, suscripciones, cobros)
    await casos_uso.cancelar_poliza(uow, poliza.id, "El cliente lo pidió")

    with pytest.raises(TransicionInvalida):
        await casos_uso.renovar_poliza(uow, poliza.id, date(2030, 1, 1))


# --- modificar_poliza (HU-60) ----------------------------------------------


async def test_modificar_poliza_reemplaza_coberturas_y_publica_evento(uow, almacen, suscripciones, cobros):
    poliza = await _emitida(uow, suscripciones, cobros)
    nuevas = [Cobertura(nombre="Robo", suma_asegurada=Decimal("1000"), deducible=Decimal("0"))]

    modificada = await casos_uso.modificar_poliza(uow, poliza.id, nuevas)

    assert [c.nombre for c in modificada.coberturas] == ["Robo"]
    assert [e.tipo for e in almacen.eventos][-1] == "PolizaModificada"
    consultada = await casos_uso.consultar_poliza(uow, poliza.id)
    assert [c.nombre for c in consultada.coberturas] == ["Robo"]


async def test_modificar_poliza_inexistente_lanza_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.modificar_poliza(uow, uuid4(), coberturas())


async def test_modificar_poliza_cancelada_lanza_transicion_invalida(uow, suscripciones, cobros):
    poliza = await _emitida(uow, suscripciones, cobros)
    await casos_uso.cancelar_poliza(uow, poliza.id, "El cliente lo pidió")

    with pytest.raises(TransicionInvalida):
        await casos_uso.modificar_poliza(uow, poliza.id, coberturas())


async def test_modificar_poliza_con_coberturas_invalidas_lanza_regla_de_negocio(uow, suscripciones, cobros):
    poliza = await _emitida(uow, suscripciones, cobros)

    with pytest.raises(ReglaDeNegocioViolada) as error:
        await casos_uso.modificar_poliza(uow, poliza.id, [])

    assert error.value.codigo == "sin_coberturas"


# --- cancelar_poliza (HU-61) ------------------------------------------------


async def test_cancelar_poliza_cambia_estado_y_publica_evento(uow, almacen, suscripciones, cobros):
    poliza = await _emitida(uow, suscripciones, cobros)

    cancelada = await casos_uso.cancelar_poliza(uow, poliza.id, "El cliente lo pidió")

    assert cancelada.estado is EstadoPoliza.CANCELADA
    assert cancelada.motivo_cancelacion == "El cliente lo pidió"
    assert [e.tipo for e in almacen.eventos][-1] == "PolizaCancelada"
    consultada = await casos_uso.consultar_poliza(uow, poliza.id)
    assert consultada.estado is EstadoPoliza.CANCELADA


async def test_cancelar_poliza_inexistente_lanza_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.cancelar_poliza(uow, uuid4(), "motivo")


async def test_cancelar_poliza_dos_veces_lanza_transicion_invalida(uow, suscripciones, cobros):
    poliza = await _emitida(uow, suscripciones, cobros)
    await casos_uso.cancelar_poliza(uow, poliza.id, "El cliente lo pidió")

    with pytest.raises(TransicionInvalida):
        await casos_uso.cancelar_poliza(uow, poliza.id, "Otro motivo")
