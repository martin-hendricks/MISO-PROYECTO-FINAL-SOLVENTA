from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    read_strategy: str = "A"
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    db_pool_min: int = 10
    db_pool_max: int = 10
    cache_ttl_seconds: int = 30

settings = Settings()
