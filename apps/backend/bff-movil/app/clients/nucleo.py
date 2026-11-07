import json
import os
from contextvars import ContextVar

import httpx

token_saliente: ContextVar[str | None] = ContextVar("token_saliente", default=None)
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
    "notificaciones": "MS_NOTIFICACIONES_URL",
}


class ClienteNucleo:
    """Llama los mismos paths que bff-web. No habla con bff-web."""

    def __init__(self, urls: dict[str, str | None] | None = None) -> None:
        if urls is None:
            urls = {nombre: os.environ.get(variable) for nombre, variable in SERVICIOS.items()}
        self._urls = urls
        self._clientes: dict[str, httpx.Client] = {}

    def autenticar(self, *, correo: str, contrasena: str) -> dict:
        return self._pedir(
            "ms-identidad",
            "POST",
            "/v1/usuarios/autenticacion",
            json={"email": correo, "password": contrasena},
        )

    def crear_usuario(
        self,
        *,
        tipo_documento: str,
        numero_documento: str,
        email: str,
        password: str,
        nombre: str = "",
        apellidos: str = "",
        ingresos_mensuales: str | None = None,
        gastos_mensuales: str | None = None,
    ) -> dict:
        return self._pedir(
            "ms-identidad",
            "POST",
            "/v1/usuarios",
            json={
                "tipo_documento": tipo_documento,
                "numero_documento": numero_documento,
                "email": email,
                "password": password,
                "nombre": nombre,
                "apellidos": apellidos,
                "ingresos_mensuales": ingresos_mensuales,
                "gastos_mensuales": gastos_mensuales,
            },
        )

    def obtener_usuario(self, usuario_id: str) -> dict:
        return self._pedir("ms-identidad", "GET", f"/v1/usuarios/{usuario_id}")

    def actualizar_perfil(self, usuario_id: str, *, nombre: str, apellidos: str) -> dict:
        return self._pedir(
            "ms-identidad",
            "PATCH",
            f"/v1/usuarios/{usuario_id}/perfil",
            json={"nombre": nombre, "apellidos": apellidos},
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

    def listar_cotizaciones_usuario(self, *, usuario_id: str, tamano: int) -> dict:
        return self._pedir(
            "ms-cotizacion",
            "GET",
            f"/v1/cotizaciones/por-usuario/{usuario_id}",
            params={"tamano": tamano},
        )

    def reconsultar(self, cotizacion_id: str, usuario_id: str | None = None) -> dict:
        params = {"usuario_id": usuario_id} if usuario_id else None
        return self._pedir("ms-cotizacion", "GET", f"/v1/cotizaciones/{cotizacion_id}", params=params)

    def reconsultar_por_oferta(self, oferta_id: str) -> dict:
        return self._pedir("ms-cotizacion", "GET", f"/v1/cotizaciones/por-oferta/{oferta_id}")

    def aceptar_oferta(
        self,
        *,
        cotizacion_id: str,
        idempotency_key: str,
        perfil_id: str,
        score: str,
        usuario_id: str | None = None,
    ) -> dict:
        return self._pedir(
            "ms-cotizacion",
            "POST",
            f"/v1/cotizaciones/{cotizacion_id}/aceptacion",
            json={"perfil_id": perfil_id, "score": score},
            params={"usuario_id": usuario_id} if usuario_id else None,
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

    def polizas_por_vencer(self, *, usuario_id: str, dias: int = 30) -> list:
        return self._pedir(
            "ms-polizas",
            "GET",
            "/v1/polizas/por-vencer",
            params={"usuario_id": usuario_id, "dias": dias},
        )

    def guardar_preferencia(self, poliza_id: str, renovacion_automatica: bool, usuario_id: str) -> dict:
        return self._pedir(
            "ms-polizas",
            "PATCH",
            f"/v1/polizas/{poliza_id}/preferencias",
            params={"usuario_id": usuario_id},
            json={"renovacion_automatica": renovacion_automatica},
        )

    def obtener_por_numero(self, numero: str, usuario_id: str | None = None) -> dict:
        params = {"usuario_id": usuario_id} if usuario_id else None
        return self._pedir("ms-polizas", "GET", f"/v1/polizas/numero/{numero}", params=params)

    def listar_siniestros(self, *, usuario_id: str) -> list:
        cuerpo = self._pedir("ms-siniestros", "GET", "/v1/siniestros", params={"usuario_id": usuario_id})
        return cuerpo if isinstance(cuerpo, list) else []

    def registrar_aviso(
        self,
        *,
        usuario_id: str,
        datos: dict,
        archivos: list[tuple],
        idempotency_key: str,
    ) -> dict:
        return self._pedir(
            "ms-siniestros",
            "POST",
            "/v1/siniestros",
            data={"datos": json.dumps(datos)},
            # httpx espera (nombre de campo, archivo). Sin el nombre, el 3-tuple
            # (filename, bytes, content-type) revienta al armar el multipart.
            files=[("archivos", archivo) for archivo in archivos],
            cabeceras={"Idempotency-Key": idempotency_key},
        )

    def detalle_siniestro(self, siniestro_id: str, usuario_id: str) -> dict:
        return self._pedir(
            "ms-siniestros",
            "GET",
            f"/v1/siniestros/{siniestro_id}/detalle",
            params={"usuario_id": usuario_id},
        )

    def crear_siniestro(
        self, *, usuario_id: str, poliza: str, poliza_id: str, idempotency_key: str
    ) -> dict:
        return self._pedir(
            "ms-siniestros",
            "POST",
            "/v1/siniestros",
            json={"usuario_id": usuario_id, "poliza": poliza, "poliza_id": poliza_id},
            cabeceras={"Idempotency-Key": idempotency_key},
        )

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

    def registrar_dispositivo(self, *, plataforma: str, token: str) -> dict:
        """POST /v1/notificaciones/dispositivos: upsert por (usuario_id, token)
        -- notificaciones resuelve el usuario_id del JWT reenviado (`uid`),
        no de un parámetro explícito. Devuelve 201 (nuevo) o 200 (ya existía),
        ambos manejados igual por _pedir (solo falla en >=400)."""
        return self._pedir(
            "notificaciones",
            "POST",
            "/v1/notificaciones/dispositivos",
            json={"plataforma": plataforma, "token": token},
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
        data: dict | None = None,
        files: list | None = None,
    ):
        try:
            headers = dict(cabeceras or {})
            token = token_saliente.get()
            if token and "Authorization" not in headers:
                headers["Authorization"] = f"Bearer {token}"
            http = self._clientes.get(servicio)
            if http is None:
                http = httpx.Client(base_url=self._base(servicio), timeout=TIMEOUT_S)
                self._clientes[servicio] = http
            respuesta = http.request(
                metodo, ruta, json=json, params=params, headers=headers, data=data, files=files
            )
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail=f"{servicio} no disponible") from exc
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = None
        if respuesta.status_code == 404:
            raise HTTPException(status_code=404, detail="No existe")
        if respuesta.status_code in (401, 403, 409, 422):
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
