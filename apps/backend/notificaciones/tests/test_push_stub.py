from uuid import uuid4

import pytest

from app.domain.errores import ServicioExternoNoDisponible
from app.domain.modelos import DispositivoPush, Notificacion
from app.infrastructure.push_stub import PushStub
from app.main import crear_app


def _notificacion(usuario_id=None) -> Notificacion:
    return Notificacion.crear(
        usuario_id=usuario_id or uuid4(),
        evento_origen_id=uuid4(),
        canal="push",
        tipo="tipo",
        titulo="Título",
        cuerpo="Cuerpo",
    )


def test_la_app_expone_el_push_stub():
    assert isinstance(crear_app().state.push, PushStub)


async def test_push_stub_devuelve_id_determinista():
    notificacion = _notificacion()
    dispositivo = DispositivoPush.registrar(notificacion.usuario_id, "android", "token-1")

    proveedor = await PushStub().enviar(dispositivo, notificacion)

    assert proveedor == f"stub-{notificacion.notificacion_id}"
    assert await PushStub().enviar(dispositivo, notificacion) == proveedor


async def test_push_stub_a_usuario_devuelve_un_id_por_dispositivo():
    notificacion = _notificacion()
    dispositivos = [
        DispositivoPush.registrar(notificacion.usuario_id, "android", "token-1"),
        DispositivoPush.registrar(notificacion.usuario_id, "ios", "token-2"),
    ]

    proveedores = await PushStub().enviar_a_usuario(dispositivos, notificacion)

    assert [r.proveedor_id for r in proveedores] == [f"stub-{notificacion.notificacion_id}"] * 2
    assert {r.estado for r in proveedores} == {"enviado"}


async def test_push_stub_con_fallo_lanza_error_de_dominio():
    notificacion = _notificacion()
    dispositivo = DispositivoPush.registrar(notificacion.usuario_id, "android", "token-1")

    with pytest.raises(ServicioExternoNoDisponible):
        await PushStub(fallar=True).enviar(dispositivo, notificacion)
