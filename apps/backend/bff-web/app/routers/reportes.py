from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends

from ..clients.ms_polizas import ClienteMsPolizas
from ..dependencies import obtener_cliente_polizas, require_roles

# El Gherkin (apps/web/e2e/features/backoffice/reports.feature) habla de
# roles "compliance" (regulador) y "operations" (reaseguradora), pero este
# sistema solo tiene 3 roles reales (app/dependencies.py: ROLES = ("cliente",
# "asesor", "operador")) -- no existe ningún rol de back-office más granular
# que "operador". Ambos reportes se autorizan contra ese único rol.
router = APIRouter(
    prefix="/operador",
    tags=["operador-reportes"],
    dependencies=[Depends(require_roles("operador"))],
)

RANGO_POR_DEFECTO_DIAS = 30


def _rango(desde: date | None, hasta: date | None) -> tuple[date, date]:
    fin = hasta or date.today()
    inicio = desde or fin - timedelta(days=RANGO_POR_DEFECTO_DIAS)
    return inicio, fin


@router.get("/reportes/regulador")
async def reporte_regulador(
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
    desde: date | None = None,
    hasta: date | None = None,
) -> dict:
    """HU-62: extracto interno de pólizas/siniestros para el regulador.

    No es el formato SFC real -- el adaptador stub de ms-polizas define el
    contenido; este router solo reenvía la respuesta.
    """
    inicio, fin = _rango(desde, hasta)
    return await cliente_polizas.reporte_regulador(inicio, fin)


@router.get("/reportes/reaseguradora")
async def reporte_reaseguradora(
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
    desde: date | None = None,
    hasta: date | None = None,
) -> dict:
    """HU-63: extracto de cartera/siniestralidad para la reaseguradora.

    No acoplado a ACORD -- mismo adaptador stub, ver reporte_regulador().
    """
    inicio, fin = _rango(desde, hasta)
    return await cliente_polizas.reporte_reaseguradora(inicio, fin)
