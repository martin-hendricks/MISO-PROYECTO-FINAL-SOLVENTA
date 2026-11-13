from uuid import UUID, uuid4

import pytest

from app.dependencies import obtener_verificador_kyc
from app.domain.modelos import EstadoUsuario, Usuario
from app.infrastructure.kyc import VerificadorKYCStub
from tests.conftest import token_de

BODY_ALTA = {
    "tipo_documento": "CC",
    "numero_documento": "1012345678",
    "email": "camila@correo.com",
    "password": "clave-secreta-123",
}


def _crear(client, **overrides):
    return client.post("/v1/usuarios", json={**BODY_ALTA, **overrides})


def test_alta_devuelve_201_con_el_usuario_sin_password(client):
    respuesta = _crear(client)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["email"] == "camila@correo.com"
    assert cuerpo["tipo_documento"] == "CC"
    assert cuerpo["estado"] == "ACTIVO"
    assert "password" not in cuerpo
    assert "password_hash" not in cuerpo


def test_alta_con_email_duplicado_es_409(client):
    _crear(client)

    respuesta = _crear(client, numero_documento="otro-documento")

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "cuenta_duplicada"


def test_alta_con_documento_duplicado_es_409(client):
    _crear(client)

    respuesta = _crear(client, email="otro@correo.com")

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "cuenta_duplicada"


def test_alta_con_documento_rechazado_por_kyc_es_422(client):
    client.app.dependency_overrides[obtener_verificador_kyc] = lambda: VerificadorKYCStub(
        documentos_rechazados=["0000000000"]
    )

    respuesta = _crear(client, numero_documento="0000000000")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "identidad_no_verificada"


def test_alta_con_kyc_caido_es_503(client):
    client.app.dependency_overrides[obtener_verificador_kyc] = lambda: VerificadorKYCStub(fallar=True)

    respuesta = _crear(client)

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "dependencia_no_disponible"


def test_alta_con_password_corto_es_422(client):
    respuesta = _crear(client, password="1234567")

    assert respuesta.status_code == 422


def test_alta_sin_email_es_422(client):
    respuesta = client.post(
        "/v1/usuarios",
        json={k: v for k, v in BODY_ALTA.items() if k != "email"},
    )

    assert respuesta.status_code == 422


