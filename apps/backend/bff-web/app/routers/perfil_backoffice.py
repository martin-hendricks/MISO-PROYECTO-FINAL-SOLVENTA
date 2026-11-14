from typing import Annotated

from fastapi import APIRouter, Depends

from ..clients.ms_identidad import ClienteMsIdentidad
from ..dependencies import obtener_cliente_identidad, require_roles
from .cliente import contexto_canonico

router = APIRouter(prefix="/backoffice", tags=["backoffice"])


@router.get("/perfil")
async def leer_perfil(
    cliente_identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    usuario: Annotated[dict, Depends(require_roles("asesor", "operador"))],
) -> dict:
    """Perfil del asesor/operador logueado (nombre/apellidos reales, para
    mostrar sus iniciales en el shell del back-office) -- mismo patrón que
    GET /cliente/perfil, pero sin equivalente hasta ahora para este canal."""
    obtenido = await cliente_identidad.obtener(str(contexto_canonico(usuario).usuario_id))
    return {
        "usuarioId": str(obtenido["usuario_id"]),
        "correo": obtenido["email"],
        "nombre": obtenido.get("nombre") or "",
        "apellidos": obtenido.get("apellidos") or "",
        "rol": obtenido.get("rol") or "",
    }
