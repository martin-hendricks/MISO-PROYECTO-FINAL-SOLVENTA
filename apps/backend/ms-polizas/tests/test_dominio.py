from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errores import ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import (
    VENTANA_GRACIA_DIAS,
    Cobertura,
    EstadoPoliza,
    Poliza,
    numero_de_poliza,
    poliza_cancelada,
    poliza_emitida,
    poliza_modificada,
    poliza_renovada,
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


def test_emitir_fija_la_prima_como_la_suma_de_las_sumas_aseguradas():
    poliza = _emitir()

    assert poliza.prima.valor == sum(c.suma_asegurada for c in coberturas())
    assert poliza.prima.periodicidad == "ANUAL"


# --- Ciclo de vida: renovar (HU-59) ---------------------------------------


def test_renovar_extiende_la_fecha_de_fin_de_vigencia():
    poliza = _emitir()

    poliza.renovar(date(2028, 10, 22), hoy=date(2026, 10, 23))

    assert poliza.estado is EstadoPoliza.VIGENTE
    assert poliza.fin_vigencia == date(2028, 10, 22)


def test_renovar_con_fecha_no_posterior_se_rechaza():
    poliza = _emitir()

    with pytest.raises(ReglaDeNegocioViolada) as error:
        poliza.renovar(poliza.fin_vigencia, hoy=date(2026, 10, 23))

    assert error.value.codigo == "nueva_vigencia_no_posterior"


def test_renovar_una_poliza_cancelada_lanza_transicion_invalida():
    poliza = _emitir()
    poliza.cancelar("Ya no se necesita", date(2026, 10, 23), "op-1")

    with pytest.raises(TransicionInvalida):
        poliza.renovar(date(2028, 10, 22), hoy=date(2026, 10, 23))


def test_evento_poliza_renovada_lleva_la_nueva_vigencia():
    poliza = _emitir()
    poliza.renovar(date(2028, 10, 22), hoy=date(2026, 10, 23))

    evento = poliza_renovada(poliza)

    assert evento.tipo == "PolizaRenovada"
    assert evento.agregado_id == poliza.id
    assert evento.payload["fin_vigencia"] == "2028-10-22"


def test_renovar_dentro_de_la_ventana_de_gracia_tras_vencer_es_valido():
    poliza = _emitir()
    vencida_hace_poco = poliza.fin_vigencia + timedelta(days=VENTANA_GRACIA_DIAS)

    poliza.renovar(date(2028, 10, 22), hoy=vencida_hace_poco)

    assert poliza.estado is EstadoPoliza.VIGENTE
    assert poliza.fin_vigencia == date(2028, 10, 22)


def test_renovar_fuera_de_la_ventana_de_gracia_lanza_transicion_invalida():
    poliza = _emitir()
    vencida_hace_mucho = poliza.fin_vigencia + timedelta(days=VENTANA_GRACIA_DIAS + 1)

    with pytest.raises(TransicionInvalida):
        poliza.renovar(date(2028, 10, 22), hoy=vencida_hace_mucho)


def test_en_ventana_gracia_es_false_para_poliza_vigente_sin_vencer():
    poliza = _emitir()

    assert poliza.en_ventana_gracia(poliza.fin_vigencia) is False


def test_en_ventana_gracia_es_false_para_poliza_cancelada():
    poliza = _emitir()
    poliza.cancelar("Ya no se necesita", date(2026, 10, 23), "op-1")

    assert poliza.en_ventana_gracia(poliza.fin_vigencia + timedelta(days=1)) is False


# --- Ciclo de vida: modificar coberturas (HU-60) --------------------------


def test_modificar_coberturas_reemplaza_el_conjunto_completo():
    poliza = _emitir()
    nuevas = [Cobertura(nombre="Robo", suma_asegurada=Decimal("1000"), deducible=Decimal("10"))]

    poliza.modificar_coberturas(nuevas)

    assert poliza.estado is EstadoPoliza.VIGENTE
    assert [c.nombre for c in poliza.coberturas] == ["Robo"]


@pytest.mark.parametrize(
    ("lista", "codigo"),
    [
        ([], "sin_coberturas"),
        ([Cobertura(nombre=" ", suma_asegurada=Decimal("1"))], "cobertura_sin_nombre"),
        ([Cobertura(nombre="RC", suma_asegurada=Decimal("0"))], "suma_asegurada_no_positiva"),
        ([Cobertura(nombre="RC", suma_asegurada=Decimal("1"), deducible=Decimal("-1"))], "deducible_negativo"),
    ],
)
def test_modificar_coberturas_invalidas_se_rechaza_con_la_misma_regla_que_emitir(lista, codigo):
    poliza = _emitir()

    with pytest.raises(ReglaDeNegocioViolada) as error:
        poliza.modificar_coberturas(lista)

    assert error.value.codigo == codigo


def test_modificar_coberturas_de_una_poliza_cancelada_lanza_transicion_invalida():
    poliza = _emitir()
    poliza.cancelar("Ya no se necesita", date(2026, 10, 23), "op-1")

    with pytest.raises(TransicionInvalida):
        poliza.modificar_coberturas(coberturas())


def test_evento_poliza_modificada_lleva_las_nuevas_coberturas():
    poliza = _emitir()
    poliza.modificar_coberturas([Cobertura(nombre="Robo", suma_asegurada=Decimal("1000"))])

    evento = poliza_modificada(poliza)

    assert evento.tipo == "PolizaModificada"
    assert [c["nombre"] for c in evento.payload["coberturas"]] == ["Robo"]


# --- Ciclo de vida: cancelar (HU-61) ---------------------------------------


def test_cancelar_cambia_el_estado_y_registra_motivo_fecha_y_operador():
    poliza = _emitir()

    poliza.cancelar("El cliente lo pidió", date(2026, 11, 1), "op-1")

    assert poliza.estado is EstadoPoliza.CANCELADA
    assert poliza.motivo_cancelacion == "El cliente lo pidió"
    assert poliza.cancelada_en == date(2026, 11, 1)
    assert poliza.cancelada_por == "op-1"


def test_cancelar_sin_motivo_se_rechaza():
    poliza = _emitir()

    with pytest.raises(ReglaDeNegocioViolada) as error:
        poliza.cancelar("   ", date(2026, 11, 1), "op-1")

    assert error.value.codigo == "motivo_requerido"


def test_cancelar_sin_operador_se_rechaza():
    poliza = _emitir()

    with pytest.raises(ReglaDeNegocioViolada) as error:
        poliza.cancelar("El cliente lo pidió", date(2026, 11, 1), "   ")

    assert error.value.codigo == "operador_requerido"


def test_cancelar_dos_veces_lanza_transicion_invalida():
    poliza = _emitir()
    poliza.cancelar("El cliente lo pidió", date(2026, 11, 1), "op-1")

    with pytest.raises(TransicionInvalida) as error:
        poliza.cancelar("Otro motivo", date(2026, 11, 2), "op-2")

    assert error.value.codigo == "transicion_invalida"
    # Y no se pisa el motivo/fecha/operador de la primera cancelación, ni se
    # recalcula una segunda devolución.
    assert poliza.motivo_cancelacion == "El cliente lo pidió"
    assert poliza.cancelada_por == "op-1"


def test_evento_poliza_cancelada_lleva_motivo_fecha_operador_y_devolucion():
    poliza = _emitir()
    poliza.cancelar("El cliente lo pidió", date(2026, 11, 1), "op-1")

    evento = poliza_cancelada(poliza)

    assert evento.tipo == "PolizaCancelada"
    assert evento.payload["motivo_cancelacion"] == "El cliente lo pidió"
    assert evento.payload["cancelada_en"] == "2026-11-01"
    assert evento.payload["cancelada_por"] == "op-1"
    assert evento.payload["devolucion_estimada"] == str(poliza.devolucion_estimada)


# --- Devolución estimada al cancelar (HU-61) -------------------------------


def test_cancelar_a_mitad_de_vigencia_devuelve_aproximadamente_la_mitad_de_la_prima():
    poliza = _emitir(hoy=date(2026, 1, 1))  # vigencia: 2026-01-01 .. 2026-12-31 (364 días)

    poliza.cancelar("El cliente lo pidió", date(2026, 7, 2), "op-1")  # 182 días restantes

    prima = poliza.prima.valor
    assert poliza.devolucion_estimada == (prima * 182 / 364).quantize(Decimal("0.01"))


def test_cancelar_el_mismo_dia_de_emision_devuelve_casi_toda_la_prima():
    poliza = _emitir(hoy=date(2026, 1, 1))

    poliza.cancelar("El cliente lo pidió", date(2026, 1, 1), "op-1")

    assert poliza.devolucion_estimada == poliza.prima.valor.quantize(Decimal("0.01"))


def test_cancelar_despues_de_vencida_no_genera_devolucion():
    poliza = _emitir(hoy=date(2026, 1, 1))

    poliza.cancelar("El cliente lo pidió", poliza.fin_vigencia + timedelta(days=1), "op-1")

    assert poliza.devolucion_estimada == Decimal("0")
