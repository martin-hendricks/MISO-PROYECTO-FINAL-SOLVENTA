from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import DateTime, UniqueConstraint

from app.infrastructure.sql import Base, _notificacion_a_dominio


def test_todas_las_fechas_se_mapean_como_timestamptz():
    columnas = [
        f"{tabla.name}.{columna.name}"
        for tabla in Base.metadata.tables.values()
        for columna in tabla.columns
        if isinstance(columna.type, DateTime) and not columna.type.timezone
    ]
    assert columnas == []


def test_tablas_del_esquema_notificaciones():
    assert set(Base.metadata.tables) == {
        "notificaciones.notificacion",
        "notificaciones.dispositivo_push",
        "notificaciones.difusion",
        "notificaciones.evento_consumido",
    }


def test_restricciones_de_idempotencia():
    notificacion = Base.metadata.tables["notificaciones.notificacion"]
    dispositivo = Base.metadata.tables["notificaciones.dispositivo_push"]

    unicas_notificacion = {
        c.name for c in notificacion.constraints if isinstance(c, UniqueConstraint)
    }
    unicas_dispositivo = {
        c.name for c in dispositivo.constraints if isinstance(c, UniqueConstraint)
    }

    assert "uq_notificacion_evento_canal" in unicas_notificacion
    assert "uq_dispositivo_usuario_token" in unicas_dispositivo


def test_la_fila_conserva_poliza_y_difusion():
    ahora = datetime.now(UTC)
    fila = SimpleNamespace(
        notificacion_id=uuid4(),
        usuario_id=uuid4(),
        evento_origen_id=None,
        canal="push",
        tipo="mensaje_operador",
        titulo="Aviso",
        cuerpo="Cuerpo",
        destino="poliza-detalle",
        poliza="POL-9",
        difusion_id=uuid4(),
        estado="pendiente",
        creada_en=ahora,
        enviada_en=None,
        leida_en=None,
        proveedor_id=None,
    )
    notificacion = _notificacion_a_dominio(fila)
    assert notificacion.poliza == "POL-9"
    assert notificacion.difusion_id == fila.difusion_id
