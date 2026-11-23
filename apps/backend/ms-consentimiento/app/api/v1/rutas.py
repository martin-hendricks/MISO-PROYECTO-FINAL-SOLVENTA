from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.application import casos_uso
from app.dependencies import obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import LlamanteDep

from .schemas import ConsentimientoSalida, ErrorSalida, OtorgarConsentimientoEntrada

router = APIRouter(prefix="/v1/consentimientos", tags=["consentimientos"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
ERRORES = {401: {"model": ErrorSalida}, 404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.post("", response_model=ConsentimientoSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def otorgar(entrada: OtorgarConsentimientoEntrada, response: Response, uow: Uow, _: LlamanteDep):
    """Otorga el consentimiento de habeas data del cliente. Idempotente: si
    ya existe uno vigente, responde 200 con ese mismo registro en vez de
    crear uno nuevo (201 solo la primera vez)."""
    registro = await casos_uso.otorgar_consentimiento(uow, entrada.cliente_id)
    if not registro.creado:
        response.status_code = status.HTTP_200_OK
    return ConsentimientoSalida.desde(registro.consentimiento)


@router.get("/{cliente_id}", response_model=ConsentimientoSalida, responses=ERRORES)
async def consultar(cliente_id: str, uow: Uow, _: LlamanteDep):
    """Consentimiento vigente del cliente. 404 si nunca otorgó uno o si el
    último que otorgó ya fue revocado."""
    vigente = await casos_uso.consultar_consentimiento_vigente(uow, cliente_id)
    return ConsentimientoSalida.desde(vigente)


@router.delete("/{cliente_id}", response_model=ConsentimientoSalida, responses=ERRORES)
async def revocar(cliente_id: str, uow: Uow, _: LlamanteDep):
    """Revoca el consentimiento vigente del cliente. 404 si no había
    ninguno vigente."""
    revocado = await casos_uso.revocar_consentimiento(uow, cliente_id)
    return ConsentimientoSalida.desde(revocado)
