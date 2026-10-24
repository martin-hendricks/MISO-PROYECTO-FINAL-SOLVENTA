from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import (
    Cobertura,
    EstadoPoliza,
    Poliza,
    numero_de_poliza,
    poliza_emitida,
)

from .dobles import coberturas


def _emitir(lista=None, hoy=date(2026, 10, 23)) -> Poliza:
    return Poliza.emitir(uuid4(), uuid4(), "POL-2026-00000001", coberturas() if lista is None else lista, hoy)


def test_la_poliza_emitida_queda_vigente_por_un_anio_con_sus_coberturas():
    poliza = _emitir()

    assert poliza.estado is EstadoPoliza.VIGENTE
    assert (poliza.inicio_vigencia, poliza.fin_vigencia) == (date(2026, 10, 23), date(2027, 10, 22))
    assert [c.nombre for c in poliza.coberturas] == ["Responsabilidad civil", "Daños totales"]


def test_vigencia_iniciada_un_29_de_febrero_termina_el_27_de_febrero():
    poliza = _emitir(hoy=date(2028, 2, 29))

    assert poliza.fin_vigencia == date(2029, 2, 27)


def test_numero_de_poliza_incluye_anio_y_secuencia():
    assert numero_de_poliza(2026, 42) == "POL-2026-00000042"


@pytest.mark.parametrize(
    ("lista", "codigo"),
    [
        ([], "sin_coberturas"),
        ([Cobertura(nombre=" ", suma_asegurada=Decimal("1"))], "cobertura_sin_nombre"),
        ([Cobertura(nombre="RC", suma_asegurada=Decimal("0"))], "suma_asegurada_no_positiva"),
        ([Cobertura(nombre="RC", suma_asegurada=Decimal("1"), deducible=Decimal("-1"))], "deducible_negativo"),
    ],
)
def test_coberturas_invalidas_se_rechazan(lista, codigo):
    with pytest.raises(ReglaDeNegocioViolada) as error:
        _emitir(lista)

    assert error.value.codigo == codigo


def test_evento_poliza_emitida_lleva_numero_y_vigencia():
    poliza = _emitir()

    evento = poliza_emitida(poliza)

    assert evento.tipo == "PolizaEmitida"
    assert evento.agregado_id == poliza.id
    assert evento.payload["numero"] == "POL-2026-00000001"
    assert evento.payload["estado"] == "VIGENTE"
    assert evento.payload["fin_vigencia"] == "2027-10-22"
