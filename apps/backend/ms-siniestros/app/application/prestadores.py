"""Casos de uso del catálogo de prestadores. La distancia, el radio y el alcance viven aquí."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.errores import NoEncontrado, RamoDesconocido
from app.domain.prestador import CIUDADES, RADIO_DEFECTO_KM, RAMOS_PRESTADOR, Centro, Prestador, PrestadorCercano
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import Llamante, dueno_visible, exigir_rol

ESTADOS = ("activo", "inactivo")


@dataclass(frozen=True)
class ConsultaPrestadores:
    lat: Decimal | None = None
    lng: Decimal | None = None
    ciudad: str | None = None
    ramo: str | None = None
    radio_km: Decimal = RADIO_DEFECTO_KM
    estado: str | None = None
    limite: int = 50


@dataclass(frozen=True)
class ResultadoBusqueda:
    centro: Centro | None
    radio_km: Decimal | None
    prestadores: list[PrestadorCercano]
    conteos: dict[str, int] | None


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


async def buscar(uow_fabrica: FabricaUnidadDeTrabajo, llamante: Llamante, consulta: ConsultaPrestadores) -> ResultadoBusqueda:
    ramo = _ramo(consulta.ramo)
    estados = _estados(llamante, consulta.estado)
    personal = llamante.rol in ("asesor", "operador")
    async with uow_fabrica() as uow:
        if consulta.lat is not None and consulta.lng is not None:
            filas = await uow.prestadores.cercanos(
                consulta.lat, consulta.lng, consulta.radio_km, ramo, estados, consulta.limite, consulta.ciudad
            )
            centro = Centro(consulta.lat, consulta.lng, "posicion")
            radio = consulta.radio_km
        elif consulta.ciudad is not None:
            filas = await uow.prestadores.por_ciudad(consulta.ciudad, ramo, estados, consulta.limite)
            lat, lng = CIUDADES[consulta.ciudad]
            centro = Centro(lat, lng, "ciudad")
            radio = None
        elif personal:
            planos = await uow.prestadores.listar(ramo, None, estados)
            filas = [PrestadorCercano(p, None) for p in planos]
            lat, lng = CIUDADES["Bogotá"]
            centro = Centro(lat, lng, "ciudad")
            radio = None
        else:
            from app.domain.errores import CentroRequerido

            raise CentroRequerido()
        conteos = await uow.prestadores.conteos_por_ciudad() if personal else None
    return ResultadoBusqueda(centro, radio, _redondear(filas), conteos)


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
                "prestadores": [],
            }
        filas = await uow.prestadores.cercanos(
            siniestro.geo.lat, siniestro.geo.lng, radio_km, ramo, ("activo",), limite
        )
        return {
            "siniestro": siniestro,
            "ramo_fijo": ramo,
            "sin_geoetiqueta": False,
            "centro": Centro(siniestro.geo.lat, siniestro.geo.lng, "siniestro"),
            "radio_km": radio_km,
            "prestadores": _redondear(filas),
        }


async def crear(uow_fabrica: FabricaUnidadDeTrabajo, llamante: Llamante, datos: dict) -> Prestador:
    exigir_rol(llamante, "operador")
    prestador = Prestador.crear(actor=llamante.sub, **datos)
    async with uow_fabrica() as uow:
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
