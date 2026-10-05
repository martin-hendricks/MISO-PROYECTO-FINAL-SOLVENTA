from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auditoria import registrar_rechazo
from .tokens import Identidad, TokenInvalido, ValidadorJWT

_ESTADO = "validador_jwt"
_bearer = HTTPBearer(auto_error=False)

NO_AUTORIZADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autorizado",
    headers={"WWW-Authenticate": "Bearer"},
)
PROHIBIDO = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acción no permitida")


def configurar_seguridad(app: FastAPI, validador: ValidadorJWT | None) -> None:
    setattr(app.state, _ESTADO, validador)


def _accion(request: Request) -> str:
    return f"{request.method} {request.url.path}"


def _correlacion(request: Request) -> str | None:
    return request.headers.get("x-correlation-id")


async def identidad_actual(
    request: Request,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Identidad:
    validador: ValidadorJWT | None = getattr(request.app.state, _ESTADO, None)
    if validador is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Seguridad no configurada")

    if credenciales is None:
        registrar_rechazo(accion=_accion(request), motivo="sin_token", correlacion=_correlacion(request))
        raise NO_AUTORIZADO
    try:
        identidad = validador.validar(credenciales.credentials)
    except TokenInvalido as exc:
        registrar_rechazo(accion=_accion(request), motivo=exc.motivo, correlacion=_correlacion(request))
        raise NO_AUTORIZADO from None

    request.state.identidad = identidad
    return identidad


def requiere_alcance(*alcances: str):
    requeridos = frozenset(alcances)

    async def verificar(
        request: Request, identidad: Annotated[Identidad, Depends(identidad_actual)]
    ) -> Identidad:
        if not requeridos <= identidad.alcances:
            registrar_rechazo(
                accion=_accion(request),
                motivo="alcance_insuficiente",
                usuario=identidad.sujeto,
                rol=identidad.rol,
                correlacion=_correlacion(request),
            )
            raise PROHIBIDO
        return identidad

    return verificar
