from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Alcance = Literal["catalogo:leer", "originaciones:escribir", "cotizaciones:escribir", "cotizaciones:leer"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "api-socios"

    ms_cotizacion_url: str = "http://localhost:8000"
    ms_identidad_url: str = "http://localhost:8010"
    ms_perfilamiento_url: str = "http://localhost:8004"

    solventa_token_secret: str = ""

    cache_socios_s: float = 30.0

    timeout_nucleo_s: float = 1.0
    timeout_opcional_s: float = 0.3
