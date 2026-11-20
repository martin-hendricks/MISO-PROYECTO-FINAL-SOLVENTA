import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import jwt
import pytest

from tests.conftest import token_de

MIGRACION = Path(__file__).resolve().parents[1] / "db" / "07_ms_identidad_socios.sql"
SOCIO_POR_DEFECTO = (
    Path(__file__).resolve().parents[1] / "db" / "08_ms_identidad_socio_default.sql"
)
ALTA = {
    "nombre": "Banco Aliado",
    "alcances": ["catalogo:leer", "cotizaciones:escribir"],
}


def _auth(rol: str) -> dict:
    return {"Authorization": f"Bearer {token_de(str(uuid4()), rol)}"}


def _auth_api_socios(sub: str = "api-socios") -> dict:
    token = jwt.encode(
        {
            "sub": sub,
            "uid": "00000000-0000-0000-0000-000000000000",
            "rol": "socio",
            "typ": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _huella(clave: str) -> str:
    return hashlib.sha256(clave.encode()).hexdigest()


def _alta(client, **cambios):
    respuesta = client.post("/v1/socios", json={**ALTA, **cambios})
    assert respuesta.status_code == 201
    return respuesta.json()


def _resolver(client, clave: str):
    return client.post(
        "/v1/socios/resolucion",
        json={"huella_sha256": _huella(clave)},
        headers=_auth_api_socios(),
    )


def test_operador_crea_socio_y_recibe_la_clave_una_sola_vez(client, almacen):
    creado = _alta(client)

    assert UUID(creado["socio_id"])
    assert creado["nombre"] == "Banco Aliado"
    assert sorted(creado["alcances"]) == ["catalogo:leer", "cotizaciones:escribir"]
    assert creado["estado"] == "activo"
    assert len(creado["api_key"]) >= 32
    [socio] = almacen.socios.values()
    [credencial] = socio.credenciales
    assert credencial.huella_sha256 == _huella(creado["api_key"])
    assert creado["api_key"] not in repr(socio)


def test_el_listado_no_expone_claves_ni_huellas(client):
    creado = _alta(client)

    respuesta = client.get("/v1/socios")

    assert respuesta.status_code == 200
    [socio] = respuesta.json()["socios"]
    assert socio["socio_id"] == creado["socio_id"]
    texto = respuesta.text
    assert creado["api_key"] not in texto
    assert _huella(creado["api_key"]) not in texto
    assert [c["credencial_id"] for c in socio["credenciales"]] == [
        creado["credencial_id"]
    ]


@pytest.mark.parametrize("rol", ["asesor", "cliente", "socio"])
def test_solo_el_operador_administra_socios(client, almacen, rol):
    socio_id = str(uuid4())
    llamadas = [
        client.post("/v1/socios", json=ALTA, headers=_auth(rol)),
        client.get("/v1/socios", headers=_auth(rol)),
        client.post(f"/v1/socios/{socio_id}/credenciales", headers=_auth(rol)),
        client.delete(
            f"/v1/socios/{socio_id}/credenciales/{uuid4()}", headers=_auth(rol)
        ),
        client.post(f"/v1/socios/{socio_id}/revocacion", headers=_auth(rol)),
    ]

    assert [r.status_code for r in llamadas] == [403] * 5
    assert almacen.socios == {}


def test_sin_token_es_401(client):
    respuesta = client.post("/v1/socios", json=ALTA, headers={"Authorization": ""})

    assert respuesta.status_code == 401


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"nombre": "", "alcances": ["catalogo:leer"]},
        {"nombre": "Aliado", "alcances": []},
        {"nombre": "Aliado", "alcances": ["polizas:borrar"]},
        {
            "nombre": "Aliado",
            "alcances": ["catalogo:leer"],
            "api_keys_sha256": ["a" * 64],
        },
    ],
)
def test_alta_invalida_es_422_y_no_guarda(client, almacen, cuerpo):
    assert client.post("/v1/socios", json=cuerpo).status_code == 422
    assert almacen.socios == {}


def test_api_socios_resuelve_el_socio_por_huella(client):
    creado = _alta(client)

    respuesta = _resolver(client, creado["api_key"])

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "socio_id": creado["socio_id"],
        "nombre": "Banco Aliado",
        "alcances": sorted(ALTA["alcances"]),
    }


def test_huella_desconocida_es_404(client):
    _alta(client)

    assert _resolver(client, "clave-que-no-existe").status_code == 404


@pytest.mark.parametrize("rol", ["operador", "asesor", "cliente"])
def test_la_resolucion_solo_la_invoca_api_socios(client, rol):
    creado = _alta(client)

    respuesta = client.post(
        "/v1/socios/resolucion",
        json={"huella_sha256": _huella(creado["api_key"])},
        headers=_auth(rol),
    )

    assert respuesta.status_code == 403


