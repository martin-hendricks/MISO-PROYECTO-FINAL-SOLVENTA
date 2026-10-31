from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-pagos"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    db_pool_size: int = 10
    log_level: str = "INFO"
    ms_suscripcion_url: str = "http://localhost:8081"
    timeout_dependencias: float = 2.0

    # Doble de la pasarela (HU-88): demora y caída forzables por entorno
    # (DOBLE_PASARELA_LATENCIA_MS, DOBLE_PASARELA_FALLAR) en el ambiente de integración.
    doble_pasarela_latencia_ms: int = 0
    doble_pasarela_fallar: bool = False
