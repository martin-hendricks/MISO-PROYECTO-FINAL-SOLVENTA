from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .errores import ReglaDeNegocioViolada

TIPOS_SOPORTADOS = frozenset(
    {"PolizaEmitida", "PolizaRenovada", "PolizaModificada", "PolizaCancelada", "PolizaPorVencer"}
)


@dataclass
class ConteoEventos:
    """Un contador agregado de eventos de un tipo en un día concreto.

    `cantidad` se incrementa en memoria antes de persistir; el repositorio SQL
    hace el upsert real (insertar en 1, o sumar 1 sobre la fila existente).
    """

    tipo: str
    fecha: date
    cantidad: int

    @classmethod
    def crear(cls, tipo: str, fecha: date) -> ConteoEventos:
        if tipo not in TIPOS_SOPORTADOS:
            raise ReglaDeNegocioViolada("tipo_invalido", f"Tipo de evento '{tipo}' no soportado")
        return cls(tipo=tipo, fecha=fecha, cantidad=1)
