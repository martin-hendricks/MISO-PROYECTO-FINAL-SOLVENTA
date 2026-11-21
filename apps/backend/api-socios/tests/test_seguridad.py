import hashlib
import json
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import Settings
from app.seguridad import exigir_alcance, exigir_api_key_socio

API_KEY = "clave-test-socio"
SOCIO_ID = "6f1c2a4e-0000-4000-8000-000000000001"
OTRO_SOCIO_ID = "6f1c2a4e-0000-4000-8000-000000000002"


def _huella(clave: str) -> str:
    return hashlib.sha256(clave.encode()).hexdigest()


def _socio(socio_id: str = SOCIO_ID, claves: tuple[str, ...] = (API_KEY,), alcances=("catalogo:leer",)) -> dict:
    return {
        "socio_id": socio_id,
        "nombre": f"Socio {socio_id[-1]}",
        "alcances": list(alcances),
        "api_keys_sha256": [_huella(c) for c in claves],
    }


def _request(*socios: dict) -> SimpleNamespace:
    config = Settings(socios=list(socios))
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(config=config)))


def test_sin_cabecera_responde_401():
    with pytest.raises(HTTPException) as exc:
        exigir_api_key_socio(_request(_socio()), None)

    assert exc.value.status_code == 401


def test_api_key_invalida_responde_401():
    with pytest.raises(HTTPException) as exc:
        exigir_api_key_socio(_request(_socio()), "clave-que-no-existe")

    assert exc.value.status_code == 401


def test_api_key_valida_resuelve_el_socio_con_sus_alcances():
    socio = exigir_api_key_socio(_request(_socio()), API_KEY)

    assert socio.socio_id == UUID(SOCIO_ID)
    assert socio.nombre == "Socio 1"
    assert socio.alcances == frozenset({"catalogo:leer"})


def test_varios_socios_cada_uno_con_su_clave():
    request = _request(_socio(), _socio(OTRO_SOCIO_ID, ("otra-clave",)))

    assert exigir_api_key_socio(request, API_KEY).socio_id == UUID(SOCIO_ID)
    assert exigir_api_key_socio(request, "otra-clave").socio_id == UUID(OTRO_SOCIO_ID)


def test_rotacion_dos_claves_vigentes_del_mismo_socio():
    request = _request(_socio(claves=("clave-vieja", "clave-nueva")))

    assert exigir_api_key_socio(request, "clave-vieja").socio_id == UUID(SOCIO_ID)
    assert exigir_api_key_socio(request, "clave-nueva").socio_id == UUID(SOCIO_ID)


def test_la_clave_en_claro_no_sirve_como_huella():
    request = _request(_socio())

    with pytest.raises(HTTPException) as exc:
        exigir_api_key_socio(request, _huella(API_KEY))

    assert exc.value.status_code == 401


def test_sin_socios_configurados_cualquier_clave_es_401():
    with pytest.raises(HTTPException) as exc:
        exigir_api_key_socio(_request(), API_KEY)

    assert exc.value.status_code == 401


def test_socio_sin_el_alcance_responde_403():
    socio = exigir_api_key_socio(_request(_socio(alcances=("catalogo:leer",))), API_KEY)

    with pytest.raises(HTTPException) as exc:
        exigir_alcance("originaciones:escribir")(socio)

    assert exc.value.status_code == 403


def test_socio_con_el_alcance_pasa():
    socio = exigir_api_key_socio(_request(_socio()), API_KEY)

    assert exigir_alcance("catalogo:leer")(socio) is socio


def test_el_registro_se_lee_como_json_desde_el_entorno(monkeypatch):
    monkeypatch.setenv("SOCIOS", json.dumps([_socio()]))

    config = Settings()

    assert config.socios[0].socio_id == UUID(SOCIO_ID)


@pytest.mark.parametrize(
    "cambio",
    [
        {"socio_id": "aliado-banco"},
        {"api_keys_sha256": ["no-es-un-sha256"]},
        {"api_keys_sha256": []},
        {"alcances": ["catalogo:borrar"]},
    ],
)
def test_entrada_invalida_falla_al_arrancar(cambio):
    with pytest.raises(ValidationError):
        Settings(socios=[{**_socio(), **cambio}])


def test_socio_id_duplicado_falla_al_arrancar():
    with pytest.raises(ValidationError):
        Settings(socios=[_socio(claves=("a",)), _socio(claves=("b",))])


def test_misma_clave_en_dos_socios_falla_al_arrancar():
    with pytest.raises(ValidationError):
        Settings(socios=[_socio(), _socio(OTRO_SOCIO_ID)])
