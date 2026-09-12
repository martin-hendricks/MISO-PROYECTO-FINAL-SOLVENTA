from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    read_strategy: str = "A"
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    provider_url: str = "http://toxiproxy:9001"
    dependency_budget_ms: int = 120
    hard_timeout_ms: int = 700
    circuit_breaker_policy: str = "count"  # "count" | "rate"
    circuit_breaker_threshold: int = 5
    cache_ttl_seconds: int = 86400


settings = Settings()
