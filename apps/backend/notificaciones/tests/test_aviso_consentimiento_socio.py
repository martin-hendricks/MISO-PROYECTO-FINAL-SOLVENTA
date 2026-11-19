from uuid import uuid4

import pytest

from app.application.manejadores import construir_contenido, manejar_evento
from app.domain.eventos import EventoBus
from app.domain.modelos import DispositivoPush


def _cotizacion(usuario_id, canal="socio", pendiente=True):
    return EventoBus.desde_mensaje(
        {
            "evento_id": str(uuid4()),
            "tipo": "SolicitudCotizacionRecibida",
            "agregado_id": str(uuid4()),
            "ocurrido_en": "2026-11-18T12:00:00+00:00",
            "origen": "ms_cotizacion",
            "payload": {
                "solicitud_id": str(uuid4()),
                "producto": "viaje",
                "usuario_id": str(usuario_id),
                "canal": canal,
                "consentimiento_pendiente": pendiente,
            },
        }
    )


async def test_cotizacion_de_socio_sin_consentimiento_avisa_al_cliente(uow, almacen, push):
    usuario = uuid4()
    dispositivo = DispositivoPush.registrar(usuario, "android", "token-1")
    almacen.dispositivos[dispositivo.dispositivo_id] = dispositivo

    notificacion = await manejar_evento(uow, push, _cotizacion(usuario))

    assert notificacion is not None
    assert notificacion.usuario_id == usuario
    assert notificacion.tipo == "consentimiento_pendiente"
    assert notificacion.destino == "consentimiento"
    assert notificacion.estado == "enviada"
    assert push.llamadas == [([dispositivo.dispositivo_id], notificacion.notificacion_id)]


def test_el_aviso_explica_que_falta_autorizar_los_datos():
    contenido = construir_contenido(_cotizacion(uuid4()))

    assert contenido is not None
    assert contenido.titulo == "Autoriza el uso de tus datos"
    assert contenido.cuerpo == (
        "Un aliado de Solventa te cotizó un seguro. Autoriza el uso de tus datos para poder aceptarlo."
    )


@pytest.mark.parametrize(
    ("canal", "pendiente"),
    [("socio", False), ("web", True), ("web", False), ("app-socio", True)],
)
async def test_no_avisa_si_no_es_socio_o_ya_hay_consentimiento(uow, almacen, push, canal, pendiente):
    notificacion = await manejar_evento(uow, push, _cotizacion(uuid4(), canal, pendiente))

    assert notificacion is None
    assert almacen.notificaciones == {}
    assert push.llamadas == []
