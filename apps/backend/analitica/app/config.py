from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "analitica"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    db_pool_size: int = 10
    log_level: str = "INFO"

    msk_bootstrap_brokers: str = ""
    msk_topic: str = "BusEventos"
    msk_consumer_group: str = "analitica-cg"
    msk_auth_mechanism: str = "AWS_MSK_IAM"
    aws_region: str = ""
