from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ms-identidad"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solventa"
    db_pool_size: int = 10
    log_level: str = "INFO"

    # Doble del proveedor KYC (HU-88): demora, caída y rechazo forzables por entorno
    # (DOBLE_KYC_LATENCIA_MS, DOBLE_KYC_FALLAR, DOBLE_KYC_DOCUMENTOS_RECHAZADOS) en el
    # ambiente de integración. Los documentos rechazados van separados por comas; vacío
    # (el default) aprueba todo documento.
    doble_kyc_latencia_ms: int = 0
    doble_kyc_fallar: bool = False
    doble_kyc_documentos_rechazados: str = ""

    # Resolución del campo "consentimiento" en el listado de clientes del
    # back-office (HU-141): dos servicios externos, ver app/infrastructure/
    # consentimiento_http.py y perfilamiento_http.py.
    #
    # ms-consentimiento (habeas data) todavía no existe en este árbol (otro
    # equipo lo construye en una rama/worktree aparte, contra este mismo
    # contrato ya coordinado): el default sigue el nombre de host/puerto
    # acordado para cuando se despliegue en docker-compose/k8s, aunque hoy
    # no haya ningún Service con ese nombre.
    ms_consentimiento_url: str = "http://ms-consentimiento:8080"
    # ms-perfilamiento ya existe y está desplegado (ver
    # apps/backend/docker-compose.yml): mismo host/puerto que usan
    # bff-web/bff-movil/api-socios para llegar a él.
    ms_perfilamiento_url: str = "http://ms-perfilamiento:8080"
    # Timeout corto a propósito: estas dos llamadas resuelven un campo
    # secundario (consentimiento) del listado de clientes, nunca deben
    # retener la respuesta del listado completo por mucho tiempo si el
    # servicio de turno está lento o caído -- ver degradación en los
    # adaptadores HTTP.
    timeout_consentimiento_s: float = 2.0

    def documentos_rechazados_kyc(self) -> list[str]:
        return [documento.strip() for documento in self.doble_kyc_documentos_rechazados.split(",") if documento.strip()]
