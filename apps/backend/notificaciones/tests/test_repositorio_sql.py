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
