from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "bff-arquetipo"

    ms_ejemplo_url: str = "http://localhost:8000"

    timeout_nucleo_s: float = 1.0
    timeout_opcional_s: float = 0.3
