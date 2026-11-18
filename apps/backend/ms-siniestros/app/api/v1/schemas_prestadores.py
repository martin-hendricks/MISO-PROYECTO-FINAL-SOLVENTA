from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.application.prestadores import ConsultaPrestadores, ResultadoBusqueda
from app.domain.errores import ReglaDeNegocioViolada
from app.domain.prestador import AREA_LIMITE, RADIO_DEFECTO_KM, AreaVisible, CiudadPrestador, Prestador, PrestadorCercano

LIMITE_SIN_AREA = 100


class PrestadorEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    tipo: str = Field(min_length=1)
    ramos: list[str] = Field(min_length=1)
    direccion: str = Field(min_length=1, max_length=200)
    ciudad: str = Field(min_length=1, max_length=80)
    pais: str = Field(default="CO", min_length=2, max_length=2)
    barrio: str = Field(min_length=1, max_length=80)
    lat: Decimal
    lng: Decimal
    telefono: str = Field(min_length=1, max_length=40)
    horario: str = Field(min_length=1, max_length=80)

    def a_dominio(self) -> dict:
        datos = self.model_dump()
        datos["ramos"] = frozenset(datos["ramos"])
        return datos


class PrestadorEdicion(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    tipo: str | None = None
    ramos: list[str] | None = None
    direccion: str | None = Field(default=None, min_length=1, max_length=200)
    ciudad: str | None = Field(default=None, min_length=1, max_length=80)
    pais: str | None = Field(default=None, min_length=2, max_length=2)
    barrio: str | None = Field(default=None, min_length=1, max_length=80)
    lat: Decimal | None = None
    lng: Decimal | None = None
    telefono: str | None = Field(default=None, min_length=1, max_length=40)
    horario: str | None = Field(default=None, min_length=1, max_length=80)

    def a_dominio(self) -> dict:
        datos = self.model_dump(exclude_unset=True)
        if "ramos" in datos:
            datos["ramos"] = frozenset(datos["ramos"] or [])
        return datos


class EstadoEntrada(BaseModel):
    estado: str = Field(pattern="^(activo|inactivo)$")


class CentroSalida(BaseModel):
    lat: Decimal
    lng: Decimal
    origen: str


class PrestadorSalida(BaseModel):
    id: str
    nombre: str
    tipo: str
    ramos: list[str]
    direccion: str
    ciudad: str
    pais: str
    barrio: str
    lat: Decimal
    lng: Decimal
    telefono: str
    horario: str
    estado: str
    distancia_km: float | None = None
    actualizado_en: datetime

    @classmethod
    def desde(cls, prestador: Prestador, distancia_km: float | None = None) -> "PrestadorSalida":
        return cls(
            id=prestador.id,
            nombre=prestador.nombre,
            tipo=prestador.tipo,
            ramos=sorted(prestador.ramos),
            direccion=prestador.direccion,
            ciudad=prestador.ciudad,
            pais=prestador.pais,
            barrio=prestador.barrio,
            lat=prestador.lat,
            lng=prestador.lng,
            telefono=prestador.telefono,
            horario=prestador.horario,
            estado=prestador.estado,
            distancia_km=distancia_km,
            actualizado_en=prestador.actualizado_en,
        )

    @classmethod
    def desde_cercano(cls, cercano: PrestadorCercano) -> "PrestadorSalida":
        return cls.desde(cercano.prestador, cercano.distancia_km)


class BusquedaSalida(BaseModel):
    centro: CentroSalida | None
    radio_km: Decimal | None
    truncado: bool
    prestadores: list[PrestadorSalida]
    conteos: dict[str, int] | None

    @classmethod
    def desde(cls, resultado: ResultadoBusqueda) -> "BusquedaSalida":
        centro = None
        if resultado.centro is not None:
            centro = CentroSalida(lat=resultado.centro.lat, lng=resultado.centro.lng, origen=resultado.centro.origen)
        return cls(
            centro=centro,
            radio_km=resultado.radio_km,
            truncado=resultado.truncado,
            prestadores=[PrestadorSalida.desde_cercano(fila) for fila in resultado.prestadores],
            conteos=resultado.conteos,
        )


class SiniestroPrestadoresSalida(BaseModel):
    siniestro: dict
    ramo_fijo: str | None
    sin_geoetiqueta: bool
    centro: CentroSalida | None
    radio_km: Decimal | None
    truncado: bool
    prestadores: list[PrestadorSalida]


class CiudadSalida(BaseModel):
    nombre: str
    lat: Decimal
    lng: Decimal
    zoom: int
    orden: int
    prestadores: int


class CiudadesSalida(BaseModel):
    pais: str
    ciudades: list[CiudadSalida]

    @classmethod
    def desde(cls, pais: str, filas: list[tuple[CiudadPrestador, int]]) -> "CiudadesSalida":
        return cls(
            pais=pais,
            ciudades=[
                CiudadSalida(nombre=c.nombre, lat=c.lat, lng=c.lng, zoom=c.zoom, orden=c.orden, prestadores=total)
                for c, total in filas
            ],
        )


def limite_para(area: AreaVisible | None, limite: int | None) -> int:
    if area is None:
        if limite is not None and limite > LIMITE_SIN_AREA:
            raise ReglaDeNegocioViolada("limite_invalido", f"Sin área el límite es {LIMITE_SIN_AREA}")
        return limite or 50
    return limite or AREA_LIMITE


def consulta_desde(
    lat: Decimal | None,
    lng: Decimal | None,
    ciudad: str | None,
    ramo: str | None,
    radio_km: Decimal | None,
    estado: str | None,
    limite: int,
    pais: str | None = None,
    area: AreaVisible | None = None,
) -> ConsultaPrestadores:
    return ConsultaPrestadores(
        lat=lat,
        lng=lng,
        ciudad=ciudad,
        pais=pais,
        ramo=ramo,
        radio_km=RADIO_DEFECTO_KM if radio_km is None else radio_km,
        estado=estado,
        limite=limite,
        area=area,
    )
