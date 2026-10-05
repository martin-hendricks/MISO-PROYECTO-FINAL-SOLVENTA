from decimal import Decimal

import pytest

from app.domain.errores import ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import Ejemplo, EstadoEjemplo


def test_registrar_normaliza_y_queda_registrado():
    ejemplo = Ejemplo.registrar("clave-0001", "  REF-1  ", Decimal("10.50"))

    assert ejemplo.referencia == "REF-1"
    assert ejemplo.estado is EstadoEjemplo.REGISTRADO


@pytest.mark.parametrize(
    ("referencia", "monto", "codigo"),
    [("REF", Decimal("0"), "monto_no_positivo"), ("REF", Decimal("-1"), "monto_no_positivo"), ("  ", Decimal("1"), "referencia_vacia")],
)
def test_reglas_de_registro(referencia, monto, codigo):
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        Ejemplo.registrar("clave-0001", referencia, monto)
    assert exc.value.codigo == codigo


def test_aprobar_solo_desde_registrado():
    ejemplo = Ejemplo.registrar("clave-0001", "REF", Decimal("1"))
    ejemplo.aprobar()

    assert ejemplo.estado is EstadoEjemplo.APROBADO
    with pytest.raises(TransicionInvalida):
        ejemplo.aprobar()
