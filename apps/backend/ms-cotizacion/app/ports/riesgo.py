from __future__ import annotations

from decimal import Decimal
from typing import Protocol
from uuid import UUID


class AdaptadorPerfilRiesgo(Protocol):
    async def obtener_factor(self, usuario_id: UUID, producto: str) -> Decimal:
        """Devuelve el factor crudo del proveedor de perfil. Puede tardar o fallar; el
        llamador (caso de uso) es quien aplica timeout y valor de respaldo, NO el
        adaptador mismo — así un adaptador real (Open Finance) no necesita saber nada de
        la política de resiliencia de Solventa, solo cumplir esta interfaz."""
        ...
