from decimal import Decimal

from app.domain.catalogo import (
    Booleano,
    Cobertura,
    DefinicionProducto,
    RangoNumerico,
    TextoLibre,
    UnidadLimite,
)


def test_texto_libre_rechaza_vacio_y_no_texto():
    dato = TextoLibre()
    assert dato.valido("Pixel")
    assert not dato.valido("  ")
    assert not dato.valido(1)
    assert dato.describir_rango() == "texto no vacío"


def test_booleano_solo_acepta_verdadero_o_falso():
    dato = Booleano()
    assert dato.valido(True)
    assert dato.valido(False)
    assert not dato.valido(1)
    assert not dato.valido("true")


def test_producto_disponible_exige_definicion_completa_y_regla():
    cobertura = (Cobertura("viaje", "Viaje", Decimal("1"), UnidadLimite.MONEDA),)
    incompleto = DefinicionProducto(
        producto="viaje",
        nombre="Viaje",
        descripcion="",
        moneda="COP",
        coberturas=cobertura,
        datos_riesgo={"duracion": RangoNumerico(Decimal("1"), Decimal("30"))},
    )
    assert not incompleto.disponible()
    listo = DefinicionProducto(
        producto="viaje",
        nombre="Viaje",
        descripcion="Cubre el viaje.",
        moneda="COP",
        coberturas=cobertura,
        datos_riesgo={"duracion": RangoNumerico(Decimal("1"), Decimal("30"))},
    )
    assert listo.disponible()
    assert not listo.disponible(tiene_regla=False)
