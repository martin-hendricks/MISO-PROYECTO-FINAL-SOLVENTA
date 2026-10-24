from uuid import UUID, uuid4

import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import EstadoPoliza, Poliza

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


async def test_consultar_poliza_por_numero(uow, suscripciones, cobros):
    emision = await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud())

    encontrada = await casos_uso.consultar_poliza_por_numero(uow, emision.poliza.numero)

    assert encontrada.id == emision.poliza.id


async def test_consultar_poliza_por_numero_inexistente(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_poliza_por_numero(uow, "POL-2026-99999999")


async def test_listar_polizas_de_usuario_ordena_por_inicio_de_vigencia_descendente(uow, suscripciones, cobros):
    usuario_id = uuid4()
    primera = await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud_de(usuario_id))
    segunda = await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud_de(usuario_id))

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


async def test_listar_polizas_de_usuario_respeta_el_limite(uow, suscripciones, cobros):
    usuario_id = uuid4()
    for _ in range(3):
        await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud_de(usuario_id))

    listado = await casos_uso.listar_polizas_de_usuario(uow, usuario_id, limite=2)

    assert len(listado) == 2


async def test_listar_polizas_de_usuario_sin_polizas_devuelve_vacio(uow):
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
