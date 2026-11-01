import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.config import Settings
from app.domain.precio import ANTIGUEDAD_DOCUMENTO, NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO, ZONA_RIESGO
from app.infrastructure.adaptadores import AdaptadorOpenDataStub, AdaptadorOpenFinanceStub
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
def config() -> Settings:
    return Settings()


async def test_consentimiento_otorgado_y_revocado_persiste(uow):
    cliente_id = f"it-{uuid4()}"

    await casos_uso.otorgar_consentimiento(uow, cliente_id)
    vigente = await casos_uso.consultar_consentimiento_vigente(uow, cliente_id)
    assert vigente is not None

    await casos_uso.revocar_consentimiento(uow, cliente_id)
    assert await casos_uso.consultar_consentimiento_vigente(uow, cliente_id) is None


async def test_otorgar_consentimiento_publica_evento_en_la_misma_transaccion(uow):
    cliente_id = f"it-{uuid4()}"

    registro = await casos_uso.otorgar_consentimiento(uow, cliente_id)

    async with uow() as tx:
        eventos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.outbox_evento WHERE agregado_id = :id"),
            {"id": registro.consentimiento.id},
        )
    assert eventos == 1


async def test_perfilar_y_ofertar_persiste_snapshot_completo(uow, config):
    cliente_id = f"it-{uuid4()}"
    await casos_uso.otorgar_consentimiento(uow, cliente_id)

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, AdaptadorOpenFinanceStub(), AdaptadorOpenDataStub(), config, f"it-{uuid4()}", cliente_id
    )

    async with uow() as tx:
        oferta = await tx.ofertas.obtener(resultado.oferta.id)
    assert oferta is not None
    assert oferta.precio > 0
    nombres = {a.nombre for a in oferta.snapshot_atributos}
    assert nombres == {NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO, ZONA_RIESGO, ANTIGUEDAD_DOCUMENTO}


async def test_ultima_oferta_por_cliente_es_la_mas_reciente(uow, config):
    cliente_id = f"it-{uuid4()}"
    await casos_uso.otorgar_consentimiento(uow, cliente_id)
    for _ in range(2):
        ultima = await casos_uso.perfilar_y_ofertar(
            uow, AdaptadorOpenFinanceStub(), AdaptadorOpenDataStub(), config, f"it-{uuid4()}", cliente_id
        )

    leida = await casos_uso.consultar_ultima_oferta(uow, cliente_id)

    assert leida.id == ultima.oferta.id
    assert leida.factor_ajuste == ultima.oferta.factor_ajuste
