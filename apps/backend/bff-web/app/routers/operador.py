from datetime import date, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..clients.base import RechazoDelNucleo, RecursoNoEncontrado, ServicioNoDisponible
from ..clients.ms_siniestros import ClienteMsSiniestros
from ..clients.ms_polizas import ClienteMsPolizas
from ..dependencies import (
    obtener_cliente_cotizacion,
    obtener_cliente_polizas,
    obtener_cliente_siniestros,
    require_roles,
)
from ..ramos import presentar
from ..clients.ms_cotizacion import ClienteMsCotizacion

router = APIRouter(
    prefix="/operador",
    tags=["operador"],
    dependencies=[Depends(require_roles("operador"))],
)

Operador = Annotated[dict, Depends(require_roles("operador"))]


class Ciclo(BaseModel):
    numero: str
    # El canal web solo conoce `numero` (número visible de póliza); ciclo()
    # lo resuelve a poliza_id vía ClienteMsPolizas.obtener_por_numero() antes
    # de llamar a renovar/modificar/cancelar. Si el frontend ya conoce el
    # UUID interno (p.ej. de una consulta previa), puede mandarlo directo en
    # `polizaId` para ahorrarse esa resolución.
    polizaId: UUID | None = None
    verbo: str
    motivo: str | None = None
    # TODO: shape provisional para habilitar el verbo "modificar" de extremo
    # a extremo -- el canal web todavía no define un formulario real de
    # edición de coberturas; mientras tanto se reusa el mismo shape de
    # entrada que ya expone ms-polizas (ver CoberturaEntrada en
    # ms-polizas/app/api/v1/schemas.py: nombre/suma_asegurada/deducible).
    coberturas: list[dict[str, Any]] | None = None
    # TODO: el canal web tampoco define todavía un formulario de renovación
    # con fecha explícita -- se usa un default de +1 año desde hoy (ver
    # ciclo()) a menos que el frontend ya mande una fecha concreta aquí.
    nuevaFinVigencia: date | None = None


# HU-26/27/28/29: la cola de avisos, la decisión, el perito y el pago viven en
# routers/siniestros.py (router_operador), integrados con el siniestro asistido real.


def _poliza_salida(
    numero: str,
    poliza: dict,
    siniestros_abiertos: int | None = None,
    cotizacion: dict | None = None,
) -> dict:
    ramo, descripcion = presentar((cotizacion or {}).get("producto"))
    datos = (cotizacion or {}).get("datos_riesgo") or {}
    return {
        "numero": numero,
        "ramo": ramo,
        "descripcion": descripcion,
        "datosRiesgo": datos,
        "estado": poliza["estado"].lower(),
        "venceEn": poliza.get("fin_vigencia", ""),
        "prima": poliza["prima"],
        # HU-60: ms-polizas ya devuelve esto (PolizaSalida.coberturas), pero
        # _poliza_salida nunca lo exponía al canal web -- sin esto, el
        # back-office no puede precargar los valores actuales antes de
        # modificarlos.
        "coberturas": poliza.get("coberturas", []),
        "renovable": poliza["renovable"],
        "devolucionEstimada": poliza.get("devolucion_estimada"),
        "canceladaEn": poliza.get("cancelada_en"),
        "canceladaPor": poliza.get("cancelada_por"),
        "motivoCancelacion": poliza.get("motivo_cancelacion"),
        "siniestrosAbiertos": siniestros_abiertos,
    }


async def _resolver_poliza_id(body: Ciclo, cliente_polizas: ClienteMsPolizas) -> UUID:
    if body.polizaId is not None:
        return body.polizaId
    encontrada = await cliente_polizas.obtener_por_numero(body.numero)
    return UUID(encontrada["id"])


async def _cotizacion_de_poliza(cliente_cotizacion: ClienteMsCotizacion, poliza: dict) -> dict:
    oferta_id = poliza.get("oferta_id")
    if not oferta_id:
        return {}
    try:
        return await cliente_cotizacion.reconsultar_por_oferta(UUID(str(oferta_id)))
    except (RecursoNoEncontrado, ServicioNoDisponible, RechazoDelNucleo, ValueError):
        return {}


@router.get("/polizas/{numero}")
async def consultar_poliza(
    numero: str,
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
) -> dict:
    """Detalle de una póliza por número visible, para que el operador decida
    si renovar o cancelar antes de ejecutar el comando (ver ciclo())."""
    poliza = await cliente_polizas.obtener_por_numero(numero)
    return _poliza_salida(numero, poliza, cotizacion=await _cotizacion_de_poliza(cliente_cotizacion, poliza))


@router.post("/polizas/ciclo")
async def ciclo(
    body: Ciclo,
    operador: Operador,
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
    cliente_siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
) -> dict:
    if body.verbo not in {"renovar", "modificar", "cancelar"}:
        raise HTTPException(status_code=400, detail="Verbo no permitido")
    if body.verbo == "cancelar" and not body.motivo:
        raise HTTPException(status_code=400, detail="Motivo requerido")
    if body.verbo == "modificar" and not body.coberturas:
        raise HTTPException(status_code=400, detail="Coberturas requeridas")

    poliza_id = await _resolver_poliza_id(body, cliente_polizas)

    if body.verbo == "renovar":
        nueva_fin_vigencia = body.nuevaFinVigencia or date.today() + timedelta(days=365)
        poliza = await cliente_polizas.renovar(poliza_id, nueva_fin_vigencia)
        return _poliza_salida(body.numero, poliza)
    if body.verbo == "modificar":
        poliza = await cliente_polizas.modificar_coberturas(poliza_id, body.coberturas or [])
        return _poliza_salida(body.numero, poliza)

    # HU-61: siniestros abiertos es solo informativo -- se consulta pero no
    # bloquea la cancelación (ver ClienteMsSiniestros.abiertos_por_poliza).
    siniestros_abiertos = await cliente_siniestros.abiertos_por_poliza(poliza_id)
    poliza = await cliente_polizas.cancelar(poliza_id, body.motivo or "", operador["sub"])
    return _poliza_salida(body.numero, poliza, siniestros_abiertos)


# TODO: depende de ms-siniestros/ms-parametrico (gestión de asistencias), que
# no están conectados a este BFF en esta rama.
@router.get("/asistencias/{asistencia_id}")
def asistencia(asistencia_id: str) -> dict:
    return {
        "asistenciaId": asistencia_id,
        "prestadorId": "PR-1",
        "poliza": "POL-88219-CO",
        "estado": "registrada",
    }
