from __future__ import annotations

from hashlib import sha256
from uuid import UUID

from app.ports.firma import ResultadoFirma

MOTIVO_RECHAZO = "El prestador de firma (stub) rechazó la firma"


class FirmaStub:
    """HU-17: firma simulada, sin prestador ni documento firmado. Responde
    siempre lo configurado (`ok` / `no`); el hash es determinista por oferta
    para que un reintento produzca la misma constancia."""

    def __init__(self, resultado: str) -> None:
        if resultado not in ("ok", "no"):
            raise ValueError(f"Resultado de firma no soportado: {resultado!r}")
        self._exitosa = resultado == "ok"

    async def firmar(self, oferta_id: UUID) -> ResultadoFirma:
        if not self._exitosa:
            return ResultadoFirma(exitosa=False, motivo=MOTIVO_RECHAZO)
        return ResultadoFirma(exitosa=True, firma_hash=sha256(f"stub:{oferta_id}".encode()).hexdigest())
