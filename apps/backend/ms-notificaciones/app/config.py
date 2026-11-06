from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-notificaciones"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    db_pool_size: int = 10
    log_level: str = "INFO"

    push_proveedor: str = "stub"
    push_stub_fallar: bool = False

    msk_bootstrap_brokers: str = ""
    msk_topic: str = "BusEventos"
    msk_consumer_group: str = "notificaciones-cg"
    msk_auth_mechanism: str = "AWS_MSK_IAM"
