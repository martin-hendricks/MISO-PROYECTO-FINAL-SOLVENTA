from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-parametrico"
    log_level: str = "INFO"

    # TopicoTelemetria. Vacío = publicador en memoria (solo pruebas y desarrollo sin bus).
    msk_bootstrap_brokers: str = ""
    msk_topic: str = "TopicoTelemetria"
    # AWS_MSK_IAM en EKS (SASL/IAM con IRSA); PLAINTEXT para el Kafka local de docker-compose.
    msk_auth_mechanism: str = "AWS_MSK_IAM"
    aws_region: str | None = None

    # Contrapresión: publicaciones simultáneas por réplica. Por encima se responde 429
    # con Retry-After en vez de encolar en memoria y caer por OOM durante el pico.
    max_publicaciones_en_vuelo: int = 500
    timeout_publicacion_segundos: float = 5.0
    reintentar_despues_segundos: int = 2

    # Credenciales del proveedor de telemetría. En EKS llegan del secreto
    # solventa-minimo-telemetria_iot-credentials con las claves clientId/clientSecret
    # (infra/k8s/values/ms-parametrico.yaml), por eso se aceptan ambos nombres.
    telemetria_client_id: str = Field("", validation_alias=AliasChoices("TELEMETRIA_CLIENT_ID", "clientId"))
    telemetria_client_secret: str = Field(
        "", validation_alias=AliasChoices("TELEMETRIA_CLIENT_SECRET", "clientSecret")
    )
