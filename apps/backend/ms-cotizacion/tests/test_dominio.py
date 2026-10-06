from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.domain.errores import DatoRiesgoInvalido, ReglaDeNegocioViolada
from app.domain.modelos import Cotizacion, EstadoCotizacion
from app.infrastructure.catalogo_memoria import PROTECCION_DISPOSITIVO

from .conftest import DATOS_VALIDOS

AHORA = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)


def test_datos_validos_se_normalizan():
    datos = PROTECCION_DISPOSITIVO.validar_datos_riesgo({**DATOS_VALIDOS, "marca": "  Pixel  "})

    assert datos == {"valorDispositivo": 2_400_000, "marca": "Pixel", "masDe12Meses": False}


@pytest.mark.parametrize("valor", [300_000, 8_000_000])
def test_limites_del_rango_son_validos(valor):
    datos = PROTECCION_DISPOSITIVO.validar_datos_riesgo({**DATOS_VALIDOS, "valorDispositivo": valor})

    assert datos["valorDispositivo"] == valor


@pytest.mark.parametrize("valor", [299_999, 8_000_001, 0, -1])
def test_fuera_de_rango_nombra_el_campo_y_su_rango(valor):
    with pytest.raises(DatoRiesgoInvalido) as exc:
        PROTECCION_DISPOSITIVO.validar_datos_riesgo({**DATOS_VALIDOS, "valorDispositivo": valor})

    assert exc.value.codigo == "dato_riesgo_fuera_de_rango"
    assert exc.value.campo == "valorDispositivo"
    assert exc.value.rango_valido == {"tipo": "entero", "min": 300_000, "max": 8_000_000}


@pytest.mark.parametrize(
    ("cambio", "campo", "codigo"),
    [
        ({"valorDispositivo": "2400000"}, "valorDispositivo", "dato_riesgo_tipo_invalido"),
        ({"valorDispositivo": True}, "valorDispositivo", "dato_riesgo_tipo_invalido"),
        ({"valorDispositivo": 2400000.5}, "valorDispositivo", "dato_riesgo_tipo_invalido"),
        ({"masDe12Meses": "no"}, "masDe12Meses", "dato_riesgo_tipo_invalido"),
        ({"marca": 123}, "marca", "dato_riesgo_tipo_invalido"),
        ({"marca": "   "}, "marca", "dato_riesgo_fuera_de_rango"),
        ({"marca": "x" * 41}, "marca", "dato_riesgo_fuera_de_rango"),
        ({"marca": None}, "marca", "dato_riesgo_faltante"),
        ({"color": "negro"}, "color", "dato_riesgo_no_reconocido"),
    ],
)
def test_datos_invalidos_nombran_el_campo(cambio, campo, codigo):
    with pytest.raises(DatoRiesgoInvalido) as exc:
        PROTECCION_DISPOSITIVO.validar_datos_riesgo({**DATOS_VALIDOS, **cambio})

    assert (exc.value.campo, exc.value.codigo) == (campo, codigo)


def test_dato_faltante_nombra_el_campo():
    datos = {k: v for k, v in DATOS_VALIDOS.items() if k != "masDe12Meses"}

    with pytest.raises(DatoRiesgoInvalido) as exc:
        PROTECCION_DISPOSITIVO.validar_datos_riesgo(datos)

    assert (exc.value.campo, exc.value.codigo) == ("masDe12Meses", "dato_riesgo_faltante")


def test_ofertar_combina_prima_y_factor_y_fija_vigencia():
    cotizacion = Cotizacion.ofertar(
        PROTECCION_DISPOSITIVO, DATOS_VALIDOS, Decimal("89000"), Decimal("1.15"), AHORA, timedelta(hours=24)
    )

    assert cotizacion.prima == Decimal("102350.00")
    assert cotizacion.moneda == "COP"
    assert cotizacion.estado is EstadoCotizacion.OFERTA_VIGENTE
    assert cotizacion.vence_en == AHORA + timedelta(hours=24)
    assert cotizacion.vigente_en(AHORA + timedelta(hours=23))
    assert not cotizacion.vigente_en(AHORA + timedelta(hours=24))


def test_cada_oferta_tiene_id_unico():
    ids = {
        Cotizacion.ofertar(
            PROTECCION_DISPOSITIVO, DATOS_VALIDOS, Decimal("1"), Decimal("1"), AHORA, timedelta(hours=1)
        ).id
        for _ in range(100)
    }

    assert len(ids) == 100


@pytest.mark.parametrize(
    ("prima", "factor", "codigo"),
    [(Decimal("0"), Decimal("1"), "prima_no_positiva"), (Decimal("1"), Decimal("0"), "factor_riesgo_no_positivo")],
)
def test_ofertar_rechaza_prima_o_factor_no_positivos(prima, factor, codigo):
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        Cotizacion.ofertar(PROTECCION_DISPOSITIVO, DATOS_VALIDOS, prima, factor, AHORA, timedelta(hours=1))

    assert exc.value.codigo == codigo
