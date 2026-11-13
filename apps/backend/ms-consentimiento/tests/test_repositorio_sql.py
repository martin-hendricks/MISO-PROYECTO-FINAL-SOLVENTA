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


async def test_otorgar_es_idempotente_contra_el_indice_unico(uow):
    cliente_id = f"it-{uuid4()}"

    primero = await casos_uso.otorgar_consentimiento(uow, cliente_id)
    segundo = await casos_uso.otorgar_consentimiento(uow, cliente_id)

    assert primero.creado and not segundo.creado
    assert segundo.consentimiento.id == primero.consentimiento.id


async def test_revocar_persiste_estado_y_permite_otorgar_de_nuevo(uow):
    cliente_id = f"it-{uuid4()}"

    primero = await casos_uso.otorgar_consentimiento(uow, cliente_id)
    revocado = await casos_uso.revocar_consentimiento(uow, cliente_id)
    segundo = await casos_uso.otorgar_consentimiento(uow, cliente_id)

    assert not revocado.vigente
    assert segundo.creado
    assert segundo.consentimiento.id != primero.consentimiento.id
