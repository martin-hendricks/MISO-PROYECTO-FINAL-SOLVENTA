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
