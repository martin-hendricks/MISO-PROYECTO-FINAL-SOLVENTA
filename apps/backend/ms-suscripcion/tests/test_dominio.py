from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import Decision, Suscripcion, suscripcion_decidida

from .dobles import regla


def _decidir(score: str, score_maximo: str = "0.7") -> Suscripcion:
    return Suscripcion.decidir(uuid4(), uuid4(), Decimal(score), regla(score_maximo))


def test_score_dentro_del_umbral_se_acepta_con_motivo_y_marca_de_tiempo():
    suscripcion = _decidir("0.5")

    assert suscripcion.decision is Decision.ACEPTADA
    assert suscripcion.aceptada
    assert suscripcion.motivo == "Riesgo dentro del apetito"
    assert suscripcion.evaluada_en.tzinfo is not None


def test_score_igual_al_umbral_se_acepta():
    assert _decidir("0.7").decision is Decision.ACEPTADA


def test_score_por_encima_del_umbral_se_rechaza_con_motivo():
    suscripcion = _decidir("0.71")

    assert suscripcion.decision is Decision.RECHAZADA
    assert not suscripcion.aceptada
    assert suscripcion.motivo == "Riesgo fuera del apetito"


def test_la_decision_es_determinista_para_el_mismo_riesgo():
    misma_regla = regla()
    decisiones = {misma_regla.evaluar(Decimal("0.69")) for _ in range(50)}

    assert decisiones == {(Decision.ACEPTADA, "Riesgo dentro del apetito")}


def test_cambiar_la_regla_cambia_la_decision_sin_tocar_codigo():
    assert _decidir("0.8", score_maximo="0.7").decision is Decision.RECHAZADA
    assert _decidir("0.8", score_maximo="0.9").decision is Decision.ACEPTADA


def test_score_negativo_viola_regla_de_negocio():
    with pytest.raises(ReglaDeNegocioViolada) as error:
        _decidir("-0.1")
    assert error.value.codigo == "score_negativo"


def test_evento_suscripcion_decidida_lleva_decision_y_motivo():
    suscripcion = _decidir("0.9")
    evento = suscripcion_decidida(suscripcion)

    assert evento.tipo == "SuscripcionDecidida"
    assert evento.agregado_id == suscripcion.id
    assert evento.payload["decision"] == "RECHAZADA"
    assert evento.payload["motivo"] == "Riesgo fuera del apetito"
    assert evento.payload["solicitud_id"] == str(suscripcion.solicitud_id)
