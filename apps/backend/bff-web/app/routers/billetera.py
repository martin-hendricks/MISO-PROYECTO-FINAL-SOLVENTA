"""Billetera del cliente: lectura de depósitos ya ejecutados. La regla vive en ms-siniestros."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from ..clients.ms_siniestros import ClienteMsSiniestros
from ..dependencies import obtener_cliente_siniestros, require_roles
from ..ramos import presentar

router_cliente = APIRouter(prefix="/cliente", tags=["cliente-billetera"])

Cliente = Annotated[dict, Depends(require_roles("cliente"))]
Siniestros = Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)]


def movimiento(pago: dict) -> dict:
    tipo = pago.get("tipo")
    return {
        "id": pago["siniestro_id"],
        "siniestroId": pago.get("numero") or pago["siniestro_id"],
        "tipo": "pago_automatico" if tipo == "parametrico" else "asistido",
        "ramo": presentar(pago.get("ramo"))[0],
        "resumen": pago.get("descripcion") or "",
        "poliza": pago.get("poliza_numero"),
        "monto": float(pago["monto"]),
        "moneda": pago.get("moneda") or "COP",
        "comprobante": pago["comprobante"],
        "depositadoEn": pago["pagado_en"],
    }


@router_cliente.get("/billetera")
async def listar(usuario: Cliente, siniestros: Siniestros) -> dict:
    cuerpo = await siniestros.pagos_recibidos()
    movimientos = [movimiento(p) for p in cuerpo["pagos"]]
    monedas = {fila["moneda"] for fila in movimientos}
    if len(monedas) > 1 or cuerpo.get("total") is None:
        return {"moneda": None, "totalRecibido": None, "movimientos": movimientos}
    return {
        "moneda": next(iter(monedas), cuerpo.get("moneda") or "COP"),
        "totalRecibido": float(cuerpo["total"]),
        "movimientos": movimientos,
    }


@router_cliente.get("/billetera/{siniestro_id}")
async def detalle(siniestro_id: UUID, usuario: Cliente, siniestros: Siniestros) -> dict:
    return movimiento(await siniestros.pago_recibido(siniestro_id))
