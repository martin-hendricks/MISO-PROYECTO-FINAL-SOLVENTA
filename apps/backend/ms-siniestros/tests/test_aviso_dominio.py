"""Dominio del siniestro asistido: agregado, evidencia, parametría y motor de reglas."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain import motor_reglas
from app.domain.aviso import (
    Adjunto,
    ArchivoEvidencia,
    PagoSiniestro,
    ParametroRamo,
    OrigenDecision,
    ResultadoAuditado,
    clave_pago,
    validar_cantidad_adjuntos,
)
from app.domain.errores import ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import EstadoSiniestro, Geo, ResultadoDecision, Siniestro, SnapshotPoliza, TipoSiniestro

HOY = date.today()
DISPOSITIVO = ParametroRamo("proteccion-dispositivo", Decimal("420000"), Decimal("500000"))


def poliza(**cambios) -> SnapshotPoliza:
    base = dict(
        poliza_id=uuid4(),
        numero="POL-88421",
        ramo="proteccion-dispositivo",
        estado="vigente",
        inicio_vigencia=HOY - timedelta(days=60),
        fin_vigencia=HOY + timedelta(days=300),
        suma_asegurada=Decimal("5000000"),
    )
    return SnapshotPoliza(**(base | cambios))


def aviso(**cambios) -> Siniestro:
    base = dict(
        usuario_id=uuid4(),
        poliza=poliza(),
        fecha_hecho=HOY - timedelta(days=1),
        descripcion="Pantalla rota",
        canal="web",
    )
    return Siniestro.avisar(**(base | cambios))


def en_evaluacion(**cambios) -> Siniestro:
    s = aviso(**cambios)
    s.tomar_para_evaluacion("motor")
    return s


# --- Agregado


def test_aviso_nace_recibido_asistido_y_con_traza_del_canal():
    s = aviso()
    assert s.tipo is TipoSiniestro.ASISTIDO
    assert s.estado is EstadoSiniestro.RECIBIDO
    assert s.evento_id is None
    assert s.historial[0].origen == "cliente:web"
    assert s.requiere_revision is False


def test_aviso_sin_descripcion_se_rechaza():
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        aviso(descripcion="   ")
    assert exc.value.codigo == "aviso_sin_descripcion"


def test_aviso_con_fecha_futura_se_rechaza():
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        aviso(fecha_hecho=HOY + timedelta(days=1))
    assert exc.value.codigo == "fecha_hecho_futura"


def test_geo_fuera_de_rango_se_rechaza():
    with pytest.raises(ReglaDeNegocioViolada):
        Geo(Decimal("91"), Decimal("0"))


def test_rechazar_sin_motivo_no_cambia_estado():
    s = en_evaluacion()
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        s.decidir(ResultadoDecision.RECHAZADO, "  ", "operador:ana")
    assert exc.value.codigo == "motivo_requerido"
    assert s.estado is EstadoSiniestro.EN_EVALUACION
    assert s.resultado is None


def test_rechazado_es_terminal():
    s = en_evaluacion()
    s.decidir(ResultadoDecision.RECHAZADO, "Documentación incompleta", "operador:ana")
    for destino in (EstadoSiniestro.PAGADO, EstadoSiniestro.ENRUTADO):
        with pytest.raises(TransicionInvalida):
            s.cambiar_estado(destino, "operador:ana")


def test_aprobado_puede_pasar_de_decidido_a_pagado():
    s = en_evaluacion()
    s.decidir(ResultadoDecision.APROBADO, None, "operador:ana")
    s.cambiar_estado(EstadoSiniestro.PAGADO, "operador:ana")
    assert s.estado is EstadoSiniestro.PAGADO


def test_decidir_fuera_de_evaluacion_es_transicion_invalida():
    s = aviso()  # sigue RECIBIDO: el motor aún no lo tomó
    with pytest.raises(TransicionInvalida):
        s.decidir(ResultadoDecision.APROBADO, None, "operador:ana")


def test_enrutar_a_perito_sale_de_la_cola():
    s = en_evaluacion()
    s.retener_para_revision("monto alto")
    s.enrutar_a_perito("operador:ana")
    assert s.estado is EstadoSiniestro.ENRUTADO
    assert s.requiere_revision is False


def test_parametrico_sin_resultado_conserva_tabla_original():
    """Compatibilidad HU-30: un paramétrico DECIDIDO (sin resultado) no salta a PAGADO."""
    s = Siniestro.recibir("evt-x", origen="api")
    s.cambiar_estado(EstadoSiniestro.EN_EVALUACION, "sistema")
    s.cambiar_estado(EstadoSiniestro.DECIDIDO, "sistema")
    with pytest.raises(TransicionInvalida):
        s.cambiar_estado(EstadoSiniestro.PAGADO, "sistema")


# --- Evidencia


def test_adjunto_valida_tipo_y_tamano_y_no_usa_el_nombre_en_la_llave():
    s = aviso()
    adjunto = Adjunto.desde_archivo(ArchivoEvidencia("../../etc/passwd.png", "image/png", b"x" * 10, "foto"), s, "b")
    assert adjunto.s3_key == f"siniestros/{s.id}/{adjunto.id}"
    assert adjunto.usuario_id == s.usuario_id
    assert len(adjunto.sha256) == 64

    with pytest.raises(ReglaDeNegocioViolada) as exc:
        Adjunto.desde_archivo(ArchivoEvidencia("a.exe", "application/x-msdownload", b"x"), s, "b")
    assert exc.value.codigo == "evidencia_tipo_no_permitido"

    with pytest.raises(ReglaDeNegocioViolada) as exc:
        Adjunto.desde_archivo(ArchivoEvidencia("a.png", "image/png", b"x" * (10 * 1024 * 1024 + 1)), s, "b")
    assert exc.value.codigo == "evidencia_muy_grande"


def test_aviso_requiere_entre_uno_y_cinco_archivos():
    with pytest.raises(ReglaDeNegocioViolada):
        validar_cantidad_adjuntos([])
    with pytest.raises(ReglaDeNegocioViolada):
        validar_cantidad_adjuntos([ArchivoEvidencia("a.png", "image/png", b"x")] * 6)


# --- Parametría y pago


def test_reserva_nunca_supera_la_suma_asegurada():
    assert DISPOSITIVO.reserva_para(Decimal("300000")) == Decimal("300000")
    assert DISPOSITIVO.reserva_para(Decimal("5000000")) == Decimal("420000")
    assert DISPOSITIVO.reserva_para(None) == Decimal("420000")


def test_pago_solo_para_aprobado_de_bajo_monto_y_clave_determinista():
    s = en_evaluacion()
    s.reserva, s.umbral_automatico = Decimal("420000"), Decimal("500000")
    with pytest.raises(ReglaDeNegocioViolada):
        PagoSiniestro.autorizar(s, OrigenDecision.OPERADOR, "ana")  # aún no aprobado
    s.decidir(ResultadoDecision.APROBADO, None, "operador:ana")
    pago = PagoSiniestro.autorizar(s, OrigenDecision.OPERADOR, "ana")
    assert pago.monto == Decimal("420000")
    assert pago.clave_idempotencia == clave_pago(s.id)

    s.reserva = Decimal("600000")
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        PagoSiniestro.autorizar(s, OrigenDecision.OPERADOR, "ana")
    assert exc.value.codigo == "monto_sobre_umbral"


# --- Motor de reglas


def test_motor_aprueba_bajo_monto_que_cumple_todo():
    r = motor_reglas.evaluar(aviso(), DISPOSITIVO, cantidad_adjuntos=1, avisos_previos_en_ventana=0)
    assert r.resultado is ResultadoAuditado.APROBADO
    assert r.reserva == Decimal("420000")
    assert all(regla.cumple for regla in r.reglas)
    assert len(r.reglas) == 6  # traza completa


def test_motor_rechaza_poliza_no_vigente():
    r = motor_reglas.evaluar(aviso(poliza=poliza(estado="cancelada")), DISPOSITIVO, 1, 0)
    assert r.resultado is ResultadoAuditado.RECHAZADO
    assert "no está vigente" in r.motivo


def test_motor_rechaza_hecho_fuera_de_vigencia():
    p = poliza(inicio_vigencia=HOY - timedelta(days=10))
    r = motor_reglas.evaluar(aviso(poliza=p, fecha_hecho=HOY - timedelta(days=20)), DISPOSITIVO, 1, 0)
    assert r.resultado is ResultadoAuditado.RECHAZADO


def test_motor_retiene_monto_sobre_umbral():
    vida = ParametroRamo("vida-crediticia", Decimal("3200000"), Decimal("500000"))
    r = motor_reglas.evaluar(aviso(poliza=poliza(ramo="vida-crediticia")), vida, 1, 0)
    assert r.resultado is ResultadoAuditado.REVISION
    assert "umbral" in r.motivo


def test_motor_retiene_posible_duplicado_antifraude():
    r = motor_reglas.evaluar(aviso(), DISPOSITIVO, 1, avisos_previos_en_ventana=1)
    assert r.resultado is ResultadoAuditado.REVISION
    assert "duplicado" in r.motivo


def test_motor_retiene_ramo_sin_parametria_y_sin_evidencia():
    r = motor_reglas.evaluar(aviso(poliza=poliza(ramo="soat-motocicleta")), None, 0, 0)
    assert r.resultado is ResultadoAuditado.REVISION
    codigos_fallidos = {regla.codigo for regla in r.reglas if not regla.cumple}
    assert {"ramo_parametrizado", "evidencia_adjunta", "monto_bajo_umbral"} <= codigos_fallidos


def test_motor_rechazo_tiene_prioridad_sobre_revision():
    r = motor_reglas.evaluar(aviso(poliza=poliza(estado="cancelada")), None, 0, 3)
    assert r.resultado is ResultadoAuditado.RECHAZADO


def test_motor_es_determinista():
    s = aviso()
    a = motor_reglas.evaluar(s, DISPOSITIVO, 1, 0)
    b = motor_reglas.evaluar(s, DISPOSITIVO, 1, 0)
    assert (a.resultado, a.motivo, a.reglas) == (b.resultado, b.motivo, b.reglas)
