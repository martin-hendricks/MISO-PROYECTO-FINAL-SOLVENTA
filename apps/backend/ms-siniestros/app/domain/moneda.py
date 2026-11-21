from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

from .errores import ReglaDeNegocioViolada

_DOS_DECIMALES = Decimal("0.01")

# Pesos colombianos por 1 unidad. La parametría del ramo sigue en COP; la reserva
# de un aviso nuevo se expresa en la moneda de la póliza. No es un tipo de cambio
# de mercado: es la misma tabla fija que usa ms-cotizacion.
COP_POR_UNIDAD: dict[str, Decimal] = {
    "COP": Decimal("1"),
    "MXN": Decimal("220"),
    "CLP": Decimal("4.5"),
    "PEN": Decimal("1100"),
}


def validar_moneda(moneda: str | None) -> str:
    """COP cuando el canal no indica moneda. Rechaza un código fuera de la tabla."""
    if moneda is None or not moneda.strip():
        return "COP"
    destino = moneda.strip().upper()
    if destino not in COP_POR_UNIDAD:
        raise ReglaDeNegocioViolada("moneda_no_soportada", "La moneda del siniestro no está soportada")
    return destino


def expresar_monto(valor: Decimal | None, moneda: str) -> Decimal | None:
    """Pasa un monto calculado en COP a la moneda del aviso. COP, o sin monto, no cambia."""
    if valor is None or moneda == "COP":
        return valor
    return (valor / COP_POR_UNIDAD[moneda]).quantize(_DOS_DECIMALES, rounding=ROUND_HALF_EVEN)
