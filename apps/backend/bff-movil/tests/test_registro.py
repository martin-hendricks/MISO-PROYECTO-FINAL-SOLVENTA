def test_prueba_de_vida_ok_y_no(client):
    base = {
        "nombre": "Camila",
        "apellidos": "Restrepo",
        "documento": "1012345678",
        "correo": "camila@correo.com",
        "habeasData": True,
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
            "pruebaDeVida": "maybe",
        },
    )
    assert response.status_code == 400


def test_revocar_consentimiento(client):
    response = client.post("/registro/consentimiento", json={"habeasData": False})
    assert response.status_code == 200
    assert response.json()["habeasData"] is False
