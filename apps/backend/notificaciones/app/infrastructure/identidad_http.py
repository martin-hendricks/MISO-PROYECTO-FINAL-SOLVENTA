from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import jwt

from app.domain.errores import ServicioExternoNoDisponible

VIGENCIA = timedelta(minutes=5)
SUB = "notificaciones"


def token_de_servicio(secreto: str, usuario_id: UUID, ahora: datetime | None = None) -> str:
    """Token de servicio con rol `servicio`: ms-identidad solo le abre el contacto del usuario."""
    if not secreto:
        raise ValueError("SOLVENTA_TOKEN_SECRET no configurado")
    emitido = ahora or datetime.now(UTC)
    return jwt.encode(
        {"sub": SUB, "uid": str(usuario_id), "rol": "servicio", "typ": "access", "exp": emitido + VIGENCIA},
        secreto,
        algorithm="HS256",
    )


class ResolutorIdentidadHTTP:
    """Resuelve el correo de un usuario consultando ms-identidad."""

    def __init__(self, base_url: str, secreto: str, http: httpx.AsyncClient | None = None) -> None:
        self._secreto = secreto
        self._http = http or httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=5.0)

    async def correo_de(self, usuario_id: UUID) -> str | None:
        try:
            respuesta = await self._http.get(
                f"/v1/usuarios/{usuario_id}/contacto",
                headers={"Authorization": f"Bearer {token_de_servicio(self._secreto, usuario_id)}"},
            )
        except httpx.HTTPError as exc:
            raise ServicioExternoNoDisponible("ms-identidad no disponible") from exc
        if respuesta.status_code == 404:
            return None
        if respuesta.status_code >= 400:
            raise ServicioExternoNoDisponible("ms-identidad rechazó la consulta de contacto")
        correo = respuesta.json().get("email")
        return correo.strip() if isinstance(correo, str) and correo.strip() else None
