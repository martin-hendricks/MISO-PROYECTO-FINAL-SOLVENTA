from __future__ import annotations

from typing import Protocol


class ConsultaPerfilamiento(Protocol):
    """Puerto hacia ms-perfilamiento: consentimiento de perfilamiento
    hipotecario (HU-53) y originación hipotecaria abierta -- ambos datos
    viven en ESE servicio, no en ms-consentimiento (ver app/ports/
    consentimiento.py para el habeas data general, un consentimiento
    distinto e independiente)."""

    async def tiene_originacion_pendiente(self, cliente_id: str) -> bool:
        """True si GET /v1/originaciones/clientes/{cliente_id}/pendiente de
        ms-perfilamiento devuelve una Originacion con cerrada_en IS NULL.
        False si responde 404 (sin originación abierta)."""
        ...
