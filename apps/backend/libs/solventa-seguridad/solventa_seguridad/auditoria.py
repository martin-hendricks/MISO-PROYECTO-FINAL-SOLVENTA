from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

logger = logging.getLogger("solventa.auditoria")


def registrar_rechazo(
    *,
    accion: str,
    motivo: str,
    usuario: str | None = None,
    rol: str | None = None,
    correlacion: str | None = None,
) -> None:
    logger.warning(
        json.dumps(
            {
                "evento": "acceso_denegado",
                "usuario": usuario,
                "rol": rol,
                "accion": accion,
                "motivo": motivo,
                "correlacion": correlacion,
                "ts": datetime.now(UTC).isoformat(),
            },
            ensure_ascii=False,
        )
    )
