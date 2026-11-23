from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada

TIPO_HABEAS_DATA = "habeas_data"
"""Único tipo de consentimiento que existe hoy en este servicio (Ley 1581 /
habeas data). No viaja en el contrato HTTP porque no hay otro valor posible
todavía: fijarlo aquí, en el dominio, evita inventar un campo de entrada que
el resto del sistema tendría que validar sin necesidad real."""


@dataclass
class Consentimiento:
    """Consentimiento de HABEAS DATA (Ley 1581 colombiana) de un cliente.

    IMPORTANTE — esto es un STUB explícito, no una integración legal real:
    - No versiona el texto/política legal que el cliente aceptó (no hay
      `version_politica` ni snapshot del documento firmado). Solo registra
      el hecho "otorgado" / "revocado" con su marca de tiempo.
    - No propaga la revocación por eventos de dominio ni outbox: no cumple
      por sí solo el ASR EC-SEG-03 (revocación efectiva propagada en <=5
      minutos a todo el sistema). Quien consuma este servicio (ms-identidad,
      y a través de él otros microservicios) debe consultar el endpoint de
      lectura directamente; no hay `ConsentimientoRevocado` que escuchar.
    - Su única responsabilidad real es exponer, de forma simple e
      idempotente, si un cliente tiene o no consentimiento vigente — el dato
      mínimo que el resto de la plataforma necesita hoy.
    """

    id: UUID
    cliente_id: str
    otorgado_en: datetime
    revocado_en: datetime | None

    @classmethod
    def otorgar(cls, cliente_id: str) -> Consentimiento:
        if not cliente_id.strip():
            raise ReglaDeNegocioViolada("cliente_id_vacio", "El cliente_id es obligatorio")
        return cls(id=uuid4(), cliente_id=cliente_id.strip(), otorgado_en=datetime.now(UTC), revocado_en=None)

    @property
    def vigente(self) -> bool:
        return self.revocado_en is None

    def revocar(self) -> None:
        if self.revocado_en is None:
            self.revocado_en = datetime.now(UTC)
