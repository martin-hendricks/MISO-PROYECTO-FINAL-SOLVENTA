from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.application import casos_uso
from app.dependencies import obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo

from .schemas import AutenticarEntrada, CrearUsuarioEntrada, ErrorSalida, UsuarioSalida

router = APIRouter(prefix="/v1/usuarios", tags=["usuarios"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
ERRORES = {401: {"model": ErrorSalida}, 409: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.post("", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def crear(entrada: CrearUsuarioEntrada, uow: Uow):
    """Alta de cuenta (SOLV-215). 409 si el correo o el documento ya existen."""
    usuario = await casos_uso.crear_usuario(
        uow,
        tipo_documento=entrada.tipo_documento,
        numero_documento=entrada.numero_documento,
        email=entrada.email,
        password_plano=entrada.password,
    )
    return UsuarioSalida.desde(usuario)


@router.post("/autenticacion", response_model=UsuarioSalida, responses=ERRORES)
async def autenticacion(entrada: AutenticarEntrada, uow: Uow):
    """Valida credenciales (SOLV-215). 401 indistinguible si el correo no
    existe o si la contraseña no coincide. No emite JWT: eso es
    responsabilidad de bff-web (issue_pair) una vez recibe este 200."""
    usuario = await casos_uso.autenticar_usuario(uow, email=entrada.email, password_plano=entrada.password)
    return UsuarioSalida.desde(usuario)
