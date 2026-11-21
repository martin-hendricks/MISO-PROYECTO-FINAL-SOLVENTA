from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest

SOCIO = UUID("6f1c2a4e-0000-4000-8000-000000000001")
OTRO_SOCIO = UUID("6f1c2a4e-0000-4000-8000-000000000002")


def _autorizacion(rol: str, uid: UUID) -> dict[str, str]:
    token = jwt.encode(
        {"sub": "api-socios", "uid": str(uid), "rol": rol, "typ": "access", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "test-secret",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _payload(socio_id: UUID) -> dict:
    return {
        "usuario_id": str(uuid4()),
        "socio_id": str(socio_id),
        "consentimiento_id": str(uuid4()),
        "producto": "soat-motocicleta",
        "canal": "app-socio",
        "datos_riesgo": {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"},
    }


def _cotizar(client, socio: UUID, clave: str = "clave-socio-0001"):
    return client.post(
        "/v1/cotizaciones",
        json=_payload(socio),
        headers={"Idempotency-Key": clave, **_autorizacion("socio", socio)},
    )


def test_socio_cotiza_a_su_propio_nombre(client):
    respuesta = _cotizar(client, SOCIO)

    assert respuesta.status_code == 201


def test_socio_no_puede_cotizar_a_nombre_de_otro_socio(client):
    respuesta = client.post(
        "/v1/cotizaciones",
        json=_payload(OTRO_SOCIO),
        headers={"Idempotency-Key": "clave-socio-0002", **_autorizacion("socio", SOCIO)},
    )

    assert respuesta.status_code == 403


def test_socio_reconsulta_su_cotizacion(client):
    cotizacion_id = _cotizar(client, SOCIO).json()["cotizacion_id"]

    respuesta = client.get(f"/v1/cotizaciones/{cotizacion_id}", headers=_autorizacion("socio", SOCIO))

    assert respuesta.status_code == 200
    assert respuesta.json()["cotizacion_id"] == cotizacion_id


def test_socio_no_ve_la_cotizacion_de_otro_socio(client):
    cotizacion_id = _cotizar(client, SOCIO).json()["cotizacion_id"]

    respuesta = client.get(f"/v1/cotizaciones/{cotizacion_id}", headers=_autorizacion("socio", OTRO_SOCIO))

    assert respuesta.status_code == 404


def test_operador_sigue_viendo_la_cotizacion_de_un_socio(client):
    cotizacion_id = _cotizar(client, SOCIO).json()["cotizacion_id"]

    respuesta = client.get(f"/v1/cotizaciones/{cotizacion_id}")

    assert respuesta.status_code == 200


@pytest.mark.parametrize(
    "metodo, ruta",
    [
        ("get", f"/v1/cotizaciones?asesor_id={uuid4()}"),
        ("get", f"/v1/cotizaciones/por-usuario/{uuid4()}"),
        ("get", f"/v1/cotizaciones/por-oferta/{uuid4()}"),
    ],
)
def test_socio_no_accede_a_listados_ni_busqueda_por_oferta(client, metodo, ruta):
    respuesta = getattr(client, metodo)(ruta, headers=_autorizacion("socio", SOCIO))

    assert respuesta.status_code == 403


def test_socio_no_acepta_ofertas(client):
    cotizacion_id = _cotizar(client, SOCIO).json()["cotizacion_id"]

    respuesta = client.post(
        f"/v1/cotizaciones/{cotizacion_id}/aceptacion",
        json={"perfil_id": str(uuid4()), "score": "720"},
        headers={"Idempotency-Key": "aceptar-socio-0001", **_autorizacion("socio", SOCIO)},
    )

    assert respuesta.status_code == 403


def test_socio_reintenta_su_propia_clave_y_recibe_su_cotizacion(client):
    primera = _cotizar(client, SOCIO, clave="clave-compartida-01")

    segunda = _cotizar(client, SOCIO, clave="clave-compartida-01")

    assert segunda.status_code == 200
    assert segunda.json()["cotizacion_id"] == primera.json()["cotizacion_id"]


def test_socio_que_reusa_la_clave_de_otro_socio_no_recibe_su_cotizacion(client):
    primera = _cotizar(client, SOCIO, clave="clave-compartida-02")

    ajena = _cotizar(client, OTRO_SOCIO, clave="clave-compartida-02")

    assert ajena.status_code == 404
    assert primera.json()["cotizacion_id"] not in ajena.text
    assert primera.json()["usuario_id"] not in ajena.text
