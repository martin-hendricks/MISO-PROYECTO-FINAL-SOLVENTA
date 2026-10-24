from datetime import date, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..clients.ms_polizas import ClienteMsPolizas
from ..dependencies import obtener_cliente_polizas, require_roles

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
    # TODO: el canal web solo conoce `numero` (número visible de póliza),
    # pero ms-polizas solo expone los endpoints de ciclo de vida por
    # poliza_id (UUID interno) -- todavía no existe en esta rama un endpoint
    # de "buscar póliza por número" en ms-polizas que resuelva numero ->
    # poliza_id (ese endpoint de lectura es alcance de otro trabajo en
    # paralelo). Mientras tanto, si el frontend ya conoce el UUID interno de
    # la póliza (p.ej. porque lo guardó de una consulta previa), puede
    # mandarlo directamente en `polizaId` para poder probar el flujo
    # end-to-end; si no lo manda, la ruta responde 501 explícito en vez de
    # inventar un UUID o fallar silenciosamente.
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


def _poliza_salida(body: Ciclo, poliza: dict) -> dict:
    # TODO: `ramo` no existe en la salida de ms-polizas (Poliza no tiene
    # concepto de ramo, ver app/domain/modelos.py de ms-polizas) -- mismo
    # faltante documentado en cliente.py (emitir()/detalle()/billetera()).
    # Se usa el numero que ya conocía el canal (body.numero) en vez del que
    # devuelve ms-polizas, porque hoy no hay garantía de que coincidan sin el
    # endpoint de búsqueda por número (ver TODO en el modelo Ciclo).
    return {
        "numero": body.numero,
        "ramo": "Protección de dispositivo",
        "estado": poliza["estado"].lower(),
        "venceEn": poliza.get("fin_vigencia", ""),
    }


@router.post("/polizas/ciclo")
async def ciclo(
    body: Ciclo,
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
) -> dict:
    if body.verbo not in {"renovar", "modificar", "cancelar"}:
        raise HTTPException(status_code=400, detail="Verbo no permitido")
    if body.verbo == "cancelar" and not body.motivo:
        raise HTTPException(status_code=400, detail="Motivo requerido")
    if body.verbo == "modificar" and not body.coberturas:
        raise HTTPException(status_code=400, detail="Coberturas requeridas")
    if body.polizaId is None:
        # Ver TODO en el modelo Ciclo: sin el endpoint de búsqueda por numero
        # en ms-polizas no hay forma de resolver numero -> poliza_id. Se
        # responde 501 explícito en vez de fallar silenciosamente o inventar
        # un UUID -- el contrato de esta ruta cambió y debe ser visible.
        raise HTTPException(status_code=501, detail="numero->poliza_id no implementado: falta polizaId")

    if body.verbo == "renovar":
        nueva_fin_vigencia = body.nuevaFinVigencia or date.today() + timedelta(days=365)
        poliza = await cliente_polizas.renovar(body.polizaId, nueva_fin_vigencia)
    elif body.verbo == "modificar":
        poliza = await cliente_polizas.modificar_coberturas(body.polizaId, body.coberturas or [])
    else:
        poliza = await cliente_polizas.cancelar(body.polizaId, body.motivo or "")

    return _poliza_salida(body, poliza)


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
