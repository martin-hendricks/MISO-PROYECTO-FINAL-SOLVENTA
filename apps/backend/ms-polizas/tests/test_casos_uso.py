from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import Cobertura, EstadoPoliza, Poliza

from .dobles import FirmaFalsa, coberturas, solicitud


async def test_emision_tras_cobro_exitoso(uow, almacen, suscripciones, cobros, firma):
    # Dado una suscripción aceptada con el cobro de prima exitoso
    pedido = solicitud()

    # Cuando el núcleo emite la póliza
    emision = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)

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


async def test_reintento_no_duplica_la_poliza(uow, almacen, suscripciones, cobros, firma):
    # Dado una póliza ya emitida para esa oferta aceptada
    pedido = solicitud()
    primera = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)

    # Cuando se reintenta la emisión
    segunda = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)

    # Entonces no se genera una segunda póliza ni un nuevo número
    assert not segunda.creada
    assert len(almacen.polizas) == 1
    assert almacen.secuencia == 1
    assert len(almacen.eventos) == 1
    # Y se devuelve la póliza existente
    assert (segunda.poliza.id, segunda.poliza.numero) == (primera.poliza.id, primera.poliza.numero)


async def test_ofertas_distintas_reciben_numeros_distintos(uow, suscripciones, cobros, firma):
    primera = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud())
    segunda = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud())

    assert primera.poliza.numero != segunda.poliza.numero


async def test_sin_suscripcion_aceptada_no_se_emite(uow, almacen, suscripciones, cobros, firma):
    suscripciones.respuesta = False

    with pytest.raises(ReglaDeNegocioViolada) as error:
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud())

    assert error.value.codigo == "suscripcion_no_aceptada"
    assert almacen.polizas == {} and almacen.secuencia == 0


async def test_sin_cobro_exitoso_no_se_emite(uow, almacen, suscripciones, cobros, firma):
    cobros.respuesta = False

    with pytest.raises(ReglaDeNegocioViolada) as error:
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud())

    assert error.value.codigo == "cobro_no_exitoso"
    assert almacen.polizas == {} and almacen.secuencia == 0


async def test_emision_concurrente_devuelve_la_poliza_ganadora(uow, almacen, suscripciones, cobros, firma):
    pedido = solicitud()
    ganadora = Poliza.emitir(pedido.oferta_id, pedido.usuario_id, "POL-2026-00000099", coberturas(), pedido_hoy())
    almacen.chocar_en_proximo_commit = ganadora

    emision = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)

    assert not emision.creada
    assert emision.poliza.numero == "POL-2026-00000099"
    assert almacen.eventos == []


async def test_choque_sin_ganadora_visible_falla(uow, almacen, suscripciones, cobros, firma):
    almacen.chocar_en_proximo_commit = Poliza.emitir(uuid4(), uuid4(), "POL-X", coberturas(), pedido_hoy())

    with pytest.raises(RuntimeError, match="sin póliza visible"):
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud())


async def test_consultar_poliza_inexistente(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_poliza(uow, uuid4())


async def test_consultar_poliza_por_numero(uow, suscripciones, cobros, firma):
    emision = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud())

    encontrada = await casos_uso.consultar_poliza_por_numero(uow, emision.poliza.numero)

    assert encontrada.id == emision.poliza.id


async def test_consultar_poliza_por_numero_inexistente(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_poliza_por_numero(uow, "POL-2026-99999999")


async def test_listar_polizas_de_usuario_ordena_por_inicio_de_vigencia_descendente(uow, suscripciones, cobros, firma):
    usuario_id = uuid4()
    primera = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud_de(usuario_id))
    segunda = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud_de(usuario_id))

    # Ambas pólizas se emiten "hoy": fuerzo que la primera quede con una
    # vigencia anterior para verificar el orden descendente sin depender del
    # reloj real.
    async with uow() as tx:
        vieja = await tx.polizas.obtener(primera.poliza.id)
    vieja.inicio_vigencia = vieja.inicio_vigencia.replace(year=vieja.inicio_vigencia.year - 1)
    async with uow() as tx:
        tx.pendientes[vieja.id] = vieja
        await tx.confirmar()

    listado = await casos_uso.listar_polizas_de_usuario(uow, usuario_id, limite=10)

    assert [p.id for p in listado] == [segunda.poliza.id, primera.poliza.id]


