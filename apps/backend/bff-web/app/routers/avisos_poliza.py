from typing import Annotated

from fastapi import APIRouter, Depends

from ..clients.ms_polizas import ClienteMsPolizas
from ..dependencies import obtener_cliente_polizas, require_roles
from ..ramos import presentar
from .cliente import contexto_canonico

# Nombrado avisos_poliza (no avisos.py) para no confundirse con la cola de
# avisos de SINIESTROS del operador (routers/siniestros.py, HU-157) -- este
# router es sobre vencimiento/renovación de pólizas, canal cliente, HU-119.
router = APIRouter(
    prefix="/cliente",
    tags=["cliente-avisos-poliza"],
    dependencies=[Depends(require_roles("cliente"))],
)

DIAS_POR_DEFECTO = 30


def _aviso_salida(poliza: dict) -> dict:
    ramo, descripcion = presentar(poliza.get("producto"))
    return {
        "numero": poliza["numero"],
        "ramo": ramo,
        "descripcion": descripcion,
        "venceEn": poliza.get("fin_vigencia", ""),
        # HU-119: "the customer cannot renew it" -- el aviso es de solo
        # lectura, nunca expone una acción de renovar (eso es exclusivo del
        # operador vía POST /operador/polizas/ciclo, ver routers/operador.py).
        "renovable": poliza.get("renovable", False),
    }


@router.get("/polizas/por-vencer")
async def polizas_por_vencer(
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
) -> dict:
    """HU-119: avisa pólizas vigentes del cliente que vencen pronto.

    HU-120 (confirmación de renovación) no necesita un endpoint propio: una
    vez renovada, GET /cliente/polizas/{numero} (ya existente) ya refleja el
    fin_vigencia actualizado -- el aviso de renovación es leer ese mismo
    detalle, no una vista separada.
    """
    contexto = contexto_canonico(usuario)
    polizas = await cliente_polizas.por_vencer(contexto.usuario_id, DIAS_POR_DEFECTO)
    return {"polizas": [_aviso_salida(p) for p in polizas]}
