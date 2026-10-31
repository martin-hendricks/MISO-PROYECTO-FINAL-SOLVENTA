from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-identidad"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    db_pool_size: int = 10
    log_level: str = "INFO"

    # Doble del proveedor KYC (HU-88): demora y caída forzables por entorno
    # (DOBLE_KYC_LATENCIA_MS, DOBLE_KYC_FALLAR) en el ambiente de integración.
    doble_kyc_latencia_ms: int = 0
    doble_kyc_fallar: bool = False
