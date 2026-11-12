from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends

from ..clients.analitica import ClienteAnalitica
from ..dependencies import obtener_cliente_analitica, require_roles

# Back-office únicamente: estas métricas son de operación interna, nunca del
# propio cliente. Mismo único rol de back-office real que reportes.py
# (app/dependencies.py: ROLES = ("cliente", "asesor", "operador")).
router = APIRouter(
    prefix="/operador",
    tags=["operador-metricas"],
    dependencies=[Depends(require_roles("operador"))],
)

RANGO_POR_DEFECTO_DIAS = 30


@router.get("/metricas")
async def metricas(
    cliente_analitica: Annotated[ClienteAnalitica, Depends(obtener_cliente_analitica)],
    desde: date | None = None,
    hasta: date | None = None,
) -> dict:
    """HU-68/69: conteos agregados de eventos de ciclo de vida de póliza.

    El contenido lo define analitica (tipo/fecha/cantidad); este router solo
    reenvía la respuesta tal cual, sin interpretarla.
    """
    fin = hasta or date.today()
    inicio = desde or fin - timedelta(days=RANGO_POR_DEFECTO_DIAS)
    return await cliente_analitica.metricas(inicio, fin)
