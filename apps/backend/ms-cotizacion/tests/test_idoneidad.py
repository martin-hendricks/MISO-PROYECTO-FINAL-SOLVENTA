from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errores import ReglaDeNegocioViolada
from app.domain.rating import ReglaRating, evaluar_idoneidad


def _regla(maximo="0.40"):
    return ReglaRating(id=uuid4(), producto="vida", version="2", formula={"porcentaje_maximo": maximo})


def test_ratio_igual_al_umbral_sigue_siendo_elegible():
    evaluar_idoneidad(_regla(), {"ingresos_mensuales": "100", "gastos_mensuales": "40"})


def test_ratio_por_encima_del_umbral_no_crea_oferta():
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        evaluar_idoneidad(_regla(), {"ingresos_mensuales": Decimal("100"), "gastos_mensuales": Decimal("41")})
    assert exc.value.codigo == "idoneidad_no_cumplida"


def test_sin_umbral_no_cambia_la_cotizacion_existente():
    evaluar_idoneidad(
        ReglaRating(id=uuid4(), producto="vida", version="1", formula={}),
        {"ingresos_mensuales": "1", "gastos_mensuales": "9"},
    )
