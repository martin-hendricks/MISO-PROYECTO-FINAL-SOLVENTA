import pytest

from .conftest import token

CLIENTE = "11111111-1111-1111-1111-111111111111"
SOCIO = {"Authorization": f"Bearer {token('socio')}"}
ORIGINACION = {"cliente_id": CLIENTE, "valor": "180000000", "plazo_meses": 240, "origen": "socio"}


def test_socio_registra_una_originacion(client):
    respuesta = client.post("/v1/originaciones", json=ORIGINACION, headers=SOCIO)

    assert respuesta.status_code == 201


def test_socio_consulta_el_consentimiento_de_un_cliente(client):
    client.post("/v1/consentimientos", json={"cliente_id": CLIENTE})

    respuesta = client.get(f"/v1/consentimientos/{CLIENTE}", headers=SOCIO)

    assert respuesta.status_code == 200
    assert respuesta.json()["vigente"] is True


def test_socio_consulta_cliente_sin_consentimiento_es_404(client):
    respuesta = client.get(f"/v1/consentimientos/{CLIENTE}", headers=SOCIO)

    assert respuesta.status_code == 404


@pytest.mark.parametrize(
    "metodo, ruta, cuerpo",
    [
        ("post", "/v1/consentimientos", {"cliente_id": CLIENTE}),
        ("delete", f"/v1/consentimientos/{CLIENTE}", None),
        ("get", f"/v1/ofertas-hipotecario/clientes/{CLIENTE}/ultima", None),
        ("get", f"/v1/originaciones/clientes/{CLIENTE}/pendiente", None),
        ("delete", f"/v1/originaciones/clientes/{CLIENTE}/pendiente", None),
    ],
)
def test_socio_no_accede_al_resto_de_perfilamiento(client, metodo, ruta, cuerpo):
    argumentos = {"headers": SOCIO}
    if cuerpo is not None:
        argumentos["json"] = cuerpo

    respuesta = getattr(client, metodo)(ruta, **argumentos)

    assert respuesta.status_code == 401
