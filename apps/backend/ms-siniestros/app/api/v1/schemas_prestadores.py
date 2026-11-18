from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.prestadores import ConsultaPrestadores, ResultadoBusqueda
from app.domain.prestador import CIUDADES, RADIO_DEFECTO_KM, Prestador, PrestadorCercano


class PrestadorEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    tipo: str = Field(min_length=1)
    ramos: list[str] = Field(min_length=1)
    direccion: str = Field(min_length=1, max_length=200)
    ciudad: str
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
    ciudad: str | None = None
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
            prestadores=[PrestadorSalida.desde_cercano(fila) for fila in resultado.prestadores],
            conteos=resultado.conteos,
        )


class SiniestroPrestadoresSalida(BaseModel):
    siniestro: dict
    ramo_fijo: str | None
    sin_geoetiqueta: bool
    centro: CentroSalida | None
    radio_km: Decimal | None
    prestadores: list[PrestadorSalida]


def consulta_desde(
    lat: Decimal | None,
    lng: Decimal | None,
    ciudad: str | None,
    ramo: str | None,
    radio_km: Decimal | None,
    estado: str | None,
    limite: int,
) -> ConsultaPrestadores:
    if ciudad is not None and ciudad not in CIUDADES:
        from app.domain.errores import ReglaDeNegocioViolada

        raise ReglaDeNegocioViolada("ciudad_desconocida", f"La ciudad '{ciudad}' no existe")
    return ConsultaPrestadores(
        lat=lat,
        lng=lng,
        ciudad=ciudad,
        ramo=ramo,
        radio_km=RADIO_DEFECTO_KM if radio_km is None else radio_km,
        estado=estado,
        limite=limite,
    )
