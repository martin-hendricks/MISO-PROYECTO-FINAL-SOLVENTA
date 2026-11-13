from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.domain.modelos import Consentimiento


class RepositorioConsentimientos(Protocol):
    async def obtener_vigente(self, cliente_id: str) -> Consentimiento | None:
        """Debe devolver el consentimiento SOLO si está vigente (no revocado).
        Nunca cachea: cada llamada refleja el último estado persistido —
        es la única garantía de "tiempo real" que ofrece este stub, ya que
        no hay propagación por eventos (ver domain/modelos.py)."""
        ...

    async def obtener_por_id(self, consentimiento_id: UUID) -> Consentimiento | None: ...

    async def agregar(self, consentimiento: Consentimiento) -> None: ...

    async def actualizar(self, consentimiento: Consentimiento) -> None: ...


class UnidadDeTrabajo(Protocol):
    consentimientos: RepositorioConsentimientos

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None: ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
