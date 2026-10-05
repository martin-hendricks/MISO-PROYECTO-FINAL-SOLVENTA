import logging

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.seguridad import (
    ValidadorJWT,
    configurar_seguridad,
    identidad_actual,
    requiere_alcance,
)

from .emisor import EmisorDePrueba

emisor = EmisorDePrueba()


def _app(con_validador: bool = True) -> FastAPI:
    app = FastAPI()
    validador = ValidadorJWT(emisor.llave_publica_pem, emisor.emisor, emisor.audiencia)
    configurar_seguridad(app, validador if con_validador else None)
    router = APIRouter(dependencies=[Depends(identidad_actual)])

    @router.get("/yo")
    async def yo(identidad=Depends(identidad_actual)):
        return {"sujeto": identidad.sujeto, "rol": identidad.rol}

    @router.get("/reportes", dependencies=[Depends(requiere_alcance("reportes:leer"))])
    async def reportes():
        return {"ok": True}

    app.include_router(router)
    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_app())


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_sin_token_es_401(client):
    respuesta = client.get("/yo")
    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": "No autorizado"}


def test_token_valido_pasa(client):
    respuesta = client.get("/yo", headers=_auth(emisor.emitir("USR-1", "cliente")))
    assert respuesta.status_code == 200
    assert respuesta.json() == {"sujeto": "USR-1", "rol": "cliente"}


def test_expirado_es_401_sin_detalles(client):
    respuesta = client.get("/yo", headers=_auth(emisor.emitir(expira_en=-120)))
    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": "No autorizado"}


def test_alcance_insuficiente_es_403(client):
    sin = client.get("/reportes", headers=_auth(emisor.emitir(rol="asesor")))
    con = client.get("/reportes", headers=_auth(emisor.emitir(rol="asesor", alcances=("reportes:leer",))))
    assert (sin.status_code, con.status_code) == (403, 200)


def test_rechazo_se_audita_sin_escribir_el_token(client, caplog):
    token = emisor.emitir("USR-7", expira_en=-120)
    with caplog.at_level(logging.WARNING, logger="solventa.auditoria"):
        client.get("/yo", headers={**_auth(token), "X-Correlation-Id": "c-1"})

    registro = caplog.text
    assert "expirado" in registro and "GET /yo" in registro and "c-1" in registro
    assert token not in registro


def test_sin_validador_falla_cerrado():
    respuesta = TestClient(_app(con_validador=False)).get("/yo", headers=_auth(emisor.emitir()))
    assert respuesta.status_code == 503
