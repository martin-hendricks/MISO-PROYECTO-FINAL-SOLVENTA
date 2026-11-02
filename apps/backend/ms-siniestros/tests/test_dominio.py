from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errores import EventoParametricoInvalido, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import (
    EstadoSiniestro,
    EvaluacionUmbral,
    EventoParametrico,
    PagoParametrico,
    Siniestro,
)


# --- HU-30: estados del siniestro -------------------------------------------------


def test_siniestro_recibido_queda_con_historial_y_origen():
    siniestro = Siniestro.recibir("evt-1", origen="api")

    assert siniestro.estado is EstadoSiniestro.RECIBIDO
    assert len(siniestro.historial) == 1
    assert siniestro.historial[0].origen == "api"


def test_siniestro_recibido_sin_poliza_id_queda_none():
    assert Siniestro.recibir("evt-1", origen="api").poliza_id is None


def test_siniestro_recibido_con_poliza_id_la_conserva():
    poliza_id = uuid4()

    assert Siniestro.recibir("evt-1", origen="api", poliza_id=poliza_id).poliza_id == poliza_id


def test_transicion_valida_deja_traza_con_marca_de_tiempo_y_origen():
    siniestro = Siniestro.recibir("evt-1", origen="api")

    siniestro.cambiar_estado(EstadoSiniestro.EN_EVALUACION, origen="operador-123")

    assert siniestro.estado is EstadoSiniestro.EN_EVALUACION
    assert len(siniestro.historial) == 2
    ultima = siniestro.historial[-1]
    assert ultima.estado is EstadoSiniestro.EN_EVALUACION
    assert ultima.origen == "operador-123"
    assert ultima.ocurrido_en is not None


def test_transicion_invalida_directa_a_pagado_se_rechaza_y_conserva_estado():
    siniestro = Siniestro.recibir("evt-1", origen="api")

    with pytest.raises(TransicionInvalida):
        siniestro.cambiar_estado(EstadoSiniestro.PAGADO, origen="operador-123")

    # El siniestro conserva su estado anterior: no queda en un estado intermedio.
    assert siniestro.estado is EstadoSiniestro.RECIBIDO
    assert len(siniestro.historial) == 1


def test_no_se_puede_retroceder_a_recibido():
    siniestro = Siniestro.recibir("evt-1", origen="api")
    siniestro.cambiar_estado(EstadoSiniestro.EN_EVALUACION, origen="operador")

    with pytest.raises(TransicionInvalida):
        siniestro.cambiar_estado(EstadoSiniestro.RECIBIDO, origen="operador")

    assert siniestro.estado is EstadoSiniestro.EN_EVALUACION


def test_no_se_puede_pagar_sin_haber_sido_decidido():
    siniestro = Siniestro.recibir("evt-1", origen="api")
    siniestro.cambiar_estado(EstadoSiniestro.EN_EVALUACION, origen="operador")

    with pytest.raises(TransicionInvalida):
        siniestro.cambiar_estado(EstadoSiniestro.PAGADO, origen="operador")


def test_recorrido_completo_de_estados():
    siniestro = Siniestro.recibir("evt-1", origen="api")
    for estado in (
        EstadoSiniestro.EN_EVALUACION,
        EstadoSiniestro.DECIDIDO,
        EstadoSiniestro.ENRUTADO,
        EstadoSiniestro.PAGADO,
    ):
        siniestro.cambiar_estado(estado, origen="sistema")

    assert siniestro.estado is EstadoSiniestro.PAGADO
    assert len(siniestro.historial) == 5


def test_pagado_es_estado_terminal():
    siniestro = Siniestro.recibir("evt-1", origen="api")
    for estado in (
        EstadoSiniestro.EN_EVALUACION,
        EstadoSiniestro.DECIDIDO,
        EstadoSiniestro.ENRUTADO,
        EstadoSiniestro.PAGADO,
    ):
        siniestro.cambiar_estado(estado, origen="sistema")

    with pytest.raises(TransicionInvalida):
        siniestro.cambiar_estado(EstadoSiniestro.EN_EVALUACION, origen="sistema")


# --- HU-32: evento paramétrico (stub) ---------------------------------------------


def test_recibir_evento_parametrico_valido():
    evento = EventoParametrico.recibir("evt-1", Decimal("120.5"))

    assert evento.evento_id == "evt-1"
    assert evento.valor == Decimal("120.5")
    assert evento.recibido_en is not None


def test_recibir_evento_sin_id_se_rechaza():
    with pytest.raises(EventoParametricoInvalido) as exc:
        EventoParametrico.recibir("", Decimal("10"))
    assert exc.value.codigo == "evento_sin_id"


