from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..clients.base import RechazoDelNucleo
from ..clients.ms_identidad import ClienteMsIdentidad
from ..dependencies import ROLES, issue_pair, obtener_cliente_identidad, refresh_session, require_roles

router = APIRouter(prefix="/sesion", tags=["sesion"])

ClienteIdentidad = Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)]


class Ingreso(BaseModel):
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)
    rol: str | None = None


class Refresh(BaseModel):
    refreshToken: str = Field(min_length=1)


_DOMINIOS_CORPORATIVOS = ("@solventa.co", "@solventa.com")


def _es_cuenta_corporativa(correo: str) -> bool:
    return correo.lower().endswith(_DOMINIOS_CORPORATIVOS)


def _rol_asignado(correo: str) -> str:
    # Stub hasta que ms-identidad asigne el rol de la cuenta corporativa.
    return "operador" if correo.lower().startswith("operador") else "asesor"


@router.post("/ingreso")
async def ingreso(body: Ingreso, cliente_identidad: ClienteIdentidad) -> dict:
    corporativa = _es_cuenta_corporativa(body.correo)
    rol = body.rol if body.rol is not None else (_rol_asignado(body.correo) if corporativa else "cliente")
    if rol not in ROLES:
        raise HTTPException(status_code=400, detail="Rol no permitido")

    # El canal (/login vs /cms/login) pide un rol explicito segun a cual
    # portal pertenece -- cliente para el canal cliente, asesor/operador
    # para el back-office. ms-identidad no conoce roles todavia (ninguna
    # cuenta tiene rol propio persistido, ver comentario de _rol_asignado),
    # asi que esta es la unica barrera real contra que una cuenta
    # corporativa entre como cliente (o un cliente entre al back-office
    # pidiendo rol=asesor): se exige que lo pedido sea consistente con el
    # dominio del correo. Sin esto, cualquiera que entrara por /login con
    # una cuenta de asesor/operador quedaba autenticado como "cliente" sin
    # que nada lo rechazara -- la identidad era real, pero el rol no tenia
    # ninguna relacion con la cuenta.
    si_cliente_pedido_es_corporativa = rol == "cliente" and corporativa
    si_corporativo_pedido_no_es_corporativa = rol != "cliente" and not corporativa
    if si_cliente_pedido_es_corporativa or si_corporativo_pedido_no_es_corporativa:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    # ms-identidad confirma identidad (correo/contrasena); el rol sigue
    # siendo un concepto de aplicacion que ms-identidad no conoce. Si
    # ms-identidad rechaza (correo inexistente o contrasena incorrecta),
    # responde 401 igual que el stub anterior.
    try:
        await cliente_identidad.autenticar(email=body.correo, password=body.contrasena)
    except RechazoDelNucleo as exc:
        raise HTTPException(status_code=401, detail="Credenciales invalidas") from exc

    return issue_pair(body.correo, rol)


@router.post("/refresh")
def refresh(body: Refresh) -> dict:
    return refresh_session(body.refreshToken)


@router.post("/salida", dependencies=[Depends(require_roles(*ROLES))])
def salida() -> dict:
    return {"estado": "aceptada"}
