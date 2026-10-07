from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime

from app.domain.modelos import EstadoSolicitud, SolicitudCotizacion
from app.infrastructure.sql import Base, SolicitudFila, _a_dominio


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
