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

    # Doble del perfil de riesgo (HU-88): demora y fallo forzables por entorno
    # (DOBLE_PERFIL_RIESGO_LATENCIA_MS, DOBLE_PERFIL_RIESGO_FALLAR) para ejercitar la
    # degradación de HU-5 en el ambiente de integración.
    doble_perfil_riesgo_latencia_ms: int = 0
    doble_perfil_riesgo_fallar: bool = False

    # Vigencia de la oferta (HU-6/SOLV-99): sin valor numérico fijado por ninguna HU,
    # default razonable a confirmar con negocio.
    oferta_vigencia_minutos: int = 60

    # Aceptación (HU-12/SOLV-105): encadena la decisión de suscripción de HU-13.
    ms_suscripcion_url: str = "http://ms-suscripcion:8000"
    timeout_dependencias: float = 2.0
