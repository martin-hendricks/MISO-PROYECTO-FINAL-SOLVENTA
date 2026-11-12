from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-siniestros"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    db_pool_size: int = 10
    log_level: str = "INFO"

    # Evidencia de siniestros (N6). Sin bucket se usa un almacén en memoria (solo para
    # desarrollo): la evidencia se pierde al reiniciar. En EKS el bucket lo inyecta
    # infra/k8s/values/ms-siniestros.yaml (S3_EVIDENCIAS_BUCKET) y las credenciales vienen
    # por IRSA; en local se apunta a LocalStack (S3) con S3_ENDPOINT_URL + llaves.
    s3_evidencias_bucket: str = ""
    aws_region: str = "us-east-1"
    s3_endpoint_url: str | None = None
    # Host con el que el NAVEGADOR abre las URLs firmadas (en local, localhost:4566 en
    # vez del host interno de Docker). Vacío = mismo que s3_endpoint_url.
    s3_endpoint_publico: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_kms_key_id: str | None = None
    s3_crear_bucket: bool = False
    url_evidencia_expira_segundos: int = 300

    # Worker de evaluación asíncrona del aviso asistido.
    worker_evaluacion_habilitado: bool = True
    worker_intervalo_segundos: float = 2.0
