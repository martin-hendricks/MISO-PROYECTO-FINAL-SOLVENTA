from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "api-socios"

    ms_cotizacion_url: str = "http://localhost:8000"
    ms_identidad_url: str = "http://localhost:8010"
    ms_perfilamiento_url: str = "http://localhost:8004"

    solventa_token_secret: str = ""
    socio_servicio_uid: str = "00000000-0000-0000-0000-00000000500c"

    socios_api_keys: str = ""
    """Credenciales de socios externos que llaman a este servicio: `socio_id:api_key` separados
    por coma. Ej. `aliado-banco:clave-secreta,aliado-retail:otra-clave`. Formato de prueba/local;
    en un ambiente real cada socio tendría su propia fila en un almacen de credenciales."""

    timeout_nucleo_s: float = 1.0
    timeout_opcional_s: float = 0.3

    def mapa_socios_api_keys(self) -> dict[str, str]:
        """api_key -> socio_id, a partir de `socios_api_keys`."""
        mapa: dict[str, str] = {}
        for par in self.socios_api_keys.split(","):
            par = par.strip()
            if not par or ":" not in par:
                continue
            socio_id, _, api_key = par.partition(":")
            socio_id, api_key = socio_id.strip(), api_key.strip()
            if socio_id and api_key:
                mapa[api_key] = socio_id
        return mapa
