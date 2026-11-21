import httpx

from tests.conftest import token

POLIZA_ID = "c1c1c1c1-0000-4000-8000-00000000c1c1"


def _auth(client):
    return {"Authorization": f"Bearer {token(client, 'cliente')}"}


def _preparar(nucleo_polizas, renovacion=True):
    nucleo_polizas.respuestas[("GET", "/v1/polizas/numero/POL-9")] = lambda _: httpx.Response(
        200, json={"id": POLIZA_ID, "numero": "POL-9", "usuario_id": None}
    )
    nucleo_polizas.respuestas[("PATCH", f"/v1/polizas/{POLIZA_ID}/preferencias")] = lambda _: httpx.Response(
        200, json={"numero": "POL-9", "renovacion_automatica": renovacion}
    )


def test_guardar_la_renovacion_automatica_responde_y_la_envia_a_ms_polizas(client, nucleo_polizas):
    """Regresion: la ruta hacía UUID(contexto.usuario_id) sobre un valor que ya era un UUID y respondia
    500 (AttributeError) antes de llamar a ms-polizas."""
    _preparar(nucleo_polizas, renovacion=True)

    respuesta = client.patch(
        "/v1/cliente/polizas/POL-9/preferencias", headers=_auth(client), json={"renovacionAutomatica": True}
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {"numero": "POL-9", "renovacionAutomatica": True}
    busqueda, guardado = nucleo_polizas.peticiones
    assert busqueda.url.params["usuario_id"] == guardado.url.params["usuario_id"]
    assert guardado.url.path == f"/v1/polizas/{POLIZA_ID}/preferencias"
    assert guardado.read() == b'{"renovacion_automatica":true}'


def test_desactivar_la_renovacion_automatica(client, nucleo_polizas):
    _preparar(nucleo_polizas, renovacion=False)

    respuesta = client.patch(
        "/v1/cliente/polizas/POL-9/preferencias", headers=_auth(client), json={"renovacionAutomatica": False}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["renovacionAutomatica"] is False


def test_preferencias_requiere_rol_cliente(client):
    asesor = {"Authorization": f"Bearer {token(client, 'asesor')}"}

    respuesta = client.patch(
        "/v1/cliente/polizas/POL-9/preferencias", headers=asesor, json={"renovacionAutomatica": True}
    )

    assert respuesta.status_code == 403
