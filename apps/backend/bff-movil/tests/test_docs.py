def test_openapi_bff_movil_expone_servers_con_prefijo(client):
    respuesta = client.get("/bff-movil/v1/openapi.json")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["servers"] == [{"url": "/bff-movil/v1"}]


def test_docs_bff_movil_devuelve_swagger_ui(client):
    respuesta = client.get("/bff-movil/v1/docs")

    assert respuesta.status_code == 200
    assert b"swagger-ui" in respuesta.content
    assert b"/bff-movil/v1/openapi.json" in respuesta.content
