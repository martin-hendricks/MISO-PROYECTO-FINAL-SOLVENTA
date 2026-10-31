from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-perfilamiento"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    db_pool_size: int = 10
    log_level: str = "INFO"

    # Timeouts por adaptador (HU-54): viven en config, no en el Protocol, para que un
    # proveedor real (Open Finance / Open Data) no necesite conocer la política de
    # resiliencia de Solventa. Al expirar, el caso de uso degrada (HU-56) en vez de
    # colgar la originación.
    timeout_open_finance_ms: int = 400
    timeout_open_data_ms: int = 400

    # Dobles (HU-88): demora y fallo forzables por entorno en el ambiente de integración
    # (DOBLE_OPEN_FINANCE_LATENCIA_MS, DOBLE_OPEN_DATA_FALLAR, ...). En 0/False el doble
    # responde de inmediato, como hasta ahora.
    doble_open_finance_latencia_ms: int = 0
    doble_open_finance_fallar: bool = False
    doble_open_data_latencia_ms: int = 0
    doble_open_data_fallar: bool = False

    # Valores de respaldo (HU-56): constantes razonables e inventadas para fines
    # académicos, una por atributo stub. Se usan cuando el adaptador excede su timeout
    # o lanza una excepción.
    respaldo_nivel_ingresos_estimado: Decimal = Decimal("1.0")
    respaldo_score_comportamiento: Decimal = Decimal("0.5")
    respaldo_zona_riesgo: Decimal = Decimal("0.5")
    respaldo_antiguedad_documento: Decimal = Decimal("1.0")

    # Fórmula de oferta (HU-55): tarifa base ajustada por los 4 atributos propios de
    # Solventa, cada uno con un peso fijo y determinista. Documentada también en el
    # README del servicio. Son valores inventados para el proyecto académico, no una
    # tabla de rating real.
    tarifa_base: Decimal = Decimal("50000")
    peso_nivel_ingresos_estimado: Decimal = Decimal("-0.08")
    peso_score_comportamiento: Decimal = Decimal("-0.15")
    peso_zona_riesgo: Decimal = Decimal("0.20")
    peso_antiguedad_documento: Decimal = Decimal("-0.05")
