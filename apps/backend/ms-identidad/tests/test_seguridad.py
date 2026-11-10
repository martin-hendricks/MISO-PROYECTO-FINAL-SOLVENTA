from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.seguridad import Llamante, alcance, exigir_backoffice, exigir_llamante, exigir_operador

UID = UUID("11111111-1111-1111-1111-111111111111")
OTRO = UUID("22222222-2222-2222-2222-222222222222")


def _token(**extra) -> str:
    payload = {
        "sub": "persona@correo.com",
        "uid": str(UID),
        "rol": "cliente",
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


def test_cliente_ajeno_responde_404():
    llamante = Llamante(uid=UID, rol="cliente", sub="persona@correo.com")
    with pytest.raises(HTTPException) as exc:
        alcance(llamante, OTRO)
    assert exc.value.status_code == 404


def test_rol_desconocido_responde_403():
    llamante = Llamante(uid=UID, rol="visitante", sub="persona@correo.com")
    with pytest.raises(HTTPException) as exc:
        alcance(llamante, UID)
    assert exc.value.status_code == 403


def test_operador_conserva_el_usuario_pedido():
    llamante = Llamante(uid=UID, rol="operador", sub="operador@solventa.com")
    assert alcance(llamante, OTRO) == OTRO


@pytest.mark.parametrize("rol", ["operador", "asesor"])
def test_exigir_backoffice_acepta_operador_y_asesor(rol):
    llamante = Llamante(uid=UID, rol=rol, sub="persona@correo.com")
    assert exigir_backoffice(llamante) is llamante


@pytest.mark.parametrize("rol", ["cliente", "visitante"])
def test_exigir_backoffice_rechaza_otros_roles(rol):
    llamante = Llamante(uid=UID, rol=rol, sub="persona@correo.com")
    with pytest.raises(HTTPException) as exc:
        exigir_backoffice(llamante)
    assert exc.value.status_code == 403


def test_exigir_operador_acepta_operador():
    llamante = Llamante(uid=UID, rol="operador", sub="operador@solventa.com")
    assert exigir_operador(llamante) is llamante


@pytest.mark.parametrize("rol", ["asesor", "cliente"])
def test_exigir_operador_rechaza_asesor_y_cliente(rol):
    llamante = Llamante(uid=UID, rol=rol, sub="persona@correo.com")
    with pytest.raises(HTTPException) as exc:
        exigir_operador(llamante)
    assert exc.value.status_code == 403
