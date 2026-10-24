from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..clients.ms_siniestros import ClienteMsSiniestros
from ..dependencies import obtener_cliente_siniestros, require_roles

router = APIRouter(
    prefix="/operador",
    tags=["operador"],
    dependencies=[Depends(require_roles("operador"))],
)

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
    verbo: str
    motivo: str | None = None


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


# TODO: el ciclo de vida de pólizas (renovar/modificar/cancelar) necesita
# endpoints en ms-polizas que hoy no existen (solo hay POST /v1/polizas y
# GET /v1/polizas/{id} en el PR feature/HU-16-emitir-poliza).
@router.post("/polizas/ciclo")
def ciclo(body: Ciclo) -> dict:
    if body.verbo not in {"renovar", "modificar", "cancelar"}:
        raise HTTPException(status_code=400, detail="Verbo no permitido")
    if body.verbo == "cancelar" and not body.motivo:
        raise HTTPException(status_code=400, detail="Motivo requerido")
    estado = "cancelada" if body.verbo == "cancelar" else "vigente"
    return {
        "numero": body.numero,
        "ramo": "Protección de dispositivo",
        "estado": estado,
        "venceEn": "2027-03-12",
    }


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
