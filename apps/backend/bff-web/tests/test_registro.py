def test_alta_web(client):
    body = {
        "nombre": "Camila",
        "apellidos": "Restrepo",
        "documento": "1012345678",
        "correo": "camila@correo.com",
        "habeasData": True,
    }
    response = client.post("/registro", json=body)
    assert response.status_code == 200
    assert response.json()["habeasData"] is True
    assert "pruebaDeVida" not in response.json()
