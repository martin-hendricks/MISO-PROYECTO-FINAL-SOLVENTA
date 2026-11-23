from uuid import uuid4

import pytest

from app.application.manejadores import (
    TIPOS_SOPORTADOS,
    construir_contenido,
    manejar_evento,
)
from app.domain.eventos import EventoBus
from app.domain.modelos import DispositivoPush
from app.infrastructure.push_stub import PushStub
from tests.dobles import PushDoble


def _evento(tipo="PolizaEmitida", payload=None, evento_id=None):
    datos = {
        "evento_id": str(evento_id or uuid4()),
        "tipo": tipo,
        "agregado_id": str(uuid4()),
        "ocurrido_en": "2026-11-06T12:00:00+00:00",
        "origen": "ms_polizas",
        "payload": payload if payload is not None else {},
    }
    return EventoBus.desde_mensaje(datos)


def _payload(usuario_id=None, **extras):
    datos = {"usuario_id": str(usuario_id or uuid4())}
    datos.update(extras)
    return datos


def _sembrar_dispositivo(almacen, usuario_id):
    dispositivo = DispositivoPush.registrar(usuario_id, "android", "token-1")
    almacen.dispositivos[dispositivo.dispositivo_id] = dispositivo
    return dispositivo


def test_tipos_soportados_son_los_cuatro_del_contrato():
    assert TIPOS_SOPORTADOS == frozenset(
        {"PolizaEmitida", "PolizaRenovada", "PolizaModificada", "PolizaCancelada"}
    )


@pytest.mark.parametrize(
    ("tipo", "payload", "esperado"),
    [
        (
            "PolizaEmitida",
            {"numero": "POL-1", "fin_vigencia": "2027-01-01"},
            (
                "poliza_emitida",
                "Tu póliza fue emitida",
                "La póliza POL-1 está vigente hasta 2027-01-01.",
                "poliza-detalle",
            ),
        ),
        (
            "PolizaRenovada",
            {"numero": "POL-1", "fin_vigencia": "2028-01-01"},
            (
                "poliza_renovada",
                "Tu póliza fue renovada",
                "La póliza POL-1 ahora vence el 2028-01-01.",
                "poliza-detalle",
            ),
        ),
        (
            "PolizaModificada",
            {"numero": "POL-1"},
            (
                "poliza_modificada",
                "Actualizamos tus coberturas",
                "La póliza POL-1 tiene nuevas coberturas.",
                "poliza-detalle",
            ),
        ),
        (
            "PolizaCancelada",
            {"numero": "POL-1"},
            (
                "poliza_cancelada",
                "Tu póliza fue cancelada",
                "La póliza POL-1 fue cancelada.",
                "poliza-detalle",
            ),
        ),
        (
            "PolizaCancelada",
            {"numero": "POL-1", "devolucion_estimada": "COP 120.000"},
            (
                "poliza_cancelada",
                "Tu póliza fue cancelada",
                "La póliza POL-1 fue cancelada. Devolución estimada: COP 120.000.",
                "poliza-detalle",
            ),
        ),
    ],
)
def test_construir_contenido_mapea_cada_tipo(tipo, payload, esperado):
    contenido = construir_contenido(_evento(tipo, _payload(**payload)))

    assert contenido is not None
    assert (contenido.tipo, contenido.titulo, contenido.cuerpo, contenido.destino) == esperado


def test_construir_contenido_omite_numero_cuando_falta():
    contenido = construir_contenido(
        _evento("PolizaEmitida", _payload(fin_vigencia="2027-01-01"))
    )

    assert contenido is not None
    assert contenido.cuerpo == "Tu póliza está vigente hasta 2027-01-01."
    assert contenido.destino == "inicio"
    assert contenido.poliza is None
    assert "None" not in contenido.cuerpo


