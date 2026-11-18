import json

import httpx

from tests.conftest import token

FILA = {
    "id": "PRE-BOG-06",
    "nombre": "Taller Moto Chapinero",
    "tipo": "taller-motos",
    "ramos": ["soat-motocicleta"],
    "direccion": "Cra 13 #45-18",
    "ciudad": "Bogotá",
    "barrio": "Chapinero",
    "lat": 4.6355,
    "lng": -74.0655,
    "telefono": "601 555 0112",
    "horario": "Lun–Sáb 7:00–19:00",
    "estado": "activo",
    "distancia_km": 0.9,
    "actualizado_en": "2026-11-17T09:00:00-05:00",
}


def _ok(cuerpo):
    return lambda _: httpx.Response(200, json=cuerpo)


def test_cliente_recorta_radio_y_renombra(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/prestadores")] = _ok(
        {"centro": {"lat": 4.64, "lng": -74.06, "origen": "posicion"}, "radio_km": 50, "prestadores": [FILA], "conteos": None}
    )
    acceso = token(client, "cliente")
    respuesta = client.get(
        "/v1/cliente/prestadores",
        params={"lat": 4.64, "lng": -74.06, "radioKm": 80, "ramo": "soat-motocicleta"},
        headers={"Authorization": f"Bearer {acceso}"},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["prestadores"][0]["barrio"] == "Chapinero"
    assert "zona" not in cuerpo["prestadores"][0]
    assert "estado" not in cuerpo["prestadores"][0]
    assert cuerpo["prestadores"][0]["distanciaKm"] == 0.9
    enviada = nucleo_siniestros.peticiones[-1]
    assert enviada.url.params["radio_km"] == "50.0"


def test_asesor_lee_y_no_escribe(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/prestadores")] = _ok(
        {
            "centro": {"lat": 4.6, "lng": -74.08, "origen": "ciudad"},
            "radio_km": None,
            "prestadores": [FILA],
            "conteos": {"Bogotá": 30, "Medellín": 20, "Chía": 10},
        }
    )
    nucleo_siniestros.respuestas[("POST", "/v1/prestadores")] = lambda _: httpx.Response(
        403, json={"codigo": "rol_no_autorizado", "mensaje": "Rol no autorizado"}
    )
    acceso = token(client, "asesor")
    lista = client.get("/v1/operador/prestadores", headers={"Authorization": f"Bearer {acceso}"})
    assert lista.status_code == 200
    assert lista.json()["conteos"]["Chía"] == 10
    alta = client.post("/v1/operador/prestadores", json={"nombre": "x"}, headers={"Authorization": f"Bearer {acceso}"})
    assert alta.status_code == 403


def test_siniestro_de_otro_cliente_es_404(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/siniestros/abc/prestadores")] = lambda _: httpx.Response(
        404, json={"codigo": "no_encontrado", "mensaje": "No existe"}
    )
    acceso = token(client, "cliente")
    respuesta = client.get("/v1/cliente/siniestros/abc/prestadores", headers={"Authorization": f"Bearer {acceso}"})
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_operador_crea(client, nucleo_siniestros):
    def creado(request: httpx.Request):
        cuerpo = json.loads(request.content)
        assert cuerpo["ramos"] == ["soat-motocicleta"]
        return httpx.Response(201, json={**FILA, "distancia_km": None})

    nucleo_siniestros.respuestas[("POST", "/v1/prestadores")] = creado
    acceso = token(client, "operador")
    respuesta = client.post(
        "/v1/operador/prestadores",
        json={"nombre": "Taller", "ramos": ["soat-motocicleta"]},
        headers={"Authorization": f"Bearer {acceso}"},
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["id"] == "PRE-BOG-06"
    assert respuesta.json()["estado"] == "activo"
