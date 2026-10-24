from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "bff-web"

    ms_cotizacion_url: str = "http://localhost:8000"
    # ms-pagos y ms-polizas todavía no tienen Dockerfile ni Service en el
    # cluster (sus implementaciones viven en PRs abiertos, ver
    # app/clients/ms_pagos.py y app/clients/ms_polizas.py) -- estas URLs
    # quedan declaradas para cuando existan, igual que ya documentaba
    # infra/k8s/values/bff-web.yaml antes de esta integración.
    ms_pagos_url: str = "http://localhost:8080"
    ms_polizas_url: str = "http://localhost:8080"
    # ms-perfilamiento y ms-siniestros ya están mergeados a develop (ver
    # apps/backend/ms-perfilamiento y apps/backend/ms-siniestros) -- estas URLs
    # siguen el mismo patrón que las anteriores, apuntando al Service interno
    # del cluster en despliegues reales.
    ms_perfilamiento_url: str = "http://localhost:8080"
    ms_siniestros_url: str = "http://localhost:8080"

    timeout_nucleo_s: float = 2.0
