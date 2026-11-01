import os

import httpx
from fastapi import HTTPException

DETALLE_INCOMPLETA = "Respuesta del nucleo incompleta"
TIMEOUT_S = 2.0

SERVICIOS = {
    "ms-identidad": "MS_IDENTIDAD_URL",
    "ms-cotizacion": "MS_COTIZACION_URL",
    "ms-pagos": "MS_PAGOS_URL",
    "ms-polizas": "MS_POLIZAS_URL",
    "ms-perfilamiento": "MS_PERFILAMIENTO_URL",
    "ms-siniestros": "MS_SINIESTROS_URL",
    "ms-suscripcion": "MS_SUSCRIPCION_URL",
}


class ClienteNucleo:
    """Llama los mismos paths que bff-web. No habla con bff-web."""

    def __init__(self, urls: dict[str, str | None] | None = None) -> None:
        if urls is None:
            urls = {nombre: os.environ.get(variable) for nombre, variable in SERVICIOS.items()}
        self._urls = urls

    def autenticar(self, *, correo: str, contrasena: str) -> dict:
        return self._pedir(
            "ms-identidad",
            "POST",
            "/v1/usuarios/autenticacion",
            json={"email": correo, "password": contrasena},
        )

    def cotizar(
        self,
        *,
        idempotency_key: str,
        usuario_id: str,
        socio_id: str,
        consentimiento_id: str,
        producto: str,
        canal: str,
        datos_riesgo: dict,
    ) -> dict:
        return self._pedir(
            "ms-cotizacion",
            "POST",
            "/v1/cotizaciones",
            json={
                "usuario_id": usuario_id,
                "socio_id": socio_id,
                "consentimiento_id": consentimiento_id,
                "producto": producto,
                "canal": canal,
                "datos_riesgo": datos_riesgo,
            },
            cabeceras={"Idempotency-Key": idempotency_key},
        )

    def reconsultar(self, cotizacion_id: str) -> dict:
        return self._pedir("ms-cotizacion", "GET", f"/v1/cotizaciones/{cotizacion_id}")

    def reconsultar_por_oferta(self, oferta_id: str) -> dict:
        return self._pedir("ms-cotizacion", "GET", f"/v1/cotizaciones/por-oferta/{oferta_id}")

    def aceptar_oferta(
        self, *, cotizacion_id: str, idempotency_key: str, perfil_id: str, score: str
    ) -> dict:
        return self._pedir(
            "ms-cotizacion",
            "POST",
            f"/v1/cotizaciones/{cotizacion_id}/aceptacion",
            json={"perfil_id": perfil_id, "score": score},
            cabeceras={"Idempotency-Key": idempotency_key},
        )

    def cobrar_prima(
        self,
        *,
        solicitud_id: str,
        oferta_id: str,
        usuario_id: str,
        monto: str,
        token_medio_pago: str,
    ) -> dict:
        return self._pedir(
            "ms-pagos",
            "POST",
            "/v1/pagos/primas",
            json={
                "solicitud_id": solicitud_id,
                "oferta_id": oferta_id,
                "usuario_id": usuario_id,
                "monto": monto,
                "token_medio_pago": token_medio_pago,
            },
        )

    def emitir(
        self,
        *,
        solicitud_id: str,
        oferta_id: str,
        usuario_id: str,
        token_pago_confirmado: str,
        coberturas: list,
    ) -> dict:
        return self._pedir(
            "ms-polizas",
            "POST",
            "/v1/polizas",
            json={
                "solicitud_id": solicitud_id,
                "oferta_id": oferta_id,
                "usuario_id": usuario_id,
                "token_pago_confirmado": token_pago_confirmado,
                "coberturas": coberturas,
            },
        )

    def listar_polizas(self, *, usuario_id: str, limite: int) -> list:
        return self._pedir(
            "ms-polizas",
            "GET",
            "/v1/polizas",
            params={"usuario_id": usuario_id, "limite": limite},
        )

    def obtener_por_numero(self, numero: str) -> dict:
        return self._pedir("ms-polizas", "GET", f"/v1/polizas/numero/{numero}")

    def otorgar_consentimiento(self, cliente_id: str) -> dict:
        return self._pedir(
            "ms-perfilamiento",
            "POST",
            "/v1/consentimientos",
            json={"cliente_id": cliente_id},
        )

    def solicitar_oferta_hipotecario(self, *, idempotency_key: str, cliente_id: str) -> dict:
        return self._pedir(
            "ms-perfilamiento",
            "POST",
            "/v1/ofertas-hipotecario",
            json={"cliente_id": cliente_id},
            cabeceras={"Idempotency-Key": idempotency_key},
        )

    def _base(self, servicio: str) -> str:
        base = (self._urls.get(servicio) or "").strip().rstrip("/")
        if not base:
            raise HTTPException(status_code=503, detail=f"{SERVICIOS[servicio]} no configurado")
        return base

    def _pedir(
        self,
        servicio: str,
        metodo: str,
        ruta: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        cabeceras: dict | None = None,
    ):
        try:
            with httpx.Client(base_url=self._base(servicio), timeout=TIMEOUT_S) as http:
                respuesta = http.request(
                    metodo, ruta, json=json, params=params, headers=cabeceras or {}
                )
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail=f"{servicio} no disponible") from exc
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = None
        if respuesta.status_code == 404:
            raise HTTPException(status_code=404, detail="No existe")
        if respuesta.status_code in (401, 409, 422):
            if isinstance(cuerpo, dict) and "mensaje" in cuerpo:
                detalle = cuerpo["mensaje"]
            elif cuerpo is None:
                detalle = "Operación rechazada"
            else:
                detalle = cuerpo
            raise HTTPException(status_code=respuesta.status_code, detail=detalle)
        if respuesta.status_code >= 400:
            raise HTTPException(status_code=503, detail=f"{servicio} no disponible")
        if cuerpo is None:
            raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
        return cuerpo
