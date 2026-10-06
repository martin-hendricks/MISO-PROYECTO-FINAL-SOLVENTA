from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-cotizacion"
    # PENDIENTE HU-6: vigencia de la oferta en firme. Valor de referencia.
    vigencia_oferta_minutos: int = 1440
    log_level: str = "INFO"
