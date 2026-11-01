from datetime import date, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..clients.ms_siniestros import ClienteMsSiniestros
from ..clients.ms_polizas import ClienteMsPolizas
from ..dependencies import obtener_cliente_polizas, obtener_cliente_siniestros, require_roles

router = APIRouter(
    prefix="/operador",
    tags=["operador"],
    dependencies=[Depends(require_roles("operador"))],
)

Operador = Annotated[dict, Depends(require_roles("operador"))]

# Mapea la decisión del operador (vocabulario del canal web) al estado real
# del enum EstadoSiniestro de ms-siniestros (ver
# apps/backend/ms-siniestros/app/domain/modelos.py). El dominio de
# ms-siniestros modela un único estado "decidido" como el paso siguiente a
# "en_evaluacion" -- NO distingue aprobado/rechazado con valores de enum
# separados ni expone un campo adicional para esa distinción binaria. Hasta
# que ms-siniestros agregue ese campo (p.ej. un "resultado" dentro de la
# transición), tanto aprobar como rechazar se traducen al mismo estado
# "decidido" en el núcleo; el motivo de rechazo que captura el canal web hoy
# no tiene dónde persistirse del lado de ms-siniestros.
_DECISION_A_ESTADO = {"aprobar": "decidido", "rechazar": "decidido"}


class Decision(BaseModel):
    siniestroId: str
    decision: str
    motivo: str | None = None


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


@router.get("/avisos")
async def cola(
    cliente_siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
) -> dict:
    """Integración real con ms-siniestros (GET /v1/siniestros).

    TODO: ms-siniestros no filtra por operador/cola -- GET /v1/siniestros
    devuelve la lista completa del servicio (hasta `limite`), sin noción de
    "cola asignada a este operador". Mientras ms-siniestros no ofrezca ese
    filtro, el BFF expone la lista completa tal cual.

    TODO: el shape del canal web espera "poliza" y "ramo" por aviso, pero el
    modelo de ms-siniestros (ver app/domain/modelos.py) no tiene esos campos
    -- un Siniestro solo referencia evento_id, no una póliza ni un ramo.
    Hace falta que ms-siniestros se relacione con ms-polizas (o que el BFF
    componga con una llamada adicional a ms-polizas) para resolver esos
    datos. Por ahora se devuelven como placeholder explícito (cadena vacía),
    nunca como un valor inventado que parezca real.
    """
    siniestros = await cliente_siniestros.listar()
    return {
        "avisos": [
            {
                "siniestroId": str(s["id"]),
                "poliza": "",
                "ramo": "",
                "estado": s["estado"],
            }
            for s in siniestros
        ]
    }


@router.post("/avisos/decision")
async def decidir(
    body: Decision,
    cliente_siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
) -> dict:
    """Integración real con ms-siniestros (POST /v1/siniestros/{id}/estado).

    Ver _DECISION_A_ESTADO: tanto aprobar como rechazar hoy mapean al mismo
    estado "decidido" del enum EstadoSiniestro, porque ese es el único estado
    que el dominio de ms-siniestros modela como sucesor de "en_evaluacion".
    Si la transición no es válida para el estado actual del siniestro (p.ej.
    ya está "decidido" o más adelante en el flujo), ms-siniestros responde
    409 (TransicionInvalida) y ese error se propaga tal cual vía los
    exception handlers de main.py.
    """
    if body.decision not in _DECISION_A_ESTADO:
        raise HTTPException(status_code=400, detail="Decision no permitida")
    if body.decision == "rechazar" and not body.motivo:
        raise HTTPException(status_code=400, detail="Motivo requerido")

    try:
        siniestro_id = UUID(body.siniestroId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="siniestroId invalido") from exc

    estado = _DECISION_A_ESTADO[body.decision]
    actualizado = await cliente_siniestros.cambiar_estado(
        siniestro_id=siniestro_id,
        estado=estado,
        origen="operador",
    )
    return {
        "siniestroId": str(actualizado["id"]),
        "decision": body.decision,
        "motivo": body.motivo,
        "estado": actualizado["estado"],
    }


def _poliza_salida(numero: str, poliza: dict, siniestros_abiertos: int | None = None) -> dict:
    # TODO: `ramo` no existe en la salida de ms-polizas (Poliza no tiene
    # concepto de ramo, ver app/domain/modelos.py de ms-polizas) -- mismo
    # faltante documentado en cliente.py (emitir()/detalle()/billetera()).
    # Se usa el numero que ya conocía el canal en vez del que devuelve
    # ms-polizas por si llegaran a divergir alguna vez.
    return {
        "numero": numero,
        "ramo": "Protección de dispositivo",
        "estado": poliza["estado"].lower(),
        "venceEn": poliza.get("fin_vigencia", ""),
        "prima": poliza["prima"],
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


@router.get("/polizas/{numero}")
async def consultar_poliza(
    numero: str,
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
) -> dict:
    """Detalle de una póliza por número visible, para que el operador decida
    si renovar o cancelar antes de ejecutar el comando (ver ciclo())."""
    poliza = await cliente_polizas.obtener_por_numero(numero)
    return _poliza_salida(numero, poliza)


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
