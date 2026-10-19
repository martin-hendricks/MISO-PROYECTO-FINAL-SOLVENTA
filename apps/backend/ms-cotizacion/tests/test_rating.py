from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errores import ReglaDeNegocioViolada
from app.domain.rating import ReglaRating, calcular_prima

REGLA = ReglaRating(
    id=uuid4(),
    producto="soat-motocicleta",
    version="0001",
    formula={"insumos_requeridos": ["cilindraje_cc"], "base": "120000", "gastos_fijos": "8500", "moneda": "COP"},
)


@pytest.mark.parametrize(
    "datos_riesgo",
    [
        {"cilindraje_cc": 150},
        {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"},
    ],
)
def test_calculo_es_repetible_dos_veces_seguidas(datos_riesgo):
    primero = calcular_prima(REGLA, datos_riesgo)
    segundo = calcular_prima(REGLA, datos_riesgo)

    assert primero == segundo
    assert primero.prima_neta == Decimal("120000.00")
    assert primero.gastos_expedicion == Decimal("8500.00")
    assert primero.moneda == "COP"


def test_insumo_obligatorio_ausente_lanza_error_tipificado():
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        calcular_prima(REGLA, {})

    assert exc.value.codigo == "insumo_obligatorio_ausente"
    assert "cilindraje_cc" in exc.value.mensaje
