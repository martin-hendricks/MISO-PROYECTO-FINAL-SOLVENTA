from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from .base import ClienteServicio


class ClienteMsSuscripcion(ClienteServicio):
    """Cliente de ms-suscripcion.

    El flujo de cliente (routers/cliente.py) nunca llama aquí directo:
    ms-cotizacion ya orquesta la decisión de suscripción internamente al
    aceptar una oferta. Este cliente existe para el flujo de asesor
    (routers/asesor.py), que necesita consultar la decisión de suscripción
    SIN pasar por la aceptación/emisión del canal cliente -- evaluar() es
    idempotente por solicitud_id (ver app/api/v1/rutas.py de ms-suscripcion),
    así que "consultar" y "evaluar" son la misma llamada: un reintento
    devuelve la decisión ya persistida sin volver a calcularla.
    """

    nombre = "ms-suscripcion"

    async def evaluar(self, solicitud_id: UUID, perfil_id: UUID, score: Decimal) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            "/v1/suscripciones",
            json={
                "solicitud_id": str(solicitud_id),
                "perfil_id": str(perfil_id),
                "score": str(score),
            },
        )
