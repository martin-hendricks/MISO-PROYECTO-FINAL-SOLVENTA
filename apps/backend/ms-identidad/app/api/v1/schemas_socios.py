from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.socios import CredencialSocio, Socio

Alcance = Literal[
    "catalogo:leer",
    "originaciones:escribir",
    "cotizaciones:escribir",
    "cotizaciones:leer",
]


class CrearSocioEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=120)
    alcances: list[Alcance] = Field(min_length=1)


class ResolverSocioEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    huella_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class CredencialSalida(BaseModel):
    credencial_id: UUID
    creada_en: datetime
    revocada_en: datetime | None

    @classmethod
    def desde(cls, credencial: CredencialSocio) -> "CredencialSalida":
        return cls(
            credencial_id=credencial.credencial_id,
            creada_en=credencial.creada_en,
            revocada_en=credencial.revocada_en,
        )


class SocioSalida(BaseModel):
    socio_id: UUID
    nombre: str
    alcances: list[str]
    estado: str
    creado_en: datetime
    credenciales: list[CredencialSalida]

    @classmethod
    def desde(cls, socio: Socio) -> "SocioSalida":
        return cls(
            socio_id=socio.socio_id,
            nombre=socio.nombre,
            alcances=sorted(socio.alcances),
            estado=socio.estado.value,
            creado_en=socio.creado_en,
            credenciales=[CredencialSalida.desde(c) for c in socio.credenciales],
        )


class ListaSociosSalida(BaseModel):
    socios: list[SocioSalida]


class ClaveEmitidaSalida(BaseModel):
    credencial_id: UUID
    api_key: str


class SocioCreadoSalida(BaseModel):
    socio_id: UUID
    nombre: str
    alcances: list[str]
    estado: str
    creado_en: datetime
    credencial_id: UUID
    api_key: str


class SocioResueltoSalida(BaseModel):
    socio_id: UUID
    nombre: str
    alcances: list[str]
