from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application import prestadores as casos
from app.domain.errores import CentroRequerido, CiudadDesconocida, NoEncontrado, PaisDesconocido
from app.domain.modelos import EstadoSiniestro, Geo, Siniestro, SnapshotPoliza, TipoSiniestro
from app.domain.prestador import AreaVisible, Prestador
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

    otro_ramo = prestador(nombre="Solo viaje", ramos=frozenset({"viaje"}), lat=Decimal("4.6360"))
    almacen.prestadores[otro_ramo.id] = otro_ramo
    segundo = prestador(nombre="Segundo", lat=Decimal("4.6500"))
    almacen.prestadores[segundo.id] = segundo
    en_area = await casos.buscar_por_siniestro(fabrica(almacen), CLIENTE, con_geo.id, Decimal("10"), 1, CHAPINERO)
    assert [fila.prestador.nombre for fila in en_area["prestadores"]] == ["Al lado"]
    assert en_area["prestadores"][0].distancia_km is not None
    assert en_area["radio_km"] is None
    assert en_area["truncado"] is True
    assert cerca["truncado"] is False


CHAPINERO = AreaVisible(Decimal("4.66"), Decimal("4.62"), Decimal("-74.05"), Decimal("-74.08"))


def _bogota_y_mas(almacen):
    filas = (
        prestador(nombre="B Chapinero"),
        prestador(nombre="A Chapinero", lat=Decimal("4.6488"), lng=Decimal("-74.0610")),
        prestador(nombre="Kennedy", lat=Decimal("4.6248"), lng=Decimal("-74.1480")),
        prestador(nombre="Cerrado", estado="inactivo"),
        prestador(nombre="Roma", pais="MX", ciudad="Ciudad de México", lat=Decimal("19.4180"), lng=Decimal("-99.1610")),
    )
    almacen.prestadores = {p.id: p for p in filas}


@pytest.mark.asyncio
async def test_area_con_y_sin_origen_y_truncado():
    almacen = AlmacenEnMemoria()
    _bogota_y_mas(almacen)
    con_origen = await casos.buscar(
        fabrica(almacen),
        CLIENTE,
        casos.ConsultaPrestadores(
            area=CHAPINERO, lat=Decimal("4.6355"), lng=Decimal("-74.0655"), ciudad="Medellín", radio_km=Decimal("1")
        ),
    )
    assert [f.prestador.nombre for f in con_origen.prestadores] == ["B Chapinero", "A Chapinero"]
    assert con_origen.prestadores[0].distancia_km == 0.0
    assert con_origen.truncado is False
    assert con_origen.centro.origen == "posicion"

    sin_origen = await casos.buscar(fabrica(almacen), CLIENTE, casos.ConsultaPrestadores(area=CHAPINERO, limite=1))
    assert [f.prestador.nombre for f in sin_origen.prestadores] == ["A Chapinero"]
    assert sin_origen.prestadores[0].distancia_km is None
    assert sin_origen.truncado is True
    assert sin_origen.centro is None


@pytest.mark.asyncio
async def test_ciudad_por_pais_y_catalogo():
    almacen = AlmacenEnMemoria()
    _bogota_y_mas(almacen)
    bogota = await casos.buscar(fabrica(almacen), CLIENTE, casos.ConsultaPrestadores(ciudad="Bogotá"))
    assert bogota.centro.lat == Decimal("4.6097")
    assert {f.prestador.pais for f in bogota.prestadores} == {"CO"}
    cdmx = await casos.buscar(fabrica(almacen), CLIENTE, casos.ConsultaPrestadores(ciudad="Ciudad de México", pais="MX"))
    assert [f.prestador.nombre for f in cdmx.prestadores] == ["Roma"]
    with pytest.raises(CiudadDesconocida):
        await casos.buscar(fabrica(almacen), CLIENTE, casos.ConsultaPrestadores(ciudad="Lima", pais="CO"))
    with pytest.raises(PaisDesconocido):
        await casos.buscar(fabrica(almacen), CLIENTE, casos.ConsultaPrestadores(ciudad="Lima", pais="AR"))


@pytest.mark.asyncio
async def test_ciudades_para_cliente_y_personal():
    almacen = AlmacenEnMemoria()
    _bogota_y_mas(almacen)
    cliente = await casos.ciudades(fabrica(almacen), CLIENTE, "CO", con_prestadores=False)
    assert [(c.nombre, total) for c, total in cliente] == [("Bogotá", 3)]
    personal = await casos.ciudades(fabrica(almacen), OPERADOR, "CO", con_prestadores=False)
    assert [(c.nombre, total) for c, total in personal] == [("Bogotá", 4), ("Medellín", 0), ("Chía", 0)]
    assert await casos.ciudades(fabrica(almacen), CLIENTE, "PE") == []
    conteos = await casos.buscar(fabrica(almacen), ASESOR, casos.ConsultaPrestadores(pais="PE"))
    assert conteos.conteos == {"Lima": 0, "Arequipa": 0, "Trujillo": 0}
    assert conteos.centro.lat == Decimal("-12.0464")


@pytest.mark.asyncio
async def test_alta_y_edicion_exigen_ciudad_del_pais():
    almacen = AlmacenEnMemoria()
    datos = dict(
        nombre="Nuevo",
        tipo="grua",
        ramos=frozenset({"viaje"}),
        direccion="Av Arequipa 1",
        ciudad="Lima",
        pais="CO",
        barrio="Miraflores",
        lat=Decimal("-12.12"),
        lng=Decimal("-77.03"),
        telefono="01",
        horario="24 horas",
    )
    with pytest.raises(CiudadDesconocida):
        await casos.crear(fabrica(almacen), OPERADOR, datos)
    creado = await casos.crear(fabrica(almacen), OPERADOR, {**datos, "pais": "PE"})
    assert creado.pais == "PE"
    with pytest.raises(CiudadDesconocida):
        await casos.editar(fabrica(almacen), OPERADOR, creado.id, {"ciudad": "Bogotá"})
    movido = await casos.editar(fabrica(almacen), OPERADOR, creado.id, {"ciudad": "Bogotá", "pais": "CO"})
    assert (movido.pais, movido.ciudad) == ("CO", "Bogotá")
