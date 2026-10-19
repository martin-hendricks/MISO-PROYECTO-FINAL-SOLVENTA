from __future__ import annotations

import asyncio
from decimal import Decimal
from uuid import UUID


class AdaptadorPerfilRiesgoStub:
    """Implementación SUSTITUIBLE de AdaptadorPerfilRiesgo para desarrollo/tests. Simula
    latencia y fallo controlables. Sustituir por un adaptador real (HTTP contra Open
    Finance) no requiere cambiar application/ ni domain/: solo cumplir el Protocol."""

    def __init__(self, latencia_ms: int = 0, fallar: bool = False, factor_fijo: Decimal = Decimal("1.1")) -> None:
        self._latencia_ms = latencia_ms
        self._fallar = fallar
        self._factor_fijo = factor_fijo

    async def obtener_factor(self, usuario_id: UUID, producto: str) -> Decimal:
        await asyncio.sleep(self._latencia_ms / 1000)
        if self._fallar:
            raise RuntimeError("stub de perfil de riesgo: fallo simulado")
        return self._factor_fijo
