from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Alcance = Literal["catalogo:leer", "originaciones:escribir"]
HuellaSha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class RegistroSocio(BaseModel):
    socio_id: UUID
    nombre: str = Field(min_length=1)
    alcances: frozenset[Alcance]
    api_keys_sha256: list[HuellaSha256] = Field(min_length=1)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "api-socios"

    ms_cotizacion_url: str = "http://localhost:8000"
    ms_identidad_url: str = "http://localhost:8010"
    ms_perfilamiento_url: str = "http://localhost:8004"

    solventa_token_secret: str = ""
    socio_servicio_uid: str = "00000000-0000-0000-0000-00000000500c"

    socios: list[RegistroSocio] = []

    timeout_nucleo_s: float = 1.0
    timeout_opcional_s: float = 0.3

    @model_validator(mode="after")
    def _socios_sin_duplicados(self) -> "Settings":
        ids = [s.socio_id for s in self.socios]
        if len(ids) != len(set(ids)):
            raise ValueError("socio_id duplicado en SOCIOS")
        huellas = [h for s in self.socios for h in s.api_keys_sha256]
        if len(huellas) != len(set(huellas)):
            raise ValueError("api_keys_sha256 repetida en SOCIOS")
        return self
