import os
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.config import Settings
from app.domain.modelos import EstadoSiniestro
from app.infrastructure.pagos import AdaptadorDesembolsoStub
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


@pytest.fixture
def adaptador_desembolso() -> AdaptadorDesembolsoStub:
    return AdaptadorDesembolsoStub()


async def test_ingesta_idempotente_persiste_evento_evaluacion_y_pago(uow, adaptador_desembolso):
    evento_id = f"it-{uuid4()}"

    primero = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, evento_id, Decimal("100"), Decimal("80"), True, Decimal("500.00")
    )
    segundo = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, evento_id, Decimal("100"), Decimal("80"), True, Decimal("500.00")
    )

    assert primero.procesado and not segundo.procesado
    assert segundo.pago.id == primero.pago.id
    assert len(adaptador_desembolso.desembolsos) == 1

    async with uow() as tx:
        total_pagos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.pago_parametrico WHERE evento_id = :id"),
            {"id": evento_id},
        )
    assert total_pagos == 1


async def test_cambiar_estado_persiste_historial(uow, adaptador_desembolso):
    evento_id = f"it-{uuid4()}"
    resultado = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, evento_id, Decimal("10"), Decimal("80"), True, Decimal("1")
    )  # queda en 'decidido' (umbral no cumplido)

    siniestro = await casos_uso.cambiar_estado_siniestro(
        uow, resultado.siniestro.id, EstadoSiniestro.ENRUTADO, "operador-it"
    )

    assert siniestro.estado is EstadoSiniestro.ENRUTADO
    releido = await casos_uso.consultar_siniestro(uow, resultado.siniestro.id)
    assert releido.estado is EstadoSiniestro.ENRUTADO
    assert any(t.origen == "operador-it" for t in releido.historial)


async def test_siniestros_abiertos_de_poliza_persisten_y_excluyen_pagados(uow, adaptador_desembolso):
    poliza_id = uuid4()
    abierto = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, f"it-abierto-{uuid4()}", Decimal("10"), Decimal("80"), True, Decimal("1"), poliza_id
    )  # decidido (umbral no cumplido) -> abierto
    await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, f"it-pagado-{uuid4()}", Decimal("100"), Decimal("80"), True, Decimal("1"), poliza_id
    )  # pagado -> no cuenta como abierto

    abiertos = await casos_uso.listar_siniestros_abiertos_de_poliza(uow, poliza_id)

    assert [s.id for s in abiertos] == [abierto.siniestro.id]
