from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

CAMPOS_OBLIGATORIOS = ("evento_id", "tipo", "agregado_id", "payload")


@dataclass(frozen=True)
class EventoBus:
    """Evento de dominio tal como viaja por `BusEventos` (MSK).

    Mismo contrato que apps/backend/notificaciones/app/domain/eventos.py --
    cada servicio consumidor es independiente, sin import cruzado en este repo.
    """

    evento_id: UUID
    tipo: str
    agregado_id: UUID
    ocurrido_en: datetime | None
    origen: str | None
    payload: dict

    @classmethod
    def desde_mensaje(cls, valor: bytes | str | dict) -> EventoBus | None:
        """Parsea un mensaje del bus.

        Devuelve `None` cuando el JSON es válido pero no representa un evento
        utilizable (no es un objeto o `payload` no es un diccionario); lanza
        `ValueError` cuando el JSON es inválido o faltan campos obligatorios.
        """
        if isinstance(valor, (bytes, bytearray, memoryview)):
            crudo = bytes(valor).decode("utf-8")
        elif isinstance(valor, str):
            crudo = valor
        elif isinstance(valor, dict):
            crudo = valor
        else:
            raise ValueError("El mensaje del bus debe ser bytes, str o dict")

        datos = json.loads(crudo) if isinstance(crudo, str) else crudo
        if not isinstance(datos, dict):
            return None

        faltantes = [campo for campo in CAMPOS_OBLIGATORIOS if campo not in datos]
        if faltantes:
            raise ValueError(f"Evento del bus sin campos obligatorios: {', '.join(faltantes)}")

        payload = datos["payload"]
        if not isinstance(payload, dict):
            return None

        return cls(
            evento_id=UUID(str(datos["evento_id"])),
            tipo=str(datos["tipo"]),
            agregado_id=UUID(str(datos["agregado_id"])),
            ocurrido_en=_fecha(datos.get("ocurrido_en")),
            origen=_texto(datos.get("origen")),
            payload=payload,
        )


def _texto(valor: object) -> str | None:
    if isinstance(valor, str) and valor.strip():
        return valor.strip()
    return None


def _fecha(valor: object) -> datetime | None:
    """`ocurrido_en` es opcional; un valor ilegible no debe frenar la partición."""
    if not isinstance(valor, str) or not valor.strip():
        return None
    try:
        return datetime.fromisoformat(valor.strip())
    except ValueError:
        return None
