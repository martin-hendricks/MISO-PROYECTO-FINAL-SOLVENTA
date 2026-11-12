from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "outbox-relay"
    log_level: str = "INFO"

    # Una DATABASE_URL por esquema productor (ver ESQUEMAS_PERMITIDOS en
    # app/application/relay.py). ms_cotizacion/ms_suscripcion/ms_pagos/
    # ms_perfilamiento viven en DBCompartida (mismo secreto, misma URL salvo
    # que se separen a futuro); ms_polizas y ms_siniestros tienen su propio
    # RDS (infra/terraform/modules/secrets/main.tf: polizas_db, siniestros_db
    # son secretos independientes de compartida_db) -- por eso son 6
    # variables y no una sola, aunque varias terminen con el mismo valor.
    # Vacía = esa fuente no se arma en main.py (permite desplegar con un
    # subconjunto configurado sin fallar por las que faltan).
    database_url_ms_cotizacion: str = ""
    database_url_ms_suscripcion: str = ""
    database_url_ms_pagos: str = ""
    database_url_ms_perfilamiento: str = ""
    database_url_ms_polizas: str = ""
    database_url_ms_siniestros: str = ""

    lote: int = 100
    intervalo_segundos: float = 5.0

    msk_bootstrap_brokers: str = ""
    msk_topic: str = "BusEventos"
    aws_region: str = ""
