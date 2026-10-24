from sqlalchemy import DateTime

from app.infrastructure.sql import Base


def test_todas_las_fechas_se_mapean_como_timestamptz():
    columnas = [
        f"{tabla.name}.{columna.name}"
        for tabla in Base.metadata.tables.values()
        for columna in tabla.columns
        if isinstance(columna.type, DateTime) and not columna.type.timezone
    ]
    assert columnas == []


def test_tablas_esperadas_estan_registradas():
    nombres = {tabla.name for tabla in Base.metadata.tables.values()}
    assert nombres == {
        "siniestro",
        "siniestro_transicion",
        "evento_parametrico",
        "evaluacion_umbral",
        "pago_parametrico",
        "outbox_evento",
    }


def test_claves_de_idempotencia_son_unicas():
    tablas = {t.name: t for t in Base.metadata.tables.values()}
    assert tablas["siniestro"].c.evento_id.unique
    assert tablas["evento_parametrico"].c.evento_id.primary_key
    assert tablas["evaluacion_umbral"].c.evento_id.unique
    assert tablas["pago_parametrico"].c.evento_id.unique
