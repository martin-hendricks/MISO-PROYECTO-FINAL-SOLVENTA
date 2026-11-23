"""Motor de reglas del siniestro asistido: la "parametría" que aprueba, rechaza o retiene.

Lectura del PDF que aplica (ver README):
- §2.2: el pago de siniestros de BAJO MONTO es automático.
- §5.1 #3: "se evalúa, se aprueba y se paga o se enruta a un perito" -> lo que el motor no
  resuelve pasa a un humano.
- §6.4 / EC-SEG-08: el caso marcado por el antifraude queda RETENIDO con traza completa.

Es determinista y sin red: misma entrada -> misma decisión. Evalúa TODAS las reglas aunque
una falle, para que la auditoría muestre el cuadro completo.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .aviso import ParametroRamo, ReglaEvaluada, ResultadoAuditado
from .modelos import Siniestro

# Reglas cuyo incumplimiento rechaza sin intervención humana (hechos objetivos).
REGLAS_DE_RECHAZO = frozenset({"poliza_vigente", "fecha_en_vigencia"})


@dataclass(frozen=True)
class ResultadoMotor:
    resultado: ResultadoAuditado  # APROBADO | RECHAZADO | REVISION
    motivo: str
    reglas: list[ReglaEvaluada]
    reserva: Decimal | None
    umbral_automatico: Decimal | None


def evaluar(
    siniestro: Siniestro,
    parametro: ParametroRamo | None,
    cantidad_adjuntos: int,
    avisos_previos_en_ventana: int,
) -> ResultadoMotor:
    poliza = siniestro.poliza
    if poliza is None or siniestro.fecha_hecho is None:
        raise ValueError("El motor solo evalúa avisos asistidos con póliza y fecha del hecho")

    reserva = parametro.reserva_para(poliza.suma_asegurada) if parametro else None
    umbral = parametro.umbral_automatico if parametro else None

    reglas = [
        ReglaEvaluada(
            "poliza_vigente",
            poliza.vigente,
            f"Estado de la póliza {poliza.numero}: {poliza.estado}",
        ),
        ReglaEvaluada(
            "fecha_en_vigencia",
            poliza.inicio_vigencia <= siniestro.fecha_hecho <= poliza.fin_vigencia,
            f"Hecho {siniestro.fecha_hecho} frente a vigencia {poliza.inicio_vigencia} a {poliza.fin_vigencia}",
        ),
        ReglaEvaluada(
            "ramo_parametrizado",
            parametro is not None,
            f"Ramo {poliza.ramo}" + ("" if parametro else " sin parametría de reserva"),
        ),
        ReglaEvaluada(
            "evidencia_adjunta",
            cantidad_adjuntos > 0,
            f"{cantidad_adjuntos} archivo(s) de evidencia",
        ),
        ReglaEvaluada(
            # Antifraude (N15): otro aviso sobre la misma póliza dentro de la ventana.
            "sin_avisos_duplicados",
            avisos_previos_en_ventana == 0,
            f"{avisos_previos_en_ventana} aviso(s) previo(s) de la póliza en los últimos "
            f"{parametro.ventana_duplicado_dias if parametro else 30} días",
        ),
        ReglaEvaluada(
            "monto_bajo_umbral",
            reserva is not None and umbral is not None and reserva <= umbral,
            f"Reserva {reserva} frente a umbral automático {umbral}",
        ),
    ]

    fallidas = [r for r in reglas if not r.cumple]
    rechazo = [r for r in fallidas if r.codigo in REGLAS_DE_RECHAZO]
    if rechazo:
        return ResultadoMotor(
            ResultadoAuditado.RECHAZADO, _motivo(rechazo), reglas, reserva, umbral
        )
    if fallidas:
        return ResultadoMotor(ResultadoAuditado.REVISION, _motivo(fallidas), reglas, reserva, umbral)
    return ResultadoMotor(
        ResultadoAuditado.APROBADO, "Cumple todas las reglas de aprobación automática", reglas, reserva, umbral
    )


_MOTIVOS = {
    "poliza_vigente": "La póliza no está vigente",
    "fecha_en_vigencia": "La fecha del evento está fuera de la vigencia de la póliza",
    "ramo_parametrizado": "El ramo no tiene parametría de aprobación automática",
    "evidencia_adjunta": "El aviso no tiene evidencia adjunta",
    "sin_avisos_duplicados": "Posible duplicado: la póliza tiene otro aviso reciente",
    "monto_bajo_umbral": "La reserva supera el umbral de aprobación automática",
}


def _motivo(reglas: list[ReglaEvaluada]) -> str:
    return "; ".join(_MOTIVOS.get(r.codigo, r.codigo) for r in reglas)
