from decimal import Decimal

from sqlalchemy import DateTime

from app.domain.modelos import AtributoPerfil, CausaDegradacion, EstadoAdaptador, OrigenAdaptador
from app.infrastructure.sql import Base, _atributo_a_json, _atributo_desde_json


def test_el_snapshot_conserva_modo_y_causa_del_adaptador():
    atributo = AtributoPerfil(
        nombre="zona_riesgo",
        valor=Decimal("0.5"),
        origen=OrigenAdaptador.OPEN_DATA,
        estado=EstadoAdaptador.DEGRADADO,
        degradado=True,
        modo="DEFAULT",
        causa=CausaDegradacion.TIMEOUT,
    )

    assert _atributo_desde_json(_atributo_a_json(atributo)) == atributo


def test_un_snapshot_anterior_sin_modo_ni_causa_se_lee_como_respuesta_en_vivo():
    atributo = _atributo_desde_json(
        {"nombre": "zona_riesgo", "valor": "0.3", "origen": "open_data", "estado": "exito", "degradado": False}
    )

    assert (atributo.modo, atributo.causa) == ("LIVE", None)


def test_todas_las_fechas_se_mapean_como_timestamptz():
    columnas = [
        f"{tabla.name}.{columna.name}"
        for tabla in Base.metadata.tables.values()
        for columna in tabla.columns
        if isinstance(columna.type, DateTime) and not columna.type.timezone
    ]
    assert columnas == []


def test_el_ajuste_competitivo_se_reconstruye_desde_los_factores_guardados():
    from app.domain.modelos import FactorInterno, ajuste_por_factores
    from app.infrastructure.sql import _factor_a_json, _factor_desde_json

    zona = AtributoPerfil(
        nombre="zona_riesgo",
        valor=Decimal("1"),
        origen=OrigenAdaptador.OPEN_DATA,
        estado=EstadoAdaptador.EXITO,
        degradado=False,
    )
    factores = (
        FactorInterno(factor="zona_riesgo", impacto="aumenta_prima", peso=Decimal("0.20")),
        FactorInterno(factor="ajuste_competitivo", impacto="reduce_prima", peso=Decimal("1.10")),
    )

    leidos = tuple(_factor_desde_json(_factor_a_json(f)) for f in factores)

    assert leidos == factores
    assert ajuste_por_factores(leidos, (zona,)) == Decimal("1.10")
