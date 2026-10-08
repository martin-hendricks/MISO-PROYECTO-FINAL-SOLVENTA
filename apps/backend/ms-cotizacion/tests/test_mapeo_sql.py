import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime

from app.domain.modelos import EstadoSolicitud, SolicitudCotizacion
from app.domain.rating import ReglaRating
from app.infrastructure.sql import Base, ReglaRatingFila, SolicitudFila, _a_dominio


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
