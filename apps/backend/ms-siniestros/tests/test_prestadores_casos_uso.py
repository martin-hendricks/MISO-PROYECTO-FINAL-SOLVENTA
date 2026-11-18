from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application import prestadores as casos
from app.domain.errores import CentroRequerido, NoEncontrado
from app.domain.modelos import EstadoSiniestro, Geo, Siniestro, SnapshotPoliza, TipoSiniestro
from app.domain.prestador import Prestador
from app.seguridad import Llamante

from .dobles import AlmacenEnMemoria, UnidadDeTrabajoEnMemoria

AHORA = datetime(2026, 11, 17, tzinfo=timezone.utc)
CLIENTE = Llamante(uid=uuid4(), rol="cliente", sub="a@solventa.co")
OPERADOR = Llamante(uid=uuid4(), rol="operador", sub="op@solventa.co")
ASESOR = Llamante(uid=uuid4(), rol="asesor", sub="as@solventa.co")


def fabrica(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


def prestador(**cambios) -> Prestador:
    datos = dict(
        nombre="Taller Chapinero",
        tipo="taller-motos",
        ramos=frozenset({"soat-motocicleta"}),
        direccion="Cra 13",
        ciudad="Bogotá",
        barrio="Chapinero",
        lat=Decimal("4.635500"),
        lng=Decimal("-74.065500"),
        telefono="601",
        horario="Lun",
        actor="semilla",
        ahora=AHORA,
    )
    datos.update(cambios)
    estado = datos.pop("estado", "activo")
    creado = Prestador.crear(**datos)
    if estado == "inactivo":
        return creado.cambiar_estado("inactivo", "semilla", AHORA)
    return creado


@pytest.mark.asyncio
async def test_cerca_de_mi_filtra_ordena_y_oculta_inactivos():
    almacen = AlmacenEnMemoria()
    cerca = prestador(nombre="Cerca")
    lejos = prestador(nombre="Lejos", lat=Decimal("6.244200"), lng=Decimal("-75.581200"), ciudad="Medellín")
    inactivo = prestador(nombre="Cerrado", estado="inactivo")
    almacen.prestadores = {p.id: p for p in (cerca, lejos, inactivo)}
    resultado = await casos.buscar(
        fabrica(almacen),
        CLIENTE,
        casos.ConsultaPrestadores(lat=Decimal("4.643200"), lng=Decimal("-74.063100"), ramo="soat-motocicleta"),
    )
    assert [fila.prestador.nombre for fila in resultado.prestadores] == ["Cerca"]
    assert resultado.prestadores[0].distancia_km is not None
    assert resultado.conteos is None
    assert resultado.centro.origen == "posicion"


@pytest.mark.asyncio
async def test_ciudad_sin_distancia_y_centro_requerido():
    almacen = AlmacenEnMemoria()
    medellin = prestador(nombre="Laureles", ciudad="Medellín", lat=Decimal("6.244800"), lng=Decimal("-75.591200"))
    almacen.prestadores[medellin.id] = medellin
    resultado = await casos.buscar(fabrica(almacen), CLIENTE, casos.ConsultaPrestadores(ciudad="Medellín"))
    assert resultado.prestadores[0].distancia_km is None
    assert resultado.centro.origen == "ciudad"
    with pytest.raises(CentroRequerido):
        await casos.buscar(fabrica(almacen), CLIENTE, casos.ConsultaPrestadores())


@pytest.mark.asyncio
async def test_conteos_para_backoffice():
    almacen = AlmacenEnMemoria()
    bogota = prestador()
    almacen.prestadores[bogota.id] = bogota
    resultado = await casos.buscar(fabrica(almacen), ASESOR, casos.ConsultaPrestadores())
    assert resultado.conteos["Bogotá"] == 1
    assert resultado.conteos["Chía"] == 0


@pytest.mark.asyncio
async def test_alta_edicion_estado_y_siniestro():
    almacen = AlmacenEnMemoria()
    creado = await casos.crear(
        fabrica(almacen),
        OPERADOR,
        dict(
            nombre="Nuevo",
            tipo="grua",
            ramos=frozenset({"soat-motocicleta"}),
            direccion="Cll 1",
            ciudad="Bogotá",
            barrio="Bosa",
            lat=Decimal("4.61"),
            lng=Decimal("-74.18"),
            telefono="601",
            horario="24 horas",
        ),
    )
    assert creado.estado == "activo"
    editado = await casos.editar(fabrica(almacen), OPERADOR, creado.id, {"ramos": frozenset({"viaje"})})
    assert editado.ramos == frozenset({"viaje"})
    inactivo = await casos.cambiar_estado(fabrica(almacen), OPERADOR, creado.id, "inactivo")
    assert inactivo.estado == "inactivo"
    with pytest.raises(NoEncontrado):
        await casos.obtener(fabrica(almacen), CLIENTE, creado.id)
    await casos.cambiar_estado(fabrica(almacen), OPERADOR, creado.id, "activo")
    visible = await casos.obtener(fabrica(almacen), CLIENTE, creado.id)
    assert visible.estado == "activo"

    dueno = CLIENTE.uid
    con_geo = Siniestro(
        id=uuid4(),
        evento_id=None,
        estado=EstadoSiniestro.RECIBIDO,
        historial=[],
        creado_en=AHORA,
        tipo=TipoSiniestro.ASISTIDO,
        numero="SIN-1988",
        usuario_id=dueno,
        poliza=SnapshotPoliza(uuid4(), "POL-1", "soat-motocicleta", "vigente", date(2026, 1, 1), date(2026, 12, 31)),
        geo=Geo(Decimal("4.635500"), Decimal("-74.065500")),
    )
    almacen.siniestros[con_geo.id] = con_geo
    activo = prestador(nombre="Al lado", ramos=frozenset({"soat-motocicleta"}))
    almacen.prestadores[activo.id] = activo
    cerca = await casos.buscar_por_siniestro(fabrica(almacen), CLIENTE, con_geo.id, Decimal("10"), 50)
    assert cerca["ramo_fijo"] == "soat-motocicleta"
    assert cerca["sin_geoetiqueta"] is False
    assert cerca["prestadores"]

    sin_geo = Siniestro(
        id=uuid4(),
        evento_id=None,
        estado=EstadoSiniestro.RECIBIDO,
        historial=[],
        creado_en=AHORA,
        tipo=TipoSiniestro.ASISTIDO,
        numero="SIN-1",
        usuario_id=dueno,
    )
    almacen.siniestros[sin_geo.id] = sin_geo
    vacio = await casos.buscar_por_siniestro(fabrica(almacen), CLIENTE, sin_geo.id, Decimal("10"), 50)
    assert vacio["sin_geoetiqueta"] is True
    assert vacio["prestadores"] == []
    with pytest.raises(NoEncontrado):
        await casos.buscar_por_siniestro(fabrica(almacen), Llamante(uuid4(), "cliente", "b@solventa.co"), con_geo.id, Decimal("10"), 50)