def test_autenticacion_con_credenciales_correctas_es_200(client):
    _crear(client)

    respuesta = client.post(
        "/v1/usuarios/autenticacion",
        json={"email": "camila@correo.com", "password": "clave-secreta-123"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == "camila@correo.com"


def test_autenticacion_con_password_incorrecto_es_401(client):
    _crear(client)

    respuesta = client.post(
        "/v1/usuarios/autenticacion",
        json={"email": "camila@correo.com", "password": "clave-incorrecta"},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "credenciales_invalidas"


def test_autenticacion_con_email_inexistente_es_401_con_el_mismo_codigo(client):
    respuesta = client.post(
        "/v1/usuarios/autenticacion",
        json={"email": "nadie@correo.com", "password": "clave-secreta-123"},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "credenciales_invalidas"


def test_autenticacion_es_insensible_a_mayusculas_en_el_email(client):
    _crear(client)

    respuesta = client.post(
        "/v1/usuarios/autenticacion",
        json={"email": "CAMILA@CORREO.com", "password": "clave-secreta-123"},
    )

    assert respuesta.status_code == 200


def _poner(almacen, i, **extra):
    usuario = Usuario(
        id=uuid4(),
        tipo_documento="CC",
        numero_documento=extra.get("numero_documento", f"doc-{i}-{uuid4().hex[:6]}"),
        email=extra.get("email", f"u{i}-{uuid4().hex[:6]}@correo.com"),
        password_hash="x",
        estado=extra.get("estado", EstadoUsuario.ACTIVO),
        nombre=extra.get("nombre", f"Nom{i:02d}"),
        apellidos=extra.get("apellidos", f"Ape{i:02d}"),
        rol=extra.get("rol", "cliente"),
    )
    almacen.usuarios[usuario.id] = usuario
    return usuario


def _auth(rol: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_de(str(uuid4()), rol)}"}


def test_listar_clientes_solo_backoffice_y_solo_rol_cliente(client, almacen):
    cliente = _poner(almacen, 1, nombre="Laura", apellidos="Pena", email="laura@correo.com", numero_documento="52448901")
    inactivo = _poner(almacen, 2, estado=EstadoUsuario.INACTIVO, apellidos="Pena", nombre="Zoe")
    _poner(almacen, 3, rol="operador", nombre="Laura", apellidos="Pena", email="ops@correo.com")

    assert client.get("/v1/usuarios", params={"rol": "cliente"}, headers=_auth("cliente")).status_code == 403
    assert client.get("/v1/usuarios", params={"rol": "asesor"}).status_code == 422
    assert client.get("/v1/usuarios", params={"rol": "cliente", "q": "a"}).json()["codigo"] == "consulta_corta"
    assert client.get("/v1/usuarios", params={"rol": "cliente", "ids": [str(uuid4()) for _ in range(51)]}).status_code == 422

    asesor = client.get("/v1/usuarios", params={"rol": "cliente"}, headers=_auth("asesor"))
    assert asesor.status_code == 200
    ids = {item["usuario_id"] for item in asesor.json()["usuarios"]}
    assert str(cliente.id) in ids and str(inactivo.id) in ids
    assert all(item["rol"] == "cliente" for item in asesor.json()["usuarios"])

    solo_activos = client.get("/v1/usuarios", params={"rol": "cliente", "estado": "ACTIVO"})
    assert {item["usuario_id"] for item in solo_activos.json()["usuarios"]} == {str(cliente.id)}

    por_nombre = client.get("/v1/usuarios", params={"rol": "cliente", "q": "LAURA"})
    assert [item["usuario_id"] for item in por_nombre.json()["usuarios"]] == [str(cliente.id)]
    por_documento = client.get("/v1/usuarios", params={"rol": "cliente", "q": "2448"})
    assert [item["usuario_id"] for item in por_documento.json()["usuarios"]] == [str(cliente.id)]
    por_correo = client.get("/v1/usuarios", params={"rol": "cliente", "q": "LAURA@"})
    assert [item["usuario_id"] for item in por_correo.json()["usuarios"]] == [str(cliente.id)]
    por_apellido = client.get("/v1/usuarios", params={"rol": "cliente", "q": "pena"})
    assert [item["usuario_id"] for item in por_apellido.json()["usuarios"]] == [str(cliente.id), str(inactivo.id)]

    solo_esos = client.get("/v1/usuarios", params={"rol": "cliente", "ids": [str(cliente.id)]})
    assert solo_esos.json()["hay_mas"] is False
    assert [item["usuario_id"] for item in solo_esos.json()["usuarios"]] == [str(cliente.id)]


def test_listar_clientes_pagina_de_20_con_hay_mas(client, almacen):
    for indice in range(21):
        _poner(almacen, indice)

    primera = client.get("/v1/usuarios", params={"rol": "cliente", "pagina": 1}).json()
    segunda = client.get("/v1/usuarios", params={"rol": "cliente", "pagina": 2}).json()

    assert primera["pagina"] == 1 and primera["hay_mas"] is True and len(primera["usuarios"]) == 20
    assert [item["apellidos"] for item in primera["usuarios"]] == [f"Ape{indice:02d}" for indice in range(20)]
    assert segunda["hay_mas"] is False and len(segunda["usuarios"]) == 1
    assert segunda["usuarios"][0]["apellidos"] == "Ape20"

    pedidas = [_poner(almacen, 100 + indice) for indice in range(25)]
    por_ids = client.get(
        "/v1/usuarios", params={"rol": "cliente", "ids": [str(usuario.id) for usuario in pedidas]}
    ).json()
    assert por_ids["hay_mas"] is False and len(por_ids["usuarios"]) == 25


def test_editar_y_cambiar_estado_solo_operador(client, almacen):
    creado = _crear(client, nombre="Camila", apellidos="Restrepo").json()
    otro = _crear(client, email="otro@correo.com", numero_documento="99887766").json()
    usuario_id = creado["usuario_id"]
    cuerpo = {"nombre": "Ana", "apellidos": "Lopez", "email": "ANA@correo.com"}

    for rol in ("cliente", "asesor"):
        assert client.patch(f"/v1/usuarios/{usuario_id}", json=cuerpo, headers=_auth(rol)).status_code == 403
        assert (
            client.post(f"/v1/usuarios/{usuario_id}/estado", json={"estado": "INACTIVO"}, headers=_auth(rol)).status_code
            == 403
        )

    editado = client.patch(f"/v1/usuarios/{usuario_id}", json=cuerpo)
    assert editado.status_code == 200
    assert editado.json()["email"] == "ana@correo.com"
    assert editado.json()["nombre"] == "Ana"

    duplicado = client.patch(
        f"/v1/usuarios/{usuario_id}",
        json={"nombre": "Ana", "apellidos": "Lopez", "email": "OTRO@correo.com"},
    )
    assert duplicado.status_code == 409
    assert duplicado.json()["codigo"] == "conflicto"

    assert client.patch(f"/v1/usuarios/{uuid4()}", json=cuerpo).status_code == 404
    assert client.patch(f"/v1/usuarios/{usuario_id}", json={**cuerpo, "nombre": ""}).status_code == 422
    assert client.patch(f"/v1/usuarios/{usuario_id}", json={**cuerpo, "nombre": "n" * 81}).status_code == 422
    assert client.patch(f"/v1/usuarios/{usuario_id}", json={**cuerpo, "email": "no-es-correo"}).status_code == 422

    almacen.usuarios[UUID(otro["usuario_id"])].rol = "asesor"
    assert client.patch(f"/v1/usuarios/{otro['usuario_id']}", json=cuerpo).status_code == 404
    assert client.post(f"/v1/usuarios/{otro['usuario_id']}/estado", json={"estado": "INACTIVO"}).status_code == 404

    igual = client.post(f"/v1/usuarios/{usuario_id}/estado", json={"estado": "ACTIVO"})
    assert igual.status_code == 200 and igual.json()["estado"] == "ACTIVO"
    assert almacen.outbox == []

    inactivo = client.post(f"/v1/usuarios/{usuario_id}/estado", json={"estado": "INACTIVO"})
    assert inactivo.status_code == 200 and inactivo.json()["estado"] == "INACTIVO"
    assert almacen.outbox[0].tipo == "UsuarioInactivado"
    assert client.post(f"/v1/usuarios/{usuario_id}/estado", json={"estado": "BLOQUEADO"}).status_code == 422
    assert client.post(f"/v1/usuarios/{uuid4()}/estado", json={"estado": "INACTIVO"}).status_code == 404


def test_consultar_y_actualizar_perfil(client):
    creado = _crear(client, nombre="Camila", apellidos="Restrepo").json()
    usuario_id = creado["usuario_id"]
    propio = {"Authorization": f"Bearer {token_de(usuario_id, 'cliente')}"}

    consulta = client.get(f"/v1/usuarios/{usuario_id}", headers=propio)
    assert consulta.status_code == 200
    assert consulta.json()["nombre"] == "Camila"

    perfil = client.patch(
        f"/v1/usuarios/{usuario_id}/perfil",
        json={"nombre": "Ana", "apellidos": "Lopez"},
        headers=propio,
    )
    assert perfil.status_code == 200
    assert perfil.json()["apellidos"] == "Lopez"
    assert perfil.json()["rol"] == "cliente"
    assert client.get(f"/v1/usuarios/{usuario_id}", headers=propio).json()["nombre"] == "Ana"

    ajeno = {"Authorization": f"Bearer {token_de(str(uuid4()), 'cliente')}"}
    assert client.get(f"/v1/usuarios/{usuario_id}", headers=ajeno).status_code == 404
    assert client.get(f"/v1/usuarios/{uuid4()}").status_code == 404
    assert (
        client.patch(
            f"/v1/usuarios/{uuid4()}/perfil", json={"nombre": "Ana", "apellidos": "Lopez"}
        ).status_code
        == 404
    )


def test_prueba_de_vida_queda_en_no_y_solo_el_dueno_la_cambia(client):
    creado = _crear(client).json()
    assert creado["prueba_de_vida"] == "no"
    explicita = _crear(
        client, email="otra@correo.com", numero_documento="900", prueba_de_vida="ok"
    ).json()
    assert explicita["prueba_de_vida"] == "ok"

    usuario_id = creado["usuario_id"]
    propio = {"Authorization": f"Bearer {token_de(usuario_id, 'cliente')}"}
    cambio = client.patch(
        f"/v1/usuarios/{usuario_id}/prueba-de-vida",
        json={"prueba_de_vida": "ok"},
        headers=propio,
    )
    assert cambio.status_code == 200
    assert cambio.json()["prueba_de_vida"] == "ok"

    ajeno = {"Authorization": f"Bearer {token_de(str(uuid4()), 'cliente')}"}
    assert (
        client.patch(
            f"/v1/usuarios/{usuario_id}/prueba-de-vida",
            json={"prueba_de_vida": "no"},
            headers=ajeno,
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/v1/usuarios/{usuario_id}/prueba-de-vida",
            json={"prueba_de_vida": "maybe"},
            headers=propio,
        ).status_code
        == 422
    )


def test_health_ready_sin_base_de_datos_devuelve_503(client):
    # El cliente de pruebas crea la app real (lifespan real -> motor SQLAlchemy real)
    # pero sin un Postgres escuchando en DATABASE_URL: el ping debe fallar controladamente.
    respuesta = client.get("/health/ready")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable"}


def test_health_live_no_toca_la_base_de_datos(client):
    assert client.get("/health/live").json() == {"status": "ok"}


def _buscar(client, rol: str, tipo: str = "CC", numero: str = "1012345678"):
    from tests.conftest import token_de

    return client.get(
        "/v1/usuarios/documento",
        params={"tipo_documento": tipo, "numero_documento": numero},
        headers={"Authorization": f"Bearer {token_de(str(uuid4()), rol)}"},
    )


@pytest.mark.parametrize("rol", ["socio", "asesor", "operador"])
def test_buscar_por_documento_devuelve_solo_el_usuario_id(client, rol):
    creado = _crear(client).json()

    respuesta = _buscar(client, rol)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"usuario_id": creado["usuario_id"]}


def test_buscar_por_documento_normaliza_como_el_alta(client):
    creado = _crear(client).json()

    respuesta = _buscar(client, "socio", tipo=" cc ", numero=" 1012345678 ")

    assert respuesta.json() == {"usuario_id": creado["usuario_id"]}


def test_buscar_por_documento_inexistente_es_404(client):
    assert _buscar(client, "socio", numero="999").status_code == 404


def test_un_cliente_no_puede_buscar_por_documento(client):
    _crear(client)

    assert _buscar(client, "cliente").status_code == 403


def test_buscar_por_documento_exige_token_y_ambos_datos(client):
    from fastapi.testclient import TestClient

    anonimo = TestClient(client.app)
    assert (
        anonimo.get("/v1/usuarios/documento", params={"tipo_documento": "CC", "numero_documento": "1"}).status_code
        == 401
    )
    assert client.get("/v1/usuarios/documento", params={"tipo_documento": "CC"}).status_code == 422


def test_un_socio_no_puede_leer_la_cuenta_completa(client):
    from tests.conftest import token_de

    creado = _crear(client).json()
    socio = {"Authorization": f"Bearer {token_de(str(uuid4()), 'socio')}"}

    assert client.get(f"/v1/usuarios/{creado['usuario_id']}", headers=socio).status_code == 403
    assert (
        client.patch(f"/v1/usuarios/{creado['usuario_id']}/perfil", json={"nombre": "X", "apellidos": "Y"}, headers=socio).status_code
        == 404
    )
