from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from tests.conftest import token_de

BODY_ALTA = {
    "tipo_documento": "CC",
    "numero_documento": "1012345678",
    "email": "camila@correo.com",
    "password": "clave-secreta-123",
}


def _servicio(sub: str = "notificaciones", rol: str = "servicio") -> dict:
    token = jwt.encode(
        {
            "sub": sub,
            "uid": str(uuid4()),
            "rol": rol,
            "typ": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_notificaciones_obtiene_el_correo_y_nada_mas(client):
    creado = client.post("/v1/usuarios", json=BODY_ALTA).json()

    respuesta = client.get(f"/v1/usuarios/{creado['usuario_id']}/contacto", headers=_servicio())

    assert respuesta.status_code == 200
    assert respuesta.json() == {"email": "camila@correo.com"}


def test_otro_servicio_o_rol_no_obtiene_el_contacto(client):
    creado = client.post("/v1/usuarios", json=BODY_ALTA).json()
    ruta = f"/v1/usuarios/{creado['usuario_id']}/contacto"

    for cabeceras in (
        _servicio(sub="api-socios"),
        _servicio(sub="notificaciones", rol="socio"),
        {"Authorization": f"Bearer {token_de(creado['usuario_id'], 'cliente')}"},
        {"Authorization": f"Bearer {token_de(str(uuid4()), 'operador')}"},
    ):
        assert client.get(ruta, headers=cabeceras).status_code == 403


def test_el_rol_servicio_no_abre_la_ficha_completa(client):
    creado = client.post("/v1/usuarios", json=BODY_ALTA).json()

    respuesta = client.get(f"/v1/usuarios/{creado['usuario_id']}", headers=_servicio())

    assert respuesta.status_code == 403


def test_usuario_inexistente_o_inactivo_responde_404(client):
    assert client.get(f"/v1/usuarios/{uuid4()}/contacto", headers=_servicio()).status_code == 404

    creado = client.post("/v1/usuarios", json=BODY_ALTA).json()
    desactivado = client.patch(
        f"/v1/clientes/{creado['usuario_id']}/estado",
        json={"estado": "inactivo"},
        headers={"Authorization": f"Bearer {token_de(str(uuid4()), 'operador')}"},
    )
    assert desactivado.status_code == 200

    respuesta = client.get(f"/v1/usuarios/{creado['usuario_id']}/contacto", headers=_servicio())
    assert respuesta.status_code == 404


def test_sin_token_responde_401(client):
    respuesta = client.get(f"/v1/usuarios/{uuid4()}/contacto", headers={"Authorization": "Bearer x"})

    assert respuesta.status_code == 401