def test_recibir_evento_con_id_en_blanco_se_rechaza():
    with pytest.raises(EventoParametricoInvalido) as exc:
        EventoParametrico.recibir("   ", Decimal("10"))
    assert exc.value.codigo == "evento_sin_id"


def test_recibir_evento_con_valor_no_numerico_se_rechaza():
    with pytest.raises(EventoParametricoInvalido) as exc:
        EventoParametrico.recibir("evt-1", "no-es-un-numero")
    assert exc.value.codigo == "evento_valor_invalido"


def test_recibir_evento_normaliza_espacios_en_el_id():
    evento = EventoParametrico.recibir("  evt-1  ", Decimal("5"))
    assert evento.evento_id == "evt-1"


# --- HU-33: evaluación de umbral ---------------------------------------------------


def test_umbral_cumplido_dispara_decision_true():
    evento = EventoParametrico.recibir("evt-1", Decimal("100"))

    evaluacion = EvaluacionUmbral.evaluar(evento, umbral=Decimal("80"), poliza_vigente=True)

    assert evaluacion.decision is True
    assert evaluacion.motivo == "umbral_cumplido"
    assert evaluacion.umbral == Decimal("80")
    assert evaluacion.valor == Decimal("100")


def test_umbral_exacto_cuenta_como_cumplido():
    evento = EventoParametrico.recibir("evt-1", Decimal("80"))

    evaluacion = EvaluacionUmbral.evaluar(evento, umbral=Decimal("80"), poliza_vigente=True)

    assert evaluacion.decision is True


def test_umbral_no_cumplido_registra_motivo():
    evento = EventoParametrico.recibir("evt-1", Decimal("50"))

    evaluacion = EvaluacionUmbral.evaluar(evento, umbral=Decimal("80"), poliza_vigente=True)

    assert evaluacion.decision is False
    assert evaluacion.motivo == "umbral_no_alcanzado"


def test_poliza_no_vigente_no_dispara_pago_aunque_supere_umbral():
    evento = EventoParametrico.recibir("evt-1", Decimal("999"))

    evaluacion = EvaluacionUmbral.evaluar(evento, umbral=Decimal("80"), poliza_vigente=False)

    assert evaluacion.decision is False
    assert evaluacion.motivo == "poliza_no_vigente"


def test_evaluacion_es_determinista():
    evento = EventoParametrico.recibir("evt-1", Decimal("100"))

    primera = EvaluacionUmbral.evaluar(evento, umbral=Decimal("80"), poliza_vigente=True)
    segunda = EvaluacionUmbral.evaluar(evento, umbral=Decimal("80"), poliza_vigente=True)

    assert (primera.decision, primera.motivo) == (segunda.decision, segunda.motivo)


# --- HU-34: pago paramétrico (stub) ------------------------------------------------


def test_disparar_pago_cuando_umbral_se_cumplio():
    evento = EventoParametrico.recibir("evt-1", Decimal("100"))
    evaluacion = EvaluacionUmbral.evaluar(evento, umbral=Decimal("80"), poliza_vigente=True)
    siniestro = Siniestro.recibir("evt-1", origen="api")

    pago = PagoParametrico.disparar(evaluacion, siniestro.id, Decimal("500.00"))

    assert pago.monto == Decimal("500.00")
    assert pago.evento_id == "evt-1"
    assert pago.siniestro_id == siniestro.id


def test_no_se_puede_disparar_pago_si_umbral_no_se_cumplio():
    evento = EventoParametrico.recibir("evt-1", Decimal("10"))
    evaluacion = EvaluacionUmbral.evaluar(evento, umbral=Decimal("80"), poliza_vigente=True)
    siniestro = Siniestro.recibir("evt-1", origen="api")

    with pytest.raises(ReglaDeNegocioViolada) as exc:
        PagoParametrico.disparar(evaluacion, siniestro.id, Decimal("500.00"))
    assert exc.value.codigo == "umbral_no_cumplido"


def test_pago_con_monto_no_positivo_se_rechaza():
    evento = EventoParametrico.recibir("evt-1", Decimal("100"))
    evaluacion = EvaluacionUmbral.evaluar(evento, umbral=Decimal("80"), poliza_vigente=True)
    siniestro = Siniestro.recibir("evt-1", origen="api")

    with pytest.raises(ReglaDeNegocioViolada) as exc:
        PagoParametrico.disparar(evaluacion, siniestro.id, Decimal("0"))
    assert exc.value.codigo == "monto_no_positivo"
