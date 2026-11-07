from sqlalchemy import DateTime, UniqueConstraint

from app.infrastructure.sql import Base


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