def test_construir_contenido_devuelve_none_si_falta_usuario_o_el_tipo_no_se_soporta():
    assert construir_contenido(_evento("PolizaEmitida", {"numero": "POL-1"})) is None
    assert construir_contenido(_evento("SiniestroActualizado", _payload())) is None


async def test_manejar_evento_crea_notificacion_y_despacha_push(uow, almacen, push):
    usuario = uuid4()
    dispositivo = _sembrar_dispositivo(almacen, usuario)
    evento = _evento("PolizaEmitida", _payload(usuario, numero="POL-7", fin_vigencia="2027-01-01"))

    notificacion = await manejar_evento(uow, push, evento)

    assert notificacion is not None
    assert notificacion.usuario_id == usuario
    assert notificacion.evento_origen_id == evento.evento_id
    assert notificacion.canal == "push"
    assert notificacion.tipo == "poliza_emitida"
    assert notificacion.estado == "enviada"
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "enviada"
    assert push.llamadas == [([dispositivo.dispositivo_id], notificacion.notificacion_id)]


async def test_manejar_evento_es_idempotente_por_evento_id(uow, almacen, push):
    usuario = uuid4()
    _sembrar_dispositivo(almacen, usuario)
    evento_id = uuid4()
    evento = _evento("PolizaRenovada", _payload(usuario, numero="POL-9"), evento_id=evento_id)

    primera = await manejar_evento(uow, push, evento)
    segunda = await manejar_evento(uow, push, evento)

    assert primera is not None and segunda is not None
    assert primera.notificacion_id == segunda.notificacion_id
    assert len(almacen.notificaciones) == 1
    assert len(push.llamadas) == 1


async def test_manejar_evento_de_tipo_desconocido_no_crea_nada(uow, almacen, push):
    evento = _evento("SiniestroActualizado", _payload())

    assert await manejar_evento(uow, push, evento) is None
    assert almacen.notificaciones == {}
    assert push.llamadas == []


@pytest.mark.parametrize("usuario_id", [None, "no-es-uuid", 123])
async def test_manejar_evento_con_usuario_invalido_no_crea_nada(uow, almacen, push, usuario_id):
    payload = {"numero": "POL-1"} if usuario_id is None else {"usuario_id": usuario_id, "numero": "POL-1"}
    evento = _evento("PolizaEmitida", payload)

    assert await manejar_evento(uow, push, evento) is None
    assert almacen.notificaciones == {}


async def test_manejar_evento_sin_dispositivos_deja_la_notificacion_fallida(uow, almacen, push):
    evento = _evento("PolizaModificada", _payload(numero="POL-1"))

    notificacion = await manejar_evento(uow, push, evento)

    assert notificacion is not None
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "fallida"
    assert push.llamadas == []


async def test_manejar_evento_con_push_caido_deja_la_notificacion_fallida(uow, almacen):
    usuario = uuid4()
    _sembrar_dispositivo(almacen, usuario)
    evento = _evento("PolizaCancelada", _payload(usuario, numero="POL-1"))

    notificacion = await manejar_evento(uow, PushStub(fallar=True), evento)

    assert notificacion is not None
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "fallida"


async def test_usuario_inactivado_apaga_dispositivos_una_sola_vez(uow, almacen, push):
    usuario = uuid4()
    dispositivo = _sembrar_dispositivo(almacen, usuario)
    evento = _evento("UsuarioInactivado", {"usuario_id": str(usuario)})

    assert await manejar_evento(uow, push, evento) is None
    assert await manejar_evento(uow, push, evento) is None

    assert almacen.dispositivos[dispositivo.dispositivo_id].activo is False
    assert evento.evento_id in almacen.eventos_consumidos
    assert almacen.notificaciones == {}


async def test_manejar_evento_no_propaga_errores_inesperados(uow, push):
    class UowRota:
        def __call__(self):
            raise RuntimeError("base de datos caída")

    evento = _evento("PolizaEmitida", _payload())

    assert await manejar_evento(UowRota(), push, evento) is None
