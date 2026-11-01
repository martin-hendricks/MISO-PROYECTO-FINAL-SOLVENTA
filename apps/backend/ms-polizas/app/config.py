from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-polizas"
    # Escritura: siempre contra el writer endpoint de DBPolizas.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    # Lectura: EC-LAT-10 (p95 <= 150 ms) exige leer de la réplica ACTIVA de
    # DBPolizas, no del writer. Por defecto apunta al mismo valor que
    # database_url -- separarla de verdad es un cambio de infraestructura
    # (apuntar esta variable al reader endpoint real de rds_polizas), no de
    # código: el motor de lectura ya está separado aquí para no necesitar
    # otro cambio de código cuando esa infraestructura exista.
    database_url_read: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    db_pool_size: int = 10
    log_level: str = "INFO"
    ms_suscripcion_url: str = "http://localhost:8081"
    ms_pagos_url: str = "http://localhost:8082"
    timeout_dependencias: float = 2.0
    # HU-17: resultado fijo del stub de firma electrónica (`ok` | `no`).
    firma_stub_resultado: str = "ok"
