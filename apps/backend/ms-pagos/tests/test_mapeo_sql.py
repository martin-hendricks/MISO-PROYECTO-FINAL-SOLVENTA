from sqlalchemy import DateTime

from app.infrastructure.sql import Base, PagoFila


def test_todas_las_fechas_se_mapean_como_timestamptz():
    columnas = [
        f"{tabla.name}.{columna.name}"
        for tabla in Base.metadata.tables.values()
        for columna in tabla.columns
        if isinstance(columna.type, DateTime) and not columna.type.timezone
    ]
    assert columnas == []


def test_pago_guarda_la_moneda_de_inicio_con_defecto_cop():
    columna = PagoFila.__table__.c.moneda

    assert columna.nullable is False
    assert columna.default.arg == "COP"