def test_un_token_socio_que_no_emitio_api_socios_no_resuelve(client):
    creado = _alta(client)

    respuesta = client.post(
        "/v1/socios/resolucion",
        json={"huella_sha256": _huella(creado["api_key"])},
        headers=_auth_api_socios(sub="otro-servicio"),
    )

    assert respuesta.status_code == 403


def test_resolucion_con_huella_mal_formada_es_422(client):
    respuesta = client.post(
        "/v1/socios/resolucion",
        json={"huella_sha256": "ABC"},
        headers=_auth_api_socios(),
    )

    assert respuesta.status_code == 422


def test_rotacion_emite_clave_nueva_y_ambas_valen_hasta_revocar_la_anterior(client):
    creado = _alta(client)

    nueva = client.post(f"/v1/socios/{creado['socio_id']}/credenciales")

    assert nueva.status_code == 201
    clave_nueva = nueva.json()["api_key"]
    assert clave_nueva != creado["api_key"]
    assert _resolver(client, creado["api_key"]).status_code == 200
    assert _resolver(client, clave_nueva).status_code == 200

    baja = client.delete(
        f"/v1/socios/{creado['socio_id']}/credenciales/{creado['credencial_id']}"
    )

    assert baja.status_code == 204
    assert _resolver(client, creado["api_key"]).status_code == 404
    assert _resolver(client, clave_nueva).status_code == 200


def test_revocar_socio_invalida_todas_sus_claves(client):
    creado = _alta(client)
    nueva = client.post(f"/v1/socios/{creado['socio_id']}/credenciales").json()[
        "api_key"
    ]

    respuesta = client.post(f"/v1/socios/{creado['socio_id']}/revocacion")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "revocado"
    assert _resolver(client, creado["api_key"]).status_code == 404
    assert _resolver(client, nueva).status_code == 404
    assert (
        client.post(f"/v1/socios/{creado['socio_id']}/credenciales").status_code == 409
    )


def test_revocar_es_idempotente(client):
    creado = _alta(client)

    client.post(f"/v1/socios/{creado['socio_id']}/revocacion")
    segunda = client.post(f"/v1/socios/{creado['socio_id']}/revocacion")

    assert segunda.status_code == 200
    assert segunda.json()["estado"] == "revocado"


def test_socio_o_credencial_inexistente_es_404(client):
    creado = _alta(client)

    assert client.post(f"/v1/socios/{uuid4()}/credenciales").status_code == 404
    assert client.post(f"/v1/socios/{uuid4()}/revocacion").status_code == 404
    assert (
        client.delete(
            f"/v1/socios/{creado['socio_id']}/credenciales/{uuid4()}"
        ).status_code
        == 404
    )


def test_un_socio_no_revoca_la_credencial_de_otro(client):
    uno = _alta(client)
    otro = _alta(client, nombre="Comparador")

    respuesta = client.delete(
        f"/v1/socios/{otro['socio_id']}/credenciales/{uno['credencial_id']}"
    )

    assert respuesta.status_code == 404
    assert _resolver(client, uno["api_key"]).status_code == 200


def test_la_migracion_crea_las_tablas_sin_tocar_datos_existentes():
    texto = MIGRACION.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS ms_identidad.socio " in texto
    assert "CREATE TABLE IF NOT EXISTS ms_identidad.credencial_socio " in texto
    assert "huella_sha256" in texto
    for prohibido in ("UPDATE", "DELETE", "DROP", "ALTER TABLE ms_identidad.usuario"):
        assert prohibido.upper() not in texto.upper()


def test_el_socio_por_defecto_se_siembra_con_la_huella_de_su_clave_y_los_cuatro_alcances():
    texto = SOCIO_POR_DEFECTO.read_text(encoding="utf-8")

    assert "INSERT INTO ms_identidad.socio " in texto
    assert "INSERT INTO ms_identidad.credencial_socio " in texto
    assert "1ebbe2fc-d8b1-4046-af76-b92bacec52ff" in texto
    assert _huella("solventa123") in texto
    assert "solventa123" not in texto.replace(_huella("solventa123"), "")
    for alcance in (
        "catalogo:leer",
        "originaciones:escribir",
        "cotizaciones:escribir",
        "cotizaciones:leer",
    ):
        assert alcance in texto
    assert texto.upper().count("ON CONFLICT DO NOTHING") == 2
    for prohibido in ("UPDATE", "DELETE", "DROP", "ALTER"):
        assert prohibido not in texto.upper()
