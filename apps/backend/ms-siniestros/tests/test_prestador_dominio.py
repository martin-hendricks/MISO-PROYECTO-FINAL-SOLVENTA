from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.domain.errores import AreaInvalida, CoordenadaFueraDeRango, PaisDesconocido, PrestadorSinRamo, RamoDesconocido
from app.domain.prestador import AreaVisible, Prestador

AHORA = datetime(2026, 11, 17, tzinfo=timezone.utc)


def _datos(**cambios):
    base = dict(
        nombre="Taller Moto Norte Usaquén",
        tipo="taller-motos",
        ramos=frozenset({"soat-motocicleta"}),
        direccion="Cll 134 #9-20",
        ciudad="Bogotá",
        barrio="Usaquén",
        lat=Decimal("4.710400"),
        lng=Decimal("-74.034000"),
        telefono="601 555 0111",
        horario="Lun–Sáb 7:00–19:00",
        actor="operador@solventa.co",
        ahora=AHORA,
    )
    base.update(cambios)
    return base


def test_crear_asigna_id_y_activo():
    prestador = Prestador.crear(**_datos())
    assert prestador.id.startswith("PRE-")
    assert len(prestador.id) == 14
    assert prestador.estado == "activo"
    assert prestador.creado_por == "operador@solventa.co"


def test_sin_ramo():
    with pytest.raises(PrestadorSinRamo):
        Prestador.crear(**_datos(ramos=frozenset()))


def test_ramo_desconocido():
    with pytest.raises(RamoDesconocido):
        Prestador.crear(**_datos(ramos=frozenset({"autos"})))


def test_coordenada_fuera_de_rango():
    with pytest.raises(CoordenadaFueraDeRango):
        Prestador.crear(**_datos(lat=Decimal("95")))


def test_editar_reemplaza_ramos_y_mismo_estado_no_cambia():
    prestador = Prestador.crear(**_datos())
    editado = prestador.editar(actor="operador@solventa.co", ramos=frozenset({"viaje", "soat-motocicleta"}), ahora=AHORA)
    assert editado.ramos == frozenset({"viaje", "soat-motocicleta"})
    igual = editado.cambiar_estado("activo", "operador@solventa.co")
    assert igual is editado
    inactivo = editado.cambiar_estado("inactivo", "operador@solventa.co", ahora=AHORA)
    assert inactivo.estado == "inactivo"


def test_pais_por_defecto_y_desconocido():
    assert Prestador.crear(**_datos()).pais == "CO"
    assert Prestador.crear(**_datos(pais="MX", ciudad="Guadalajara")).pais == "MX"
    with pytest.raises(PaisDesconocido):
        Prestador.crear(**_datos(pais="AR"))
    with pytest.raises(PaisDesconocido):
        Prestador.crear(**_datos()).editar(actor="op", pais="BR")


def test_area_visible():
    assert AreaVisible.desde(None, None, None, None) is None
    bogota = AreaVisible.desde(Decimal("4.8"), Decimal("4.5"), Decimal("-74.0"), Decimal("-74.2"))
    assert bogota.norte == Decimal("4.8")
    for bordes in (
        (Decimal("4.5"), Decimal("4.8"), Decimal("-74.0"), Decimal("-74.2")),
        (Decimal("4.8"), Decimal("4.5"), Decimal("-74.2"), Decimal("-74.0")),
        (Decimal("91"), Decimal("4.5"), Decimal("-74.0"), Decimal("-74.2")),
        (Decimal("4.8"), Decimal("4.5"), Decimal("181"), Decimal("-74.2")),
        (Decimal("4.8"), None, Decimal("-74.0"), Decimal("-74.2")),
    ):
        with pytest.raises(AreaInvalida):
            AreaVisible.desde(*bordes)
