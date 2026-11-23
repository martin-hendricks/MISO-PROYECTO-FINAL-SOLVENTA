"""Autenticación del proveedor de telemetría por credenciales de cliente.

El canal de telemetría no es un usuario de Solventa: no usa el JWT de los BFF. Usa el
par clientId/clientSecret del secreto telemetria_iot que Terraform ya provisiona. La
comparación es en tiempo constante. La firma HMAC por mensaje o el mTLS por proveedor
quedan como evolución (README, "Fuera de alcance").
"""

import hmac
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from app.config import Settings


def exigir_proveedor(
    request: Request,
    cliente: Annotated[str | None, Header(alias="X-Telemetria-Cliente")] = None,
    secreto: Annotated[str | None, Header(alias="X-Telemetria-Secreto")] = None,
) -> str:
    config: Settings = request.app.state.config
    if not config.telemetria_client_id or not config.telemetria_client_secret:
        raise HTTPException(status_code=500, detail="Credenciales de telemetría no configuradas")
    if cliente is None or secreto is None:
        raise HTTPException(status_code=401, detail="Credenciales de telemetría requeridas")
    cliente_ok = hmac.compare_digest(cliente.encode(), config.telemetria_client_id.encode())
    secreto_ok = hmac.compare_digest(secreto.encode(), config.telemetria_client_secret.encode())
    if not (cliente_ok and secreto_ok):
        raise HTTPException(status_code=401, detail="Credenciales de telemetría inválidas")
    return cliente


ProveedorAutenticado = Annotated[str, Depends(exigir_proveedor)]
