from __future__ import annotations

import asyncio
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


async def _simular_tercero(proveedor: str, latencia_ms: int, fallar: bool) -> None:
    """HU-88: demora y fallo forzables por configuración, para ejercitar la degradación
    de HU-56 en el ambiente de integración sin red ni proveedor real."""
    await asyncio.sleep(latencia_ms / 1000)
    if fallar:
        raise RuntimeError(f"doble de {proveedor}: fallo simulado")


class AdaptadorOpenFinanceStub:
    """Implementación SUSTITUIBLE de AdaptadorOpenFinance (HU-54) para desarrollo/tests.
    Los atributos ("nivel_ingresos_estimado", "score_comportamiento") son propios de
    Solventa, inventados para el proyecto académico: no son el payload real de ningún
    banco. Un adaptador real cumpliría el mismo Protocol llamando por HTTP al proveedor
    de Open Finance, sin que application/ ni domain/ cambien."""

    def __init__(self, latencia_ms: int = 0, fallar: bool = False) -> None:
        self._latencia_ms = latencia_ms
        self._fallar = fallar

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        await _simular_tercero("Open Finance", self._latencia_ms, self._fallar)
        return {
            NIVEL_INGRESOS_ESTIMADO: _pseudo_aleatorio(cliente_id, "open_finance:ingresos"),
            SCORE_COMPORTAMIENTO: _pseudo_aleatorio(cliente_id, "open_finance:score"),
        }


class AdaptadorOpenDataStub:
    """Implementación SUSTITUIBLE de AdaptadorOpenData (HU-54) para desarrollo/tests.
    Los atributos ("zona_riesgo", "antiguedad_documento") son propios de Solventa,
    inventados para el proyecto académico: no son el esquema real de ningún catálogo
    Open Data."""

    def __init__(self, latencia_ms: int = 0, fallar: bool = False) -> None:
        self._latencia_ms = latencia_ms
        self._fallar = fallar

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        await _simular_tercero("Open Data", self._latencia_ms, self._fallar)
        return {
            ZONA_RIESGO: _pseudo_aleatorio(cliente_id, "open_data:zona"),
            ANTIGUEDAD_DOCUMENTO: _pseudo_aleatorio(cliente_id, "open_data:antiguedad"),
        }
