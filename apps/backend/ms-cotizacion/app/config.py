from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-cotizacion"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    db_pool_size: int = 10
    log_level: str = "INFO"

    # Factor de riesgo (HU-5/SOLV-98): corte duro de EC-LAT-08 (700ms, 100% de los casos).
    # El timeout vive aquí, no en el Protocol del adaptador, para que un proveedor real
    # (Open Finance) no necesite conocer la política de resiliencia de Solventa.
    factor_riesgo_timeout_maximo_ms: int = 700
    factor_riesgo_valor_respaldo: Decimal = Decimal("1.0")
