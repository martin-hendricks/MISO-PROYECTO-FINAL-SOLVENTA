from __future__ import annotations

from typing import Protocol


class ConsultaConsentimiento(Protocol):
    """Puerto hacia ms-consentimiento (habeas data), un servicio DISTINTO del
    consentimiento de perfilamiento hipotecario (ver app/ports/perfilamiento.py).

    Contrato acordado con el otro equipo (en construcción en paralelo, rama
    separada): GET /v1/consentimientos/{cliente_id} responde 200 con
    {"vigente": true, "revocado_en": null, ...} si hay un consentimiento
    habeas_data vigente, o 404 si el cliente nunca otorgó uno o si el que
    tenía fue revocado -- el contrato NO distingue esos dos casos en el 404.
    Este puerto no necesita distinguirlos tampoco: `vigente()` solo contesta
    True/False, y la capa de aplicación (ver casos_uso_clientes.py) trata
    cualquier False como "no hay habeas data vigente" sin más matiz."""

    async def vigente(self, cliente_id: str) -> bool:
        """True si ms-consentimiento confirma un habeas data vigente (200,
        vigente=true). False si responde 404 (nunca otorgado o revocado --
        el contrato no distingue) o si vigente=false explícito."""
        ...
