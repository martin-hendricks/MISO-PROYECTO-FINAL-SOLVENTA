from decimal import Decimal

import pytest

from app.application import casos_uso
from app.domain.catalogo import Cobertura, DefinicionProducto, RangoNumerico, UnidadLimite
from app.domain.errores import NoEncontrado, ProductoNoEncontrado

from .dobles import SOAT_MOTOCICLETA, CatalogoEnMemoria


def test_consultar_el_producto_vigente(catalogo):
    producto = casos_uso.consultar_producto(catalogo, "soat-motocicleta")

    assert producto.moneda == "COP"
    assert [(c.codigo, c.limite, c.unidad_limite) for c in producto.coberturas] == [
        ("gastos_medicos", Decimal("800"), UnidadLimite.SMLDV),
        ("incapacidad_permanente", Decimal("180"), UnidadLimite.SMLDV),
        ("muerte", Decimal("750"), UnidadLimite.SMLDV),
        ("gastos_transporte", Decimal("10"), UnidadLimite.SMLDV),
    ]
    assert {nombre: dato.describir_rango() for nombre, dato in producto.datos_riesgo.items()} == {
        "cilindraje_cc": "entre 50 y 1800",
        "modelo_anio": "entre 2000 y 2026",
        "ciudad_circulacion": "uno de: bogota, medellin, cali, barranquilla, bucaramanga",
    }


def test_producto_inexistente(catalogo):
    with pytest.raises(ProductoNoEncontrado) as exc:
        casos_uso.consultar_producto(catalogo, "soat-automovil")

    assert isinstance(exc.value, NoEncontrado)
    assert exc.value.codigo == "producto_no_encontrado"
    assert exc.value.producto == "soat-automovil"


def test_el_catalogo_no_expone_alta_ni_edicion(catalogo):
    publicas = {nombre for nombre in dir(catalogo) if not nombre.startswith("_")}
    assert publicas == {"obtener", "listar"}


def test_un_segundo_ramo_es_dato_no_codigo():
    viaje = DefinicionProducto(
        producto="asistencia-viaje",
        nombre="Asistencia en viaje",
        moneda="USD",
        coberturas=(Cobertura("gastos_medicos", "Gastos médicos", Decimal("50000"), UnidadLimite.MONEDA),),
        datos_riesgo={"dias_viaje": RangoNumerico(Decimal("1"), Decimal("90"))},
    )
    catalogo = CatalogoEnMemoria(SOAT_MOTOCICLETA, viaje)

    assert casos_uso.consultar_producto(catalogo, "asistencia-viaje").moneda == "USD"
    assert casos_uso.consultar_producto(catalogo, "soat-motocicleta").moneda == "COP"
