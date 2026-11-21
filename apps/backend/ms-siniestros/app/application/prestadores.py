"""Casos de uso del catálogo de prestadores. La distancia, el radio, el área y el alcance viven aquí."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.errores import CentroRequerido, CiudadDesconocida, NoEncontrado, RamoDesconocido
from app.domain.prestador import (
    AREA_LIMITE,
    PAIS_DEFECTO,
    RADIO_DEFECTO_KM,
    RAMOS_PRESTADOR,
    AreaVisible,
    Centro,
    CiudadPrestador,
    Prestador,
    PrestadorCercano,
    exigir_pais,
)
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import Llamante, dueno_visible, exigir_rol

ESTADOS = ("activo", "inactivo")


@dataclass(frozen=True)
class ConsultaPrestadores:
    lat: Decimal | None = None
    lng: Decimal | None = None
    ciudad: str | None = None
    pais: str | None = None
    ramo: str | None = None
    radio_km: Decimal = RADIO_DEFECTO_KM
    estado: str | None = None
    limite: int = 50
    area: AreaVisible | None = None


@dataclass(frozen=True)
class ResultadoBusqueda:
    centro: Centro | None
    radio_km: Decimal | None
    prestadores: list[PrestadorCercano]
    conteos: dict[str, int] | None
    truncado: bool = False


def _ramo(ramo: str | None) -> str | None:
    if ramo is None:
        return None
    if ramo not in RAMOS_PRESTADOR:
        raise RamoDesconocido(ramo)
    return ramo


def _estados(llamante: Llamante, estado: str | None) -> tuple[str, ...]:
    if llamante.rol == "cliente":
        return ("activo",)
    if estado is None:
        return ESTADOS
    return (estado,)


def _redondear(filas: list[PrestadorCercano]) -> list[PrestadorCercano]:
    return [
        PrestadorCercano(
            fila.prestador,
            None if fila.distancia_km is None else round(float(fila.distancia_km), 1),
        )
        for fila in filas
    ]


async def _en_area(uow, area: AreaVisible, ramo, estados, limite: int, origen) -> tuple[list[PrestadorCercano], bool]:
    tope = min(limite, AREA_LIMITE)
    filas = await uow.prestadores.en_area(area, ramo, estados, tope + 1, origen)
    return filas[:tope], len(filas) > tope


async def _ciudad_del_catalogo(uow, pais: str, nombre: str) -> CiudadPrestador:
    ciudad = await uow.prestadores.ciudad(pais, nombre)
    if ciudad is None:
        raise CiudadDesconocida(pais, nombre)
    return ciudad


async def buscar(uow_fabrica: FabricaUnidadDeTrabajo, llamante: Llamante, consulta: ConsultaPrestadores) -> ResultadoBusqueda:
    ramo = _ramo(consulta.ramo)
    estados = _estados(llamante, consulta.estado)
    personal = llamante.rol in ("asesor", "operador")
    pais = exigir_pais(consulta.pais or PAIS_DEFECTO)
    hay_origen = consulta.lat is not None and consulta.lng is not None
    truncado = False
    async with uow_fabrica() as uow:
        if consulta.area is not None:
            origen = (consulta.lat, consulta.lng) if hay_origen else None
            filas, truncado = await _en_area(uow, consulta.area, ramo, estados, consulta.limite, origen)
            centro = Centro(consulta.lat, consulta.lng, "posicion") if hay_origen else None
            radio = None
        elif hay_origen:
            filas = await uow.prestadores.cercanos(
                consulta.lat,
                consulta.lng,
                consulta.radio_km,
                ramo,
                estados,
                consulta.limite,
                consulta.ciudad,
                consulta.pais,
            )
            centro = Centro(consulta.lat, consulta.lng, "posicion")
            radio = consulta.radio_km
        elif consulta.ciudad is not None:
            ciudad = await _ciudad_del_catalogo(uow, pais, consulta.ciudad)
            filas = await uow.prestadores.por_ciudad(pais, ciudad.nombre, ramo, estados, consulta.limite)
            centro = Centro(ciudad.lat, ciudad.lng, "ciudad")
            radio = None
        elif personal:
            planos = await uow.prestadores.listar(ramo, pais, None, estados)
            filas = [PrestadorCercano(p, None) for p in planos]
            catalogo = await uow.prestadores.ciudades(pais, solo_activos=False)
            centro = Centro(catalogo[0][0].lat, catalogo[0][0].lng, "ciudad") if catalogo else None
            radio = None
        else:
            raise CentroRequerido()
        conteos = await uow.prestadores.conteos_por_ciudad(pais) if personal else None
    return ResultadoBusqueda(centro, radio, _redondear(filas), conteos, truncado)


async def ciudades(
    uow_fabrica: FabricaUnidadDeTrabajo, llamante: Llamante, pais: str, con_prestadores: bool = True
) -> list[tuple[CiudadPrestador, int]]:
    exigir_pais(pais)
    solo_con_activos = con_prestadores or llamante.rol == "cliente"
    async with uow_fabrica() as uow:
        filas = await uow.prestadores.ciudades(pais, solo_activos=solo_con_activos)
    if solo_con_activos:
        return [(ciudad, total) for ciudad, total in filas if total > 0]
    return filas


async def obtener(uow_fabrica: FabricaUnidadDeTrabajo, llamante: Llamante, prestador_id: str) -> Prestador:
    async with uow_fabrica() as uow:
        prestador = await uow.prestadores.obtener(prestador_id)
    if prestador is None or (llamante.rol == "cliente" and prestador.estado != "activo"):
        raise NoEncontrado("No existe")
    return prestador


async def buscar_por_siniestro(
    uow_fabrica: FabricaUnidadDeTrabajo,
    llamante: Llamante,
    siniestro_id,
    radio_km: Decimal,
    limite: int,
    area: AreaVisible | None = None,
) -> dict:
    dueno = dueno_visible(llamante, None)
    async with uow_fabrica() as uow:
        siniestro = await uow.siniestros.obtener(siniestro_id)
        if siniestro is None or (dueno is not None and siniestro.usuario_id != dueno):
            raise NoEncontrado("No existe")
        ramo = siniestro.poliza.ramo if siniestro.poliza else None
        if ramo is not None and ramo not in RAMOS_PRESTADOR:
            ramo = None
        if siniestro.geo is None:
            return {
                "siniestro": siniestro,
                "ramo_fijo": ramo,
                "sin_geoetiqueta": True,
                "centro": None,
                "radio_km": None,
                "truncado": False,
                "prestadores": [],
            }
        truncado = False
        if area is not None:
            filas, truncado = await _en_area(
                uow, area, ramo, ("activo",), limite, (siniestro.geo.lat, siniestro.geo.lng)
            )
            radio = None
        else:
            filas = await uow.prestadores.cercanos(
                siniestro.geo.lat, siniestro.geo.lng, radio_km, ramo, ("activo",), limite
            )
            radio = radio_km
        return {
            "siniestro": siniestro,
            "ramo_fijo": ramo,
            "sin_geoetiqueta": False,
            "centro": Centro(siniestro.geo.lat, siniestro.geo.lng, "siniestro"),
            "radio_km": radio,
            "truncado": truncado,
            "prestadores": _redondear(filas),
        }


async def crear(uow_fabrica: FabricaUnidadDeTrabajo, llamante: Llamante, datos: dict) -> Prestador:
    exigir_rol(llamante, "operador")
    prestador = Prestador.crear(actor=llamante.sub, **datos)
    async with uow_fabrica() as uow:
        await _ciudad_del_catalogo(uow, prestador.pais, prestador.ciudad)
        await uow.prestadores.guardar(prestador)
        await uow.confirmar()
    return prestador


async def editar(uow_fabrica: FabricaUnidadDeTrabajo, llamante: Llamante, prestador_id: str, datos: dict) -> Prestador:
    exigir_rol(llamante, "operador")
    async with uow_fabrica() as uow:
        actual = await uow.prestadores.obtener(prestador_id)
        if actual is None:
            raise NoEncontrado("No existe")
        nuevo = actual.editar(actor=llamante.sub, **datos)
        if (nuevo.pais, nuevo.ciudad) != (actual.pais, actual.ciudad):
            await _ciudad_del_catalogo(uow, nuevo.pais, nuevo.ciudad)
        await uow.prestadores.guardar(nuevo)
        await uow.confirmar()
    return nuevo


async def cambiar_estado(uow_fabrica: FabricaUnidadDeTrabajo, llamante: Llamante, prestador_id: str, estado: str) -> Prestador:
    exigir_rol(llamante, "operador")
    async with uow_fabrica() as uow:
        actual = await uow.prestadores.obtener(prestador_id)
        if actual is None:
            raise NoEncontrado("No existe")
        nuevo = actual.cambiar_estado(estado, llamante.sub)
        await uow.prestadores.guardar(nuevo)
        await uow.confirmar()
    return nuevo
