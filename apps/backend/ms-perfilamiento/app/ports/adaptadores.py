from __future__ import annotations

from decimal import Decimal
from typing import Protocol


class AdaptadorOpenFinance(Protocol):
    """Puerto SUSTITUIBLE (HU-54) hacia la fuente simulada de Open Finance. El núcleo
    nunca conoce el esquema real del banco: solo este Protocol, que ya expresa los
    atributos propios de Solventa. El caso de uso (no el adaptador) decide el timeout y
    qué hacer si tarda o falla — ver application/casos_uso.py y config.py."""

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        """Devuelve {"nivel_ingresos_estimado": ..., "score_comportamiento": ...}."""
        ...


class AdaptadorOpenData(Protocol):
    """Puerto SUSTITUIBLE (HU-54) hacia la fuente simulada de Open Data (catálogos
    públicos/abiertos). Mismo contrato de resiliencia que AdaptadorOpenFinance: el
    adaptador real no necesita saber nada de timeouts ni de degradación."""

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        """Devuelve {"zona_riesgo": ..., "antiguedad_documento": ...}."""
        ...
