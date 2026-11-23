from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.domain.modelos import Poliza


@dataclass(frozen=True)
class ReporteGenerado:
    """HU-62/HU-63: el núcleo nunca produce el formato SFC/ACORD real -- el
    adaptador decide la forma del archivo. `contenido` es el extracto en
    bruto (hoy un CSV en memoria vía el stub); un prestador real devolvería
    aquí la referencia/URL de lo que haya generado, con el mismo contrato."""

    nombre_archivo: str
    tipo_contenido: str
    contenido: str


class GeneradorReportes(Protocol):
    """HU-62: extracto interno de pólizas para el regulador, nunca el
    formato SFC real -- solo la implementación cambia si se integra un
    prestador real."""

    async def reporte_regulador(self, polizas: list[Poliza], desde: date, hasta: date) -> ReporteGenerado: ...

    # HU-63: extracto de cartera/siniestralidad para la reaseguradora, nunca
    # el formato ACORD real.
    async def reporte_reaseguradora(
        self, canceladas: list[Poliza], desde: date, hasta: date
    ) -> ReporteGenerado: ...
