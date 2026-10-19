from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum

from .rating import ResultadoPrima

_DOS_DECIMALES = Decimal("0.01")


class OrigenFactorRiesgo(StrEnum):
    REAL = "real"
    RESPALDO = "respaldo"


@dataclass(frozen=True)
class FactorRiesgo:
    valor: Decimal
    origen: OrigenFactorRiesgo


def aplicar_factor_riesgo(resultado: ResultadoPrima, factor: FactorRiesgo) -> ResultadoPrima:
    """Determinista: ajusta solo prima_neta; gastos_expedicion no se ve afectada por el
    perfil. Nunca lanza excepción: aplicar el valor de respaldo jamás falla, es la
    garantía central de la HU ("la degradación nunca cancela el recorrido")."""
    prima_ajustada = (resultado.prima_neta * factor.valor).quantize(_DOS_DECIMALES, rounding=ROUND_HALF_EVEN)
    return ResultadoPrima(
        prima_neta=prima_ajustada, gastos_expedicion=resultado.gastos_expedicion, moneda=resultado.moneda
    )
