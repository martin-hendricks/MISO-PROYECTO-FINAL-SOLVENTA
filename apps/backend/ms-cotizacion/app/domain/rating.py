from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any
from uuid import UUID

from .errores import ReglaDeNegocioViolada

_DOS_DECIMALES = Decimal("0.01")


@dataclass(frozen=True)
class ReglaRating:
    id: UUID
    producto: str
    version: str
    formula: dict[str, Any]


@dataclass(frozen=True)
class ResultadoPrima:
    prima_neta: Decimal
    gastos_expedicion: Decimal
    moneda: str

    @property
    def prima_total(self) -> Decimal:
        return self.prima_neta + self.gastos_expedicion


def evaluar_idoneidad(regla: ReglaRating, datos_riesgo: dict[str, Any]) -> None:
    """Rechaza la cotización cuando el gasto supera el porcentaje máximo vigente.
    Un ratio igual al umbral sigue siendo elegible. Sin umbral o sin montos, la
    regla anterior de precio se conserva."""
    formula = regla.formula
    if "porcentaje_maximo" not in formula:
        return
    if "ingresos_mensuales" not in datos_riesgo or "gastos_mensuales" not in datos_riesgo:
        return
    ingresos = Decimal(str(datos_riesgo["ingresos_mensuales"]))
    gastos = Decimal(str(datos_riesgo["gastos_mensuales"]))
    if ingresos <= 0:
        raise ReglaDeNegocioViolada("idoneidad_no_cumplida", "El ingreso mensual debe ser mayor que cero")
    if gastos / ingresos > Decimal(str(formula["porcentaje_maximo"])):
        raise ReglaDeNegocioViolada(
            "idoneidad_no_cumplida", "El ratio de gastos supera el porcentaje máximo vigente"
        )


def calcular_prima(regla: ReglaRating, datos_riesgo: dict[str, Any]) -> ResultadoPrima:
    """Determinista: mismos (regla, datos_riesgo) -> mismo ResultadoPrima exacto.
    Falla con error tipificado si falta un insumo obligatorio, antes de construir
    cualquier resultado parcial."""
    formula = regla.formula
    for insumo in formula.get("insumos_requeridos", []):
        if insumo not in datos_riesgo:
            raise ReglaDeNegocioViolada(
                "insumo_obligatorio_ausente", f"Falta el insumo obligatorio '{insumo}' para calcular la prima"
            )

    base = Decimal(str(formula["base"]))
    prima_neta = base.quantize(_DOS_DECIMALES, rounding=ROUND_HALF_EVEN)
    gastos = Decimal(str(formula["gastos_fijos"])).quantize(_DOS_DECIMALES, rounding=ROUND_HALF_EVEN)
    return ResultadoPrima(prima_neta=prima_neta, gastos_expedicion=gastos, moneda=formula["moneda"])
