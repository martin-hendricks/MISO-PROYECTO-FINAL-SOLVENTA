from datetime import UTC, datetime, timedelta
from decimal import Decimal


class RelojFijo:
    def __init__(self, instante: datetime = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)) -> None:
        self.instante = instante

    def ahora(self) -> datetime:
        return self.instante

    def avanzar(self, delta: timedelta) -> None:
        self.instante += delta


class PrimaEspia:
    """Doble de HU-4: registra con qué datos se le llamó."""

    def __init__(self, prima: Decimal = Decimal("100000")) -> None:
        self.prima = prima
        self.llamadas: list[dict] = []

    async def calcular(self, producto, datos_riesgo):
        self.llamadas.append(dict(datos_riesgo))
        return self.prima


class FactorEspia:
    """Doble de HU-5: registra con qué datos se le llamó."""

    def __init__(self, factor: Decimal = Decimal("1.15")) -> None:
        self.factor = factor
        self.llamadas: list[dict] = []

    async def obtener(self, producto, datos_riesgo):
        self.llamadas.append(dict(datos_riesgo))
        return self.factor
