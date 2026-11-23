def test_prueba_de_vida_ok_y_no(client):
    base = {
        "nombre": "Camila",
        "apellidos": "Restrepo",
        "documento": "1012345678",
        "correo": "camila@correo.com",
        "habeasData": True,
        "ingresos_mensuales": "4500000.00",
        "gastos_mensuales": "1500000.00",
    }
    ok = client.post("/registro", json={**base, "pruebaDeVida": "ok"})
    no = client.post("/registro", json={**base, "pruebaDeVida": "no"})
    assert ok.status_code == 200 and ok.json()["pruebaDeVida"] == "ok"
    assert no.status_code == 200 and no.json()["pruebaDeVida"] == "no"
    assert "selfie" not in ok.json()


def test_otro_valor_de_prueba_es_400(client):
    response = client.post(
        "/registro",
        json={
            "nombre": "Camila",
            "apellidos": "Restrepo",
            "documento": "1",
            "correo": "c@c.com",
            "habeasData": True,
            "ingresos_mensuales": "4500000.00",
            "gastos_mensuales": "1500000.00",
            "pruebaDeVida": "maybe",
        },
    )
    assert response.status_code == 400


def test_registro_v1_reenvia_prueba_de_vida(client):
    from app.main import app

    llamadas = []

    class Nucleo:
        def crear_usuario(self, **kwargs):
            llamadas.append(kwargs)
            return {
                "usuario_id": "11111111-1111-1111-1111-111111111111",
                "email": kwargs["email"],
                "estado": "ACTIVO",
            }

    anterior = app.state.nucleo
    app.state.nucleo = Nucleo()
    try:
        response = client.post(
            "/v1/registro",
            json={
                "nombre": "Camila",
                "apellidos": "Restrepo",
                "documento": "1012345678",
                "correo": "camila@correo.com",
                "habeasData": True,
                "pruebaDeVida": "ok",
                "contrasena": "secreto12",
                "tipoDocumento": "CC",
                "ingresos_mensuales": "4500000.00",
                "gastos_mensuales": "1500000.00",
            },
        )
    finally:
        app.state.nucleo = anterior
    assert response.status_code == 200
    assert llamadas[0]["prueba_de_vida"] == "ok"


def test_revocar_consentimiento(client):
    response = client.post("/registro/consentimiento", json={"habeasData": False})
    assert response.status_code == 200
    assert response.json()["habeasData"] is False
