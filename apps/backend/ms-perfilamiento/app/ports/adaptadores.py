from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol, runtime_checkable

from app.domain.modelos import CausaDegradacion

# Consentimiento bajo el que se esta perfilando. El caso de uso lo fija antes de invocar a
# los adaptadores y la cache compartida lo usa para poder borrar, al revocarlo, lo que
# guardo bajo el (las entradas se indexan por cedula, que quien revoca no conoce).
consentimiento_en_curso: ContextVar[str | None] = ContextVar("consentimiento_en_curso", default=None)


@dataclass(frozen=True)
class PerfilResuelto:
    """Atributos mas de donde salieron: del proveedor en esta llamada, de la cache fresca
    o de un valor vencido que se sirvio porque el proveedor no respondio a tiempo."""

    atributos: dict[str, Decimal]
    origen: Literal["proveedor", "cache", "vencido"]
    edad_segundos: float = 0.0
    causa: CausaDegradacion | None = None


@runtime_checkable
class AdaptadorConOrigen(Protocol):
    """Adaptador que, ademas de los atributos, dice de donde los saco. Lo implementa el
    decorador con cache y circuit breaker; los stubs y un proveedor directo no lo necesitan."""

    async def obtener_resuelto(self, cliente_id: str) -> PerfilResuelto: ...


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
