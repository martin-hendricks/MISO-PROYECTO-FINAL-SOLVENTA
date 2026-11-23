import os
from uuid import uuid4

import pytest

from app.application import casos_uso
from app.config import Settings
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


async def test_crear_notificacion_es_idempotente_en_postgres(uow):
    usuario = uuid4()
    evento = uuid4()

    primera = await casos_uso.crear_notificacion(
        uow, usuario, evento, "push", "tipo", "Título", "Cuerpo"
    )
    segunda = await casos_uso.crear_notificacion(
        uow, usuario, evento, "push", "tipo", "Otro", "Otro"
    )

    assert segunda.notificacion_id == primera.notificacion_id
    assert [n.notificacion_id for n in await casos_uso.listar_notificaciones(uow, usuario, 10)] == [
        primera.notificacion_id
    ]


async def test_registrar_y_reactivar_dispositivo_en_postgres(uow):
    usuario = uuid4()
    token = f"token-{uuid4()}"

    creado = await casos_uso.registrar_dispositivo(uow, usuario, "android", token)
    await casos_uso.desactivar_dispositivo(uow, usuario, creado.dispositivo.dispositivo_id)
    reactivado = await casos_uso.registrar_dispositivo(uow, usuario, "ios", token)

    assert not reactivado.creado
    assert reactivado.dispositivo.dispositivo_id == creado.dispositivo.dispositivo_id
    assert reactivado.dispositivo.activo
    assert reactivado.dispositivo.plataforma == "ios"


async def test_evento_consumido_y_desactivar_dispositivos_en_postgres(uow):
    usuario = uuid4()
    evento = uuid4()
    await casos_uso.registrar_dispositivo(uow, usuario, "android", f"token-{uuid4()}")
    await casos_uso.registrar_dispositivo(uow, usuario, "android", f"token-{uuid4()}")

    async with uow() as tx:
        assert await tx.eventos.consumir(evento, "UsuarioInactivado")
        repetido = await tx.eventos.consumir(evento, "UsuarioInactivado")
        await tx.dispositivos.desactivar_de_usuario(usuario)
        await tx.confirmar()

    assert repetido is False
    assert await casos_uso.listar_audiencia(uow, [usuario]) == []


async def test_audiencia_y_historial_de_difusion_en_postgres(uow):
    con_token, sin_token = uuid4(), uuid4()
    await casos_uso.registrar_dispositivo(uow, con_token, "android", f"token-{uuid4()}")

    audiencia = dict(await casos_uso.listar_audiencia(uow, [con_token, sin_token]))
    assert audiencia[con_token] == 1
    assert sin_token not in audiencia

    from app.infrastructure.push_stub import PushStub

    primera = await casos_uso.difundir(
        uow, PushStub(), uuid4(), "Primera", "Cuerpo", "usuarios", [con_token], None
    )
    segunda = await casos_uso.difundir(
        uow, PushStub(), uuid4(), "Segunda", "Cuerpo", "usuarios", [con_token], "POL-2"
    )
    pagina = await casos_uso.listar_difusiones(uow, 1, None)
    assert [d.difusion_id for d in pagina] == [segunda.difusion_id]
    anterior = await casos_uso.listar_difusiones(uow, 1, pagina[0].creada_en)
    assert [d.difusion_id for d in anterior] == [primera.difusion_id]
