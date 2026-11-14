from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

VIGENCIA = timedelta(minutes=5)


def token_de_servicio(secreto: str, nombre_servicio: str, ahora: datetime | None = None) -> str:
    """Token para llamadas service-to-service (ms-identidad -> ms-consentimiento,
    ms-cotizacion -> ms-perfilamiento, etc.): rol `servicio`, sin usuario humano
    detrás. Mismo formato que `api-socios/app/clients/token_servicio.py`
    (rol `socio`): un microservicio que llama a otro se autentica con esto
    en vez de ir sin ningún header, como ocurría antes de esta HU."""
    if not secreto:
        raise ValueError("SOLVENTA_TOKEN_SECRET no configurado")
    emitido = ahora or datetime.now(UTC)
    return jwt.encode(
        {"sub": nombre_servicio, "uid": nombre_servicio, "rol": "servicio", "typ": "access", "exp": emitido + VIGENCIA},
        secreto,
        algorithm="HS256",
    )
