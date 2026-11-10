from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta

import httpx
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import service_account

from app.domain.errores import ServicioExternoNoDisponible
from app.domain.modelos import DispositivoPush, Notificacion
from app.ports.push import EstadoEnvio, ResultadoEnvio

ALCANCE = "https://www.googleapis.com/auth/firebase.messaging"
_TOKEN_INVALIDO = frozenset({"UNREGISTERED", "INVALID_ARGUMENT"})


class EnviadorFCM:
    """Adaptador de FCM HTTP v1. Un POST por dispositivo, solo bloque `data`."""

    def __init__(self, credenciales_json: str, cliente: httpx.AsyncClient | None = None) -> None:
        try:
            info = json.loads(credenciales_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError("FCM_CREDENCIALES_JSON no es JSON") from exc
        if not isinstance(info, dict) or not info.get("project_id"):
            raise RuntimeError("FCM_CREDENCIALES_JSON no trae project_id")
        self._info = info
        self._proyecto = str(info["project_id"])
        self._cliente = cliente or httpx.AsyncClient(timeout=10)
        self._credenciales = None
        self._token = ""
        self._vence: datetime | None = None

    async def enviar(self, dispositivo: DispositivoPush, notificacion: Notificacion) -> str:
        resultado = await self._enviar_uno(dispositivo, notificacion)
        if resultado.estado == EstadoEnvio.ENVIADO and resultado.proveedor_id:
            return resultado.proveedor_id
        if resultado.estado == EstadoEnvio.TOKEN_INVALIDO:
            raise ServicioExternoNoDisponible("Token de FCM inválido")
        raise ServicioExternoNoDisponible("FCM no respondió")

    async def enviar_a_usuario(
        self, dispositivos: list[DispositivoPush], notificacion: Notificacion
    ) -> list[ResultadoEnvio]:
        return [await self._enviar_uno(dispositivo, notificacion) for dispositivo in dispositivos]

    async def _token_acceso(self) -> str:
        ahora = datetime.now(UTC)
        if self._token and self._vence and ahora < self._vence:
            return self._token

        def _renovar() -> tuple[str, datetime]:
            credenciales = service_account.Credentials.from_service_account_info(
                self._info, scopes=[ALCANCE]
            )
            credenciales.refresh(GoogleRequest())
            vence = credenciales.expiry
            if vence is None:
                vence = datetime.now(UTC) + timedelta(minutes=30)
            if vence.tzinfo is None:
                vence = vence.replace(tzinfo=UTC)
            return credenciales.token, vence - timedelta(minutes=5)

        self._token, self._vence = await asyncio.to_thread(_renovar)
        return self._token

    def _data(self, notificacion: Notificacion) -> dict[str, str]:
        datos = {
            "notificacionId": str(notificacion.notificacion_id),
            "tipo": notificacion.tipo,
            "titulo": notificacion.titulo,
            "cuerpo": notificacion.cuerpo,
            "destino": notificacion.destino or "inicio",
        }
        if notificacion.poliza:
            datos["poliza"] = notificacion.poliza
        return datos

    async def _enviar_uno(
        self, dispositivo: DispositivoPush, notificacion: Notificacion
    ) -> ResultadoEnvio:
        try:
            token = await self._token_acceso()
            respuesta = await self._cliente.post(
                f"https://fcm.googleapis.com/v1/projects/{self._proyecto}/messages:send",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "message": {
                        "fid": dispositivo.token,
                        "data": self._data(notificacion),
                        "android": {"priority": "HIGH"},
                    }
                },
            )
        except httpx.HTTPError:
            return ResultadoEnvio(dispositivo.dispositivo_id, EstadoEnvio.NO_DISPONIBLE.value)
        if respuesta.status_code == 200:
            nombre = respuesta.json().get("name")
            return ResultadoEnvio(
                dispositivo.dispositivo_id, EstadoEnvio.ENVIADO.value, str(nombre) if nombre else None
            )
        codigo = ""
        try:
            detalles = respuesta.json().get("error", {}).get("details", [])
            codigo = next(
                (d.get("errorCode", "") for d in detalles if isinstance(d, dict)),
                respuesta.json().get("error", {}).get("status", ""),
            )
        except ValueError:
            codigo = ""
        if respuesta.status_code in (400, 404) and codigo in _TOKEN_INVALIDO:
            return ResultadoEnvio(dispositivo.dispositivo_id, EstadoEnvio.TOKEN_INVALIDO.value)
        if respuesta.status_code == 400 and "registration" in respuesta.text.lower():
            return ResultadoEnvio(dispositivo.dispositivo_id, EstadoEnvio.TOKEN_INVALIDO.value)
        return ResultadoEnvio(dispositivo.dispositivo_id, EstadoEnvio.NO_DISPONIBLE.value)
