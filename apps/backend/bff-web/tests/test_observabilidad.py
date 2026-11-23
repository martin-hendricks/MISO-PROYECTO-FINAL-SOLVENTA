def test_metrics_expone_formato_prometheus(client):
    respuesta = client.get("/metrics")

    assert respuesta.status_code == 200
    assert b"http_request_duration_seconds" in respuesta.content
