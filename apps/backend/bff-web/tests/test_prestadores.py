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


CIUDADES_MX = {
    "pais": "MX",
    "ciudades": [{"nombre": "Ciudad de México", "lat": 19.4326, "lng": -99.1332, "zoom": 11, "orden": 1, "prestadores": 5}],
}


def test_ciudades_cliente_y_operador(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/prestadores/ciudades")] = _ok(CIUDADES_MX)
    cliente = client.get(
        "/v1/cliente/prestadores/ciudades",
        params={"pais": "MX"},
        headers={"Authorization": f"Bearer {token(client, 'cliente')}"},
    )
    assert cliente.status_code == 200
    assert cliente.json() == {
        "pais": "MX",
        "ciudades": [{"nombre": "Ciudad de México", "lat": 19.4326, "lng": -99.1332, "zoom": 11, "prestadores": 5}],
    }
    assert nucleo_siniestros.peticiones[-1].url.params["con_prestadores"] == "true"
    asesor = client.get(
        "/v1/operador/prestadores/ciudades",
        params={"pais": "MX"},
        headers={"Authorization": f"Bearer {token(client, 'asesor')}"},
    )
    assert asesor.status_code == 200
    assert nucleo_siniestros.peticiones[-1].url.params["con_prestadores"] == "false"


def test_area_reenvia_bordes_sin_radio(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/prestadores")] = _ok(
        {"centro": None, "radio_km": None, "truncado": True, "prestadores": [{**FILA, "pais": "CO"}], "conteos": None}
    )
    respuesta = client.get(
        "/v1/cliente/prestadores",
        params={"norte": 4.66, "sur": 4.62, "este": -74.05, "oeste": -74.08, "lat": 4.64, "lng": -74.06},
        headers={"Authorization": f"Bearer {token(client, 'cliente')}"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["truncado"] is True
    assert respuesta.json()["prestadores"][0]["pais"] == "CO"
    enviada = nucleo_siniestros.peticiones[-1].url.params
    assert (enviada["norte"], enviada["oeste"], enviada["limite"]) == ("4.66", "-74.08", "500")
    assert "radio_km" not in enviada


def test_area_invalida_pasa_tal_cual(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/prestadores")] = lambda _: httpx.Response(
        422, json={"codigo": "area_invalida", "mensaje": "El área visible no es válida"}
    )
    respuesta = client.get(
        "/v1/cliente/prestadores",
        params={"norte": 4.6, "sur": 4.7, "este": -74.0, "oeste": -74.1},
        headers={"Authorization": f"Bearer {token(client, 'cliente')}"},
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "area_invalida"


def test_operador_lee_edita_y_cambia_estado(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/prestadores/PRE-BOG-06")] = _ok(FILA)
    nucleo_siniestros.respuestas[("PATCH", "/v1/prestadores/PRE-BOG-06")] = _ok({**FILA, "nombre": "Nuevo"})
    nucleo_siniestros.respuestas[("POST", "/v1/prestadores/PRE-BOG-06/estado")] = _ok({**FILA, "estado": "inactivo"})
    acceso = {"Authorization": f"Bearer {token(client, 'operador')}"}
    ficha = client.get("/v1/operador/prestadores/PRE-BOG-06", headers=acceso)
    assert ficha.status_code == 200
    assert ficha.json()["estado"] == "activo"
    editado = client.patch("/v1/operador/prestadores/PRE-BOG-06", json={"nombre": "Nuevo"}, headers=acceso)
    assert editado.json()["nombre"] == "Nuevo"
    estado = client.post(
        "/v1/operador/prestadores/PRE-BOG-06/estado",
        json={"estado": "inactivo"},
        headers=acceso,
    )
    assert estado.json()["estado"] == "inactivo"


def test_siniestro_del_cliente_adapta_el_aviso(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/siniestros/abc/prestadores")] = _ok(
        {
            "siniestro": {"id": "abc", "numero": "SIN-1"},
            "ramo_fijo": "soat-motocicleta",
            "sin_geoetiqueta": False,
            "centro": {"lat": 4.6, "lng": -74.0, "origen": "siniestro"},
            "radio_km": 10,
            "truncado": False,
            "prestadores": [FILA],
        }
    )
    respuesta = client.get(
        "/v1/cliente/siniestros/abc/prestadores",
        headers={"Authorization": f"Bearer {token(client, 'cliente')}"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["siniestro"] == {"id": "abc", "numero": "SIN-1", "ramo": "soat-motocicleta"}
    assert respuesta.json()["prestadores"][0]["id"] == "PRE-BOG-06"


def test_operador_filtra_por_pais(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/prestadores")] = _ok(
        {"centro": None, "radio_km": None, "truncado": False, "prestadores": [], "conteos": {"Santiago": 0}}
    )
    respuesta = client.get(
        "/v1/operador/prestadores",
        params={"pais": "CL"},
        headers={"Authorization": f"Bearer {token(client, 'asesor')}"},
    )
    assert respuesta.json()["pais"] == "CL"
    assert respuesta.json()["conteos"] == {"Santiago": 0}
    assert nucleo_siniestros.peticiones[-1].url.params["pais"] == "CL"
