from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

VIGENCIA = timedelta(minutes=5)


def token_de_servicio(secreto: str, nombre_servicio: str, ahora: datetime | None = None) -> str:
    """Token para llamadas service-to-service (ms-pagos -> ms-suscripcion al
    verificar la decisión de la solicitud): rol `servicio`, sin usuario humano
    detrás. Mismo formato que `ms-cotizacion/app/infrastructure/token_servicio.py`:
    un microservicio que llama a otro se autentica con esto en vez de ir sin
    ningún header."""
    if not secreto:
        raise ValueError("SOLVENTA_TOKEN_SECRET no configurado")
    emitido = ahora or datetime.now(UTC)
    return jwt.encode(
        {"sub": nombre_servicio, "uid": nombre_servicio, "rol": "servicio", "typ": "access", "exp": emitido + VIGENCIA},
        secreto,
        algorithm="HS256",
    )
