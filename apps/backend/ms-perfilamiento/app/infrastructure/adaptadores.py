from __future__ import annotations

import hashlib
from decimal import Decimal

from app.domain.precio import ANTIGUEDAD_DOCUMENTO, NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO, ZONA_RIESGO


def _pseudo_aleatorio(cliente_id: str, sal: str) -> Decimal:
    """Determinista por cliente_id: mismo cliente_id -> mismo valor siempre, sin
    depender de ningún proveedor real. Se usa solo para dar variedad entre clientes en
    el stub; un adaptador real reemplazaría esto por la llamada HTTP al proveedor."""
    digest = hashlib.sha256(f"{cliente_id}:{sal}".encode()).hexdigest()
    entero = int(digest[:8], 16)
    return (Decimal(entero % 1000) / Decimal(1000)).quantize(Decimal("0.001"))


class AdaptadorOpenFinanceStub:
    """Implementación SUSTITUIBLE de AdaptadorOpenFinance (HU-54) para desarrollo/tests.
    Los atributos ("nivel_ingresos_estimado", "score_comportamiento") son propios de
    Solventa, inventados para el proyecto académico: no son el payload real de ningún
    banco. Un adaptador real cumpliría el mismo Protocol llamando por HTTP al proveedor
    de Open Finance, sin que application/ ni domain/ cambien."""

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        return {
            NIVEL_INGRESOS_ESTIMADO: _pseudo_aleatorio(cliente_id, "open_finance:ingresos"),
            SCORE_COMPORTAMIENTO: _pseudo_aleatorio(cliente_id, "open_finance:score"),
        }


class AdaptadorOpenDataStub:
    """Implementación SUSTITUIBLE de AdaptadorOpenData (HU-54) para desarrollo/tests.
    Los atributos ("zona_riesgo", "antiguedad_documento") son propios de Solventa,
    inventados para el proyecto académico: no son el esquema real de ningún catálogo
    Open Data."""

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        return {
            ZONA_RIESGO: _pseudo_aleatorio(cliente_id, "open_data:zona"),
            ANTIGUEDAD_DOCUMENTO: _pseudo_aleatorio(cliente_id, "open_data:antiguedad"),
        }
