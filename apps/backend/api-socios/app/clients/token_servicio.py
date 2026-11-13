from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

VIGENCIA = timedelta(minutes=5)


def token_de_socio(secreto: str, uid: str, ahora: datetime | None = None) -> str:
    """Token de servicio con rol `socio`: ms-identidad solo le permite resolver documentos."""
    if not secreto:
        raise ValueError("SOLVENTA_TOKEN_SECRET no configurado")
    emitido = ahora or datetime.now(UTC)
    return jwt.encode(
        {"sub": "api-socios", "uid": uid, "rol": "socio", "typ": "access", "exp": emitido + VIGENCIA},
        secreto,
        algorithm="HS256",
    )
