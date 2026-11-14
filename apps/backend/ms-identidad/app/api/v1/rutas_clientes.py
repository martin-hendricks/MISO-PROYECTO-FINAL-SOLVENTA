from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.application import casos_uso_clientes
from app.dependencies import (
    obtener_cliente_consentimiento,
    obtener_cliente_perfilamiento,
    obtener_uow,
)
from app.domain.modelos import EstadoUsuario
from app.ports.consentimiento import ConsultaConsentimiento
from app.ports.perfilamiento import ConsultaPerfilamiento
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import LlamanteDep, exigir_rol_backoffice

from .schemas import ErrorSalida
from .schemas_clientes import ActualizarEstadoClienteEntrada, ClienteSalida, ClientesSalida

router = APIRouter(prefix="/v1/clientes", tags=["clientes"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Consentimiento = Annotated[ConsultaConsentimiento, Depends(obtener_cliente_consentimiento)]
Perfilamiento = Annotated[ConsultaPerfilamiento, Depends(obtener_cliente_perfilamiento)]
ERRORES = {403: {"model": ErrorSalida}, 404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.get("", response_model=ClientesSalida, responses=ERRORES)
async def listar(uow: Uow, llamante: LlamanteDep, consentimiento: Consentimiento, perfilamiento: Perfilamiento):
    """Listado de clientes para el back-office (HU-141). Solo asesor/operador."""
    exigir_rol_backoffice(llamante)
    pares = await casos_uso_clientes.listar_clientes(uow, consentimiento, perfilamiento)
    return ClientesSalida(clientes=[ClienteSalida.desde(usuario, valor) for usuario, valor in pares])


@router.get("/{usuario_id}", response_model=ClienteSalida, responses=ERRORES)
async def consultar(
    usuario_id: UUID, uow: Uow, llamante: LlamanteDep, consentimiento: Consentimiento, perfilamiento: Perfilamiento
):
    """Ficha de un cliente individual para el back-office (HU-141)."""
    exigir_rol_backoffice(llamante)
    usuario, valor = await casos_uso_clientes.obtener_cliente(uow, usuario_id, consentimiento, perfilamiento)
    return ClienteSalida.desde(usuario, valor)


@router.patch("/{usuario_id}/estado", response_model=ClienteSalida, responses=ERRORES)
async def actualizar_estado(
    usuario_id: UUID,
    entrada: ActualizarEstadoClienteEntrada,
    uow: Uow,
    llamante: LlamanteDep,
    consentimiento: Consentimiento,
    perfilamiento: Perfilamiento,
):
    """Activa/desactiva un cliente desde el back-office (HU-141)."""
    exigir_rol_backoffice(llamante)
    nuevo_estado = EstadoUsuario.ACTIVO if entrada.estado == "activo" else EstadoUsuario.INACTIVO
    usuario = await casos_uso_clientes.actualizar_estado_cliente(uow, usuario_id, nuevo_estado)
    valor = await casos_uso_clientes.resolver_consentimiento(usuario.id, consentimiento, perfilamiento)
    return ClienteSalida.desde(usuario, valor)
