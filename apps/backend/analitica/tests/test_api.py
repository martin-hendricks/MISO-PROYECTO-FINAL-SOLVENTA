from datetime import date


def _sembrar(almacen, tipo, fecha, cantidad):
    almacen.conteos[(tipo, fecha)] = cantidad


def test_metricas_requiere_token(client):
    respuesta = client.request(
        "GET",
        "/v1/metricas",
        params={"desde": "2026-01-01", "hasta": "2026-01-31"},
        sin_token=True,
    )
    assert respuesta.status_code == 401


def test_metricas_rechaza_rol_cliente(client_cliente):
    respuesta = client_cliente.get(
        "/v1/metricas", params={"desde": "2026-01-01", "hasta": "2026-01-31"}
    )
    assert respuesta.status_code == 403


def test_metricas_devuelve_conteos_en_rango(client, almacen):
    _sembrar(almacen, "PolizaEmitida", date(2026, 1, 10), 5)
    _sembrar(almacen, "PolizaCancelada", date(2026, 1, 15), 2)
    _sembrar(almacen, "PolizaEmitida", date(2026, 2, 1), 9)  # fuera de rango

    respuesta = client.get(
        "/v1/metricas", params={"desde": "2026-01-01", "hasta": "2026-01-31"}
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo["conteos"]) == 2
    tipos = {c["tipo"]: c["cantidad"] for c in cuerpo["conteos"]}
    assert tipos == {"PolizaEmitida": 5, "PolizaCancelada": 2}


def test_metricas_sin_datos_devuelve_lista_vacia(client):
    respuesta = client.get(
        "/v1/metricas", params={"desde": "2026-01-01", "hasta": "2026-01-31"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"conteos": []}


def test_metricas_hasta_antes_de_desde_es_422(client):
    respuesta = client.get(
        "/v1/metricas", params={"desde": "2026-01-31", "hasta": "2026-01-01"}
    )
    assert respuesta.status_code == 422
