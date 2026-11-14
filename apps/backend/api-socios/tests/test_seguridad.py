from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.config import Settings
from app.seguridad import exigir_api_key_socio

API_KEY = "clave-test-socio"
SOCIO_ID = "socio-test"


def _request(socios_api_keys: str) -> SimpleNamespace:
    config = Settings(socios_api_keys=socios_api_keys)
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(config=config)))


def test_sin_cabecera_responde_401():
    request = _request(f"{SOCIO_ID}:{API_KEY}")

    with pytest.raises(HTTPException) as exc:
        exigir_api_key_socio(request, None)

    assert exc.value.status_code == 401


def test_api_key_invalida_responde_401():
    request = _request(f"{SOCIO_ID}:{API_KEY}")

    with pytest.raises(HTTPException) as exc:
        exigir_api_key_socio(request, "clave-que-no-existe")

    assert exc.value.status_code == 401


def test_api_key_valida_resuelve_el_socio():
    request = _request(f"{SOCIO_ID}:{API_KEY}")

    socio = exigir_api_key_socio(request, API_KEY)

    assert socio.socio_id == SOCIO_ID


def test_varios_socios_configurados_cada_uno_con_su_clave():
    request = _request(f"{SOCIO_ID}:{API_KEY},otro-socio:otra-clave")

    assert exigir_api_key_socio(request, API_KEY).socio_id == SOCIO_ID
    assert exigir_api_key_socio(request, "otra-clave").socio_id == "otro-socio"


def test_sin_ninguna_api_key_configurada_cualquier_clave_es_401():
    request = _request("")

    with pytest.raises(HTTPException) as exc:
        exigir_api_key_socio(request, API_KEY)

    assert exc.value.status_code == 401
