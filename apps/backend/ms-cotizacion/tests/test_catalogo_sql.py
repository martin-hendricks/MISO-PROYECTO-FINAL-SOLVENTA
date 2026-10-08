from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.catalogo import RangoNumerico, UnidadLimite, ValoresPermitidos
from app.infrastructure.catalogo_sql import CatalogoSQL, CoberturaFila, DatoRiesgoFila, ProductoFila, a_definicion


def _fila_producto(codigo="soat-motocicleta", moneda="COP", datos=None) -> ProductoFila:
    return ProductoFila(
        producto_id=uuid4(),
        codigo=codigo,
        nombre="SOAT motocicleta",
        ramo="soat",
        moneda=moneda,
        coberturas=[
            CoberturaFila(codigo="gastos_medicos", nombre="Gastos médicos", limite=Decimal("800.00"), unidad_limite="SMLDV", orden=1),
            CoberturaFila(codigo="muerte", nombre="Muerte", limite=Decimal("750.00"), unidad_limite="SMLDV", orden=2),
        ],
        datos_riesgo=datos
        if datos is not None
        else [
            DatoRiesgoFila(nombre="cilindraje_cc", tipo="rango", minimo=Decimal("50"), maximo=Decimal("1800")),
            DatoRiesgoFila(nombre="ciudad_circulacion", tipo="valores", valores=["bogota", "cali"]),
        ],
    )


def test_mapea_filas_a_la_definicion_del_producto():
    definicion = a_definicion(_fila_producto())

    assert (definicion.producto, definicion.moneda) == ("soat-motocicleta", "COP")
    assert [(c.codigo, c.limite, c.unidad_limite) for c in definicion.coberturas] == [
        ("gastos_medicos", Decimal("800.00"), UnidadLimite.SMLDV),
        ("muerte", Decimal("750.00"), UnidadLimite.SMLDV),
    ]
    assert definicion.datos_riesgo["cilindraje_cc"] == RangoNumerico(Decimal("50"), Decimal("1800"))
    assert definicion.datos_riesgo["ciudad_circulacion"] == ValoresPermitidos(("bogota", "cali"))


def test_tipo_de_dato_desconocido_falla_al_cargar():
    fila = _fila_producto(datos=[DatoRiesgoFila(nombre="x", tipo="fecha")])

    with pytest.raises(ValueError, match="fecha"):
        a_definicion(fila)


def test_un_segundo_ramo_persistido_se_sirve_sin_cambiar_codigo():
    catalogo = CatalogoSQL(
        [a_definicion(_fila_producto()), a_definicion(_fila_producto(codigo="asistencia-viaje", moneda="USD"))]
    )

    assert catalogo.obtener("asistencia-viaje").moneda == "USD"
    assert catalogo.obtener("soat-motocicleta").moneda == "COP"
    assert catalogo.obtener("no-existe") is None
    assert [p.producto for p in catalogo.listar()] == ["soat-motocicleta", "asistencia-viaje"]
