from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.domain.catalogo import RangoNumerico, ValoresPermitidos

from .dobles import SOAT_MOTOCICLETA


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(50, True), ("1800", True), (125.5, True), (49, False), (1801, False), ("abc", False), (None, False), (True, False)],
)
def test_rango_numerico_incluye_los_extremos_y_rechaza_lo_no_numerico(valor, esperado):
    assert RangoNumerico(Decimal("50"), Decimal("1800")).valido(valor) is esperado


def test_valores_permitidos():
    ciudades = ValoresPermitidos(("bogota", "cali"))

    assert ciudades.valido("cali")
    assert not ciudades.valido("Cali")
    assert ciudades.describir_rango() == "uno de: bogota, cali"


def test_la_definicion_del_producto_es_de_solo_lectura():
    with pytest.raises(FrozenInstanceError):
        SOAT_MOTOCICLETA.moneda = "USD"
    with pytest.raises(TypeError):
        SOAT_MOTOCICLETA.datos_riesgo["nuevo"] = RangoNumerico(Decimal("0"), Decimal("1"))
    with pytest.raises(AttributeError):
        SOAT_MOTOCICLETA.coberturas.append(SOAT_MOTOCICLETA.coberturas[0])


def test_codigos_de_coberturas_en_orden():
    assert SOAT_MOTOCICLETA.codigos_coberturas == [
        "gastos_medicos",
        "incapacidad_permanente",
        "muerte",
        "gastos_transporte",
    ]
