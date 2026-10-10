import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DateTime

from app.domain.modelos import EstadoSolicitud, SolicitudCotizacion
from app.domain.oferta import Oferta
from app.domain.rating import ReglaRating
from app.domain.riesgo import OrigenFactorRiesgo
from app.infrastructure.sql import Base, OfertaFila, ReglaRatingFila, SolicitudFila, _a_dominio, _oferta_a_dominio


def test_todas_las_fechas_se_mapean_como_timestamptz():
    columnas = [
        f"{tabla.name}.{columna.name}"
        for tabla in Base.metadata.tables.values()
        for columna in tabla.columns
        if isinstance(columna.type, DateTime) and not columna.type.timezone
    ]
    assert columnas == []


def test_solicitud_fila_a_dominio_ida_y_vuelta():
    solicitud = SolicitudCotizacion(
        id=uuid4(),
        idempotency_key="clave-0001",
        usuario_id=uuid4(),
        socio_id=uuid4(),
        consentimiento_id=uuid4(),
        producto="soat-motocicleta",
        canal="app-socio",
        datos_riesgo={"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"},
        estado=EstadoSolicitud.RECIBIDA,
        creada_en=datetime.now(UTC),
    )

    fila = SolicitudFila(
        solicitud_id=solicitud.id,
        idempotency_key=solicitud.idempotency_key,
        usuario_id=solicitud.usuario_id,
        socio_id=solicitud.socio_id,
        consentimiento_id=solicitud.consentimiento_id,
        producto=solicitud.producto,
        canal=solicitud.canal,
        datos_riesgo=solicitud.datos_riesgo,
        estado=solicitud.estado.value,
        creada_en=solicitud.creada_en,
    )

    reconstruida = _a_dominio(fila)

    assert reconstruida == solicitud


def test_regla_rating_fila_formula_json_ida_y_vuelta():
    regla = ReglaRating(
        id=uuid4(),
        producto="soat-motocicleta",
        version="0001",
        formula={"insumos_requeridos": ["cilindraje_cc"], "base": "120000", "gastos_fijos": "8500", "moneda": "COP"},
    )

    fila = ReglaRatingFila(
        regla_id=regla.id, producto=regla.producto, version=regla.version, formula=json.dumps(regla.formula)
    )
    reconstruida = ReglaRating(
        id=fila.regla_id, producto=fila.producto, version=fila.version, formula=json.loads(fila.formula)
    )

    assert reconstruida == regla


def test_oferta_fila_a_dominio_ida_y_vuelta():
    oferta = Oferta(
        id=uuid4(),
        solicitud_id=uuid4(),
        regla_id=uuid4(),
        version_regla="0001",
        prima_neta=Decimal("120000.00"),
        gastos_expedicion=Decimal("8500.00"),
        moneda="COP",
        coberturas=["muerte", "incapacidad_permanente"],
        factor_riesgo=Decimal("1.1000"),
        factor_riesgo_origen=OrigenFactorRiesgo.REAL,
        vence_en=datetime.now(UTC) + timedelta(minutes=60),
    )

    fila = OfertaFila(
        oferta_id=oferta.id,
        solicitud_id=oferta.solicitud_id,
        regla_id=oferta.regla_id,
        version_regla=oferta.version_regla,
        prima=oferta.prima,
        prima_neta=oferta.prima_neta,
        gastos_expedicion=oferta.gastos_expedicion,
        moneda=oferta.moneda,
        coberturas=",".join(oferta.coberturas),
        factor_riesgo=oferta.factor_riesgo,
        factor_riesgo_origen=oferta.factor_riesgo_origen.value,
        vence_en=oferta.vence_en,
    )

    reconstruida = _oferta_a_dominio(fila)

    assert reconstruida == oferta
