from __future__ import annotations

from decimal import Decimal
from typing import Protocol


class AdaptadorDesembolso(Protocol):
    async def desembolsar(self, evento_id: str, monto: Decimal) -> None:
        """Ejecuta el desembolso. El llamador (caso de uso) decide el monto y cuándo
        llamar; el adaptador solo cumple esta interfaz. Sustituir el stub por la red de
        desembolsos real no debe alterar application/ ni domain/."""
        ...
