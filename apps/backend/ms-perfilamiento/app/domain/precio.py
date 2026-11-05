from __future__ import annotations

from decimal import Decimal

from .modelos import FactorInterno, Oferta, Perfil, ajuste_por_factores

# Nombres de los atributos propios de Solventa (HU-54), usados como claves canónicas
# tanto para armar el Perfil como para calcular la Oferta y sus factores internos.
NIVEL_INGRESOS_ESTIMADO = "nivel_ingresos_estimado"
SCORE_COMPORTAMIENTO = "score_comportamiento"
ZONA_RIESGO = "zona_riesgo"
ANTIGUEDAD_DOCUMENTO = "antiguedad_documento"

_IMPACTO_REDUCE = "reduce_prima"
_IMPACTO_AUMENTA = "aumenta_prima"


def _impacto(peso: Decimal) -> str:
    return _IMPACTO_REDUCE if peso < 0 else _IMPACTO_AUMENTA


def calcular_oferta(cliente_id: str, perfil: Perfil, pesos: dict[str, Decimal], tarifa_base: Decimal) -> Oferta:
    """Fórmula simple y determinista (HU-55): tarifa_base * (1 + sum(peso_i * valor_i))
    sobre los atributos propios de Solventa. No es scoring crediticio real: es una
    fórmula inventada para fines del proyecto académico, documentada en el README del
    servicio. Cada atributo aporta un FactorInterno en lenguaje de negocio, nunca el
    valor crudo del proveedor."""
    factores = [
        FactorInterno(factor=nombre, impacto=_impacto(peso), peso=peso)
        for nombre, peso in pesos.items()
        if perfil.atributo(nombre) is not None
    ]

    precio = tarifa_base * ajuste_por_factores(tuple(factores), perfil.atributos)
    if precio <= 0:
        # Guardia de negocio: ningún combo de pesos/atributos deja la oferta en un
        # precio inválido; se acota a un mínimo simbólico antes de construir la Oferta.
        precio = Decimal("1")
    return Oferta.armar(cliente_id=cliente_id, precio=precio, factores=factores, perfil=perfil)
