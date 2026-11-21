"""Evento canónico de telemetría: el único formato que viaja por TopicoTelemetria.

Ningún esquema de proveedor cruza este límite (capa anticorrupción, :AdaptadorTelemetria):
cada adaptador traduce al EventoTelemetria y el consumidor (ms-siniestros) solo conoce
este contrato. Agregar o sustituir un proveedor no toca al consumidor (EC-MOD-05).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

VERSION_CONTRATO = 1


class EventoInvalido(Exception):
    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


@dataclass(frozen=True)
class Cobertura:
    """Datos de la póliza que el proveedor reporta junto con la medición.

    Simplificación vigente (igual que el POST /v1/eventos-parametricos de ms-siniestros):
    el umbral y el monto llegan del emisor. La versión objetivo los resuelve contra una
    proyección local de pólizas paramétricas; ver README, "Fuera de alcance"."""

    umbral: Decimal
    monto: Decimal
    vigente: bool = True
    poliza_id: UUID | None = None
    poliza_numero: str | None = None
    usuario_id: UUID | None = None


@dataclass(frozen=True)
class EventoTelemetria:
    evento_id: str
    proveedor: str
    tipo: str
    valor: Decimal
    ocurrido_en: datetime
    ramo: str
    descripcion: str
    cobertura: Cobertura
    recibido_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.evento_id.strip():
            raise EventoInvalido("evento_sin_id", "El evento requiere un identificador")
        if self.cobertura.monto <= 0:
            raise EventoInvalido("monto_no_positivo", "El monto de la cobertura debe ser mayor que cero")

    @staticmethod
    def clave(proveedor: str, id_externo: str) -> str:
        """Clave de idempotencia: el id del proveedor con su prefijo, para que dos
        proveedores con ids iguales no colisionen. Es también la key del mensaje: todas
        las entregas de un mismo evento caen en la misma partición y se procesan en orden."""
        return f"{proveedor}:{id_externo.strip()}"

    def a_mensaje(self) -> dict:
        c = self.cobertura
        return {
            "version": VERSION_CONTRATO,
            "evento_id": self.evento_id,
            "proveedor": self.proveedor,
            "tipo": self.tipo,
            "valor": str(self.valor),
            "ocurrido_en": self.ocurrido_en.isoformat(),
            "recibido_en": self.recibido_en.isoformat(),
            "ramo": self.ramo,
            "descripcion": self.descripcion,
            "cobertura": {
                "umbral": str(c.umbral),
                "monto": str(c.monto),
                "vigente": c.vigente,
                "poliza_id": str(c.poliza_id) if c.poliza_id else None,
                "poliza_numero": c.poliza_numero,
                "usuario_id": str(c.usuario_id) if c.usuario_id else None,
            },
        }
