from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any

from .errores import ReglaDeNegocioViolada
from .rating import ResultadoPrima

_DOS_DECIMALES = Decimal("0.01")

# Pesos colombianos por 1 unidad de la moneda. Tasas fijas de la plataforma:
# la fórmula sigue calculando en su moneda y la prima de una cotización nueva
# se expresa en la moneda que el canal tenía seleccionada. No es un tipo de
# cambio de mercado.
COP_POR_UNIDAD: dict[str, Decimal] = {
    "COP": Decimal("1"),
    "MXN": Decimal("220"),
    "CLP": Decimal("4.5"),
    "PEN": Decimal("1100"),
}

# Montos de riesgo que el cliente escribe en la moneda seleccionada. Plazo, edad
# y cilindrada no están aquí: siguen en las unidades del catálogo.
CAMPOS_MONEDA = frozenset({"valorDispositivo", "sumaAsegurada", "valor", "cuota", "valorCredito"})


def validar_moneda(moneda: str | None) -> str | None:
    """None cuando el canal no eligió moneda. Rechaza un código fuera de COP, MXN, CLP y PEN."""
    if moneda is None or not moneda.strip():
        return None
    destino = moneda.strip().upper()
    if destino not in COP_POR_UNIDAD:
        raise ReglaDeNegocioViolada("moneda_no_soportada", "La moneda de la cotización no está soportada")
    return destino


def expresar_prima(resultado: ResultadoPrima, moneda: str | None) -> ResultadoPrima:
    """Deja la prima en la moneda pedida. Sin moneda, o con la de la fórmula, no la toca."""
    destino = validar_moneda(moneda)
    if destino is None:
        return resultado
    origen = resultado.moneda
    if destino == origen:
        return resultado
    if origen not in COP_POR_UNIDAD:
        raise ReglaDeNegocioViolada(
            "moneda_no_soportada", f"No se puede expresar una prima calculada en {origen}"
        )
    divisor = COP_POR_UNIDAD[destino]
    origen_en_cop = COP_POR_UNIDAD[origen]

    def convertir(valor: Decimal) -> Decimal:
        return (valor * origen_en_cop / divisor).quantize(_DOS_DECIMALES, rounding=ROUND_HALF_EVEN)

    return ResultadoPrima(
        prima_neta=convertir(resultado.prima_neta),
        gastos_expedicion=convertir(resultado.gastos_expedicion),
        moneda=destino,
    )


def expresar_datos_riesgo(datos: dict[str, Any], moneda: str | None, moneda_producto: str) -> dict[str, Any]:
    """Pasa los montos que el canal envió a la moneda del producto, para el rango del catálogo.

    Un valor de dispositivo en soles se compara con el rango en pesos. Plazo y edad no se tocan.
    """
    origen = validar_moneda(moneda)
    if origen is None or origen == moneda_producto:
        return datos
    if origen not in COP_POR_UNIDAD or moneda_producto not in COP_POR_UNIDAD:
        return datos
    salida = dict(datos)
    for campo, valor in datos.items():
        if campo not in CAMPOS_MONEDA or isinstance(valor, bool) or valor is None:
            continue
        try:
            numero = Decimal(str(valor))
        except (InvalidOperation, ValueError):
            continue
        convertido = (numero * COP_POR_UNIDAD[origen] / COP_POR_UNIDAD[moneda_producto]).quantize(
            _DOS_DECIMALES, rounding=ROUND_HALF_EVEN
        )
        salida[campo] = int(convertido) if convertido == convertido.to_integral_value() else float(convertido)
    return salida
