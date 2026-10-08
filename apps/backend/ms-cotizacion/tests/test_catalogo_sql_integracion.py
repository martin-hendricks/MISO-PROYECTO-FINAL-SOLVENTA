import os
from decimal import Decimal

import pytest

from app.config import Settings
from app.domain.catalogo import UnidadLimite
from app.infrastructure.catalogo_sql import CatalogoSQL
from app.infrastructure.sql import crear_motor

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def motor():
    motor = crear_motor(Settings())
    yield motor
    await motor.dispose()


async def test_carga_la_semilla_de_soat_motocicleta(motor):
    catalogo = await CatalogoSQL.cargar(motor)

    soat = catalogo.obtener("soat-motocicleta")
    assert soat.moneda == "COP"
    assert [(c.codigo, c.limite) for c in soat.coberturas] == [
        ("gastos_medicos", Decimal("800.00")),
        ("incapacidad_permanente", Decimal("180.00")),
        ("muerte", Decimal("750.00")),
        ("gastos_transporte", Decimal("10.00")),
    ]
    assert {c.unidad_limite for c in soat.coberturas} == {UnidadLimite.SMLDV}
    assert set(soat.datos_riesgo) == {"cilindraje_cc", "modelo_anio", "ciudad_circulacion"}
