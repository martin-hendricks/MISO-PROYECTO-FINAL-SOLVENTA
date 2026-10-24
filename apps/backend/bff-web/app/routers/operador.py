from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import require_roles

router = APIRouter(
    prefix="/operador",
    tags=["operador"],
    dependencies=[Depends(require_roles("operador"))],
)


class Decision(BaseModel):
    siniestroId: str
    decision: str
    motivo: str | None = None


class Ciclo(BaseModel):
    numero: str
    verbo: str
    motivo: str | None = None


# TODO: depende de ms-siniestros, que no tiene código en esta rama ni en
# develop -- falta ese microservicio para integrar la cola real de avisos.
@router.get("/avisos")
def cola() -> dict:
    return {
        "avisos": [
            {
                "siniestroId": "SIN-441",
                "poliza": "POL-88219-CO",
                "ramo": "Protección de dispositivo",
                "estado": "en_evaluacion",
            }
        ]
    }


# TODO: mismo faltante que cola() -- la decisión sobre un aviso depende de
# ms-siniestros.
@router.post("/avisos/decision")
def decidir(body: Decision) -> dict:
    if body.decision not in {"aprobar", "rechazar"}:
        raise HTTPException(status_code=400, detail="Decision no permitida")
    if body.decision == "rechazar" and not body.motivo:
        raise HTTPException(status_code=400, detail="Motivo requerido")
    return body.model_dump()


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
