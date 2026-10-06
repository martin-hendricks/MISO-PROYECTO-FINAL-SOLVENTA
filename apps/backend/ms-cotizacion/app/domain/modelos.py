from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from .catalogo import Cobertura, Producto
from .errores import ReglaDeNegocioViolada

CENTAVOS = Decimal("0.01")


class EstadoCotizacion(StrEnum):
    OFERTA_VIGENTE = "oferta_vigente"


@dataclass(frozen=True)
class Cotizacion:
    """Oferta en firme asociada a un cotizacionId. Sin histórico: vive mientras esté vigente (HU-3)."""

    id: UUID
    producto: str
    datos_riesgo: dict[str, Any]
    prima_base: Decimal
    factor_riesgo: Decimal
    prima: Decimal
    moneda: str
    coberturas: tuple[Cobertura, ...]
    estado: EstadoCotizacion
    creada_en: datetime
    vence_en: datetime

    @classmethod
    def ofertar(
        cls,
        producto: Producto,
        datos_riesgo: dict[str, Any],
        prima_base: Decimal,
        factor_riesgo: Decimal,
        ahora: datetime,
        vigencia: timedelta,
    ) -> Cotizacion:
        if prima_base <= 0:
            raise ReglaDeNegocioViolada("prima_no_positiva", "La prima base debe ser mayor que cero")
        if factor_riesgo <= 0:
            raise ReglaDeNegocioViolada("factor_riesgo_no_positivo", "El factor de riesgo debe ser mayor que cero")
        return cls(
            id=uuid4(),
            producto=producto.codigo,
            datos_riesgo=dict(datos_riesgo),
            prima_base=prima_base,
            factor_riesgo=factor_riesgo,
            prima=(prima_base * factor_riesgo).quantize(CENTAVOS, rounding=ROUND_HALF_UP),
            moneda=producto.moneda,
            coberturas=producto.coberturas,
            estado=EstadoCotizacion.OFERTA_VIGENTE,
            creada_en=ahora,
            vence_en=ahora + vigencia,
        )

    def vigente_en(self, instante: datetime) -> bool:
        return instante < self.vence_en
