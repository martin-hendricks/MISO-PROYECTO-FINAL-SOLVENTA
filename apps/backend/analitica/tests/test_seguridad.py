from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.seguridad import exigir_llamante

UID = UUID("11111111-1111-1111-1111-111111111111")


def _token(**extra) -> str:
    payload = {
        "sub": "persona@correo.com",
        "uid": str(UID),
        "rol": "operador",
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


def test_token_sin_uid_responde_401():
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token(uid=None))
    with pytest.raises(HTTPException) as exc:
        exigir_llamante(credenciales)
    assert exc.value.status_code == 401


def test_rol_desconocido_responde_401():
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token(rol="visitante"))
    with pytest.raises(HTTPException) as exc:
        exigir_llamante(credenciales)
    assert exc.value.status_code == 401


def test_token_valido_devuelve_llamante():
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token())
    llamante = exigir_llamante(credenciales)
    assert llamante.uid == UID
    assert llamante.rol == "operador"