async def test_listar_polizas_de_usuario_respeta_el_limite(uow, suscripciones, cobros, firma):
    usuario_id = uuid4()
    for _ in range(3):
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud_de(usuario_id))

    listado = await casos_uso.listar_polizas_de_usuario(uow, usuario_id, limite=2)

    assert len(listado) == 2


async def test_listar_polizas_de_usuario_sin_polizas_devuelve_vacio(uow, firma):
    assert await casos_uso.listar_polizas_de_usuario(uow, uuid4(), limite=10) == []


def solicitud_de(usuario_id: UUID):
    pedido = solicitud()
    return casos_uso.SolicitudEmision(
        solicitud_id=pedido.solicitud_id,
        oferta_id=pedido.oferta_id,
        usuario_id=usuario_id,
        token_pago_confirmado=pedido.token_pago_confirmado,
        coberturas=pedido.coberturas,
    )


def pedido_hoy():
    return casos_uso._hoy()


async def _emitida(uow, suscripciones, cobros) -> Poliza:
    emision = await casos_uso.emitir_poliza(uow, suscripciones, cobros, FirmaFalsa(), solicitud())
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


async def test_firma_exitosa_persiste_constancia_y_emite_la_poliza(uow, almacen, suscripciones, cobros, firma):
    # Dado una suscripción aceptada en proceso de emisión
    pedido = solicitud()

    # Cuando el stub de firma responde ok
    emision = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)

    # Entonces la constancia queda persistida con su marca de tiempo
    [constancia] = almacen.constancias
    assert constancia.oferta_id == pedido.oferta_id
    assert constancia.exitosa and constancia.motivo is None
    assert constancia.firmada_en.tzinfo is not None
    # Y el flujo continúa hacia la emisión de la póliza, que lleva el hash de la firma
    assert emision.creada
    assert emision.poliza.firma_hash == constancia.firma_hash == f"hash-{pedido.oferta_id}"
    assert [e.tipo for e in almacen.eventos] == ["PolizaEmitida"]


async def test_firma_no_exitosa_no_emite_y_deja_el_motivo(uow, almacen, suscripciones, cobros, firma):
    # Dado una suscripción aceptada en proceso de emisión
    firma.exitosa = False
    pedido = solicitud()

    # Cuando el stub de firma responde no
    with pytest.raises(ReglaDeNegocioViolada) as error:
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)

    # Entonces no se emite póliza
    assert error.value.codigo == "firma_no_exitosa"
    assert almacen.polizas == {} and almacen.secuencia == 0 and almacen.eventos == []
    # Y el estado refleja el motivo de la firma fallida
    assert "Firma rechazada por el firmante" in error.value.mensaje
    [constancia] = almacen.constancias
    assert not constancia.exitosa and constancia.motivo == "Firma rechazada por el firmante"
    assert constancia.firma_hash is None


async def test_sin_cobro_exitoso_no_se_firma(uow, almacen, suscripciones, cobros, firma):
    cobros.respuesta = False

    with pytest.raises(ReglaDeNegocioViolada):
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud())

    assert firma.firmadas == [] and almacen.constancias == []


async def test_reintento_de_emision_no_vuelve_a_firmar(uow, almacen, suscripciones, cobros, firma):
    pedido = solicitud()
    await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)

    await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)

    assert firma.firmadas == [pedido.oferta_id]
    assert len(almacen.constancias) == 1


async def test_consultar_firma_devuelve_la_ultima_constancia_de_la_oferta(uow, suscripciones, cobros, firma):
    pedido = solicitud()
    firma.exitosa = False
    with pytest.raises(ReglaDeNegocioViolada):
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)
    firma.exitosa = True
    await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, pedido)

    constancia = await casos_uso.consultar_firma(uow, pedido.oferta_id)

    assert constancia.exitosa


async def test_consultar_firma_sin_constancia(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_firma(uow, uuid4())
