from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class AdaptadorDesembolsoStub:
    """Implementación SUSTITUIBLE de AdaptadorDesembolso (HU-34). Simula el desembolso
    sin red de pagos real: solo registra en memoria que el desembolso se ejecutó.
    Sustituir por la red de desembolsos real (ms-pagos u otra pasarela) no requiere
    cambiar application/ ni domain/: solo cumplir el Protocol AdaptadorDesembolso."""

    desembolsos: list[tuple[str, Decimal]] = field(default_factory=list)

    async def desembolsar(self, evento_id: str, monto: Decimal) -> None:
        self.desembolsos.append((evento_id, monto))
