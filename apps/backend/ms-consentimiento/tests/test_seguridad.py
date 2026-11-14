import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.seguridad import exigir_llamante

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")


def _token(**extra) -> str:
    payload = {
        "sub": "persona@correo.com",
        "rol": "asesor",
        "typ": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    payload.update(extra)
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def test_sin_secreto_responde_500(monkeypatch):
    monkeypatch.delenv("SOLVENTA_TOKEN_SECRET", raising=False)
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token())
    with pytest.raises(HTTPException) as exc:
        exigir_llamante(credenciales)
    assert exc.value.status_code == 500


def test_sin_token_responde_401():
    with pytest.raises(HTTPException) as exc:
        exigir_llamante(None)
    assert exc.value.status_code == 401


def test_token_ilegible_responde_401():
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials="no-es-un-jwt")
    with pytest.raises(HTTPException) as exc:
        exigir_llamante(credenciales)
    assert exc.value.status_code == 401


def test_token_que_no_es_acceso_responde_401():
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token(typ="refresh"))
    with pytest.raises(HTTPException) as exc:
        exigir_llamante(credenciales)
    assert exc.value.status_code == 401


def test_rol_no_reconocido_responde_401():
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token(rol="desconocido"))
    with pytest.raises(HTTPException) as exc:
        exigir_llamante(credenciales)
    assert exc.value.status_code == 401


def test_rol_servicio_es_valido():
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token(rol="servicio", sub="ms-identidad"))
    llamante = exigir_llamante(credenciales)
    assert llamante.rol == "servicio"
    assert llamante.sub == "ms-identidad"
