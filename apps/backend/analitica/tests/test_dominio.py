from datetime import date

import pytest

from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import ConteoEventos


def test_crear_conteo_valido():
    conteo = ConteoEventos.crear("PolizaEmitida", date(2026, 1, 1))
    assert conteo.tipo == "PolizaEmitida"
    assert conteo.fecha == date(2026, 1, 1)
    assert conteo.cantidad == 1


def test_crear_conteo_tipo_no_soportado_lanza():
    with pytest.raises(ReglaDeNegocioViolada):
        ConteoEventos.crear("TipoInventado", date(2026, 1, 1))
