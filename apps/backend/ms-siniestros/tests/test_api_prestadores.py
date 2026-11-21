from decimal import Decimal

from .conftest import cabecera

CUERPO = {
    "nombre": "Taller Moto Norte Usaquén",
    "tipo": "taller-motos",
    "ramos": ["soat-motocicleta"],
    "direccion": "Cll 134 #9-20",
    "ciudad": "Bogotá",
    "barrio": "Usaquén",
    "lat": "4.710400",
    "lng": "-74.034000",
    "telefono": "601 555 0111",
    "horario": "Lun–Sáb 7:00–19:00",
}


def test_sin_token(client):
    respuesta = client.get("/v1/prestadores", headers={"Authorization": ""})
    assert respuesta.status_code == 401


def test_alta_y_busqueda(client):
    alta = client.post("/v1/prestadores", json=CUERPO, headers=cabecera("operador"))
    assert alta.status_code == 201
    creado = alta.json()
    assert creado["id"].startswith("PRE-")
    assert creado["estado"] == "activo"
    cerca = client.get(
        "/v1/prestadores",
        params={"lat": "4.7104", "lng": "-74.034", "ramo": "soat-motocicleta"},
        headers=cabecera("cliente"),
    )
    assert cerca.status_code == 200
    cuerpo = cerca.json()
    assert cuerpo["prestadores"][0]["id"] == creado["id"]
    assert cuerpo["prestadores"][0]["distancia_km"] == 0.0
    assert cuerpo["conteos"] is None
    staff = client.get("/v1/prestadores", headers=cabecera("asesor"))
    assert staff.json()["conteos"]["Bogotá"] >= 1


def test_errores_de_entrada(client):
    sin_ramo = client.post("/v1/prestadores", json={**CUERPO, "ramos": []}, headers=cabecera("operador"))
    assert sin_ramo.status_code == 422
    desconocido = client.get("/v1/prestadores", params={"lat": 4.6, "lng": -74.0, "ramo": "autos"}, headers=cabecera("cliente"))
    assert desconocido.status_code == 422
    assert desconocido.json()["codigo"] == "ramo_desconocido"
    sin_centro = client.get("/v1/prestadores", headers=cabecera("cliente"))
    assert sin_centro.status_code == 422
    assert sin_centro.json()["codigo"] == "centro_requerido"
    radio = client.get("/v1/prestadores", params={"lat": 4.6, "lng": -74, "radio_km": 80}, headers=cabecera("cliente"))
    assert radio.status_code == 422
    fuera = client.post("/v1/prestadores", json={**CUERPO, "lat": "95"}, headers=cabecera("operador"))
    assert fuera.status_code == 422
    assert fuera.json()["codigo"] == "coordenada_fuera_de_rango"


def test_asesor_no_escribe_y_cliente_no_ve_inactivo(client):
    alta = client.post("/v1/prestadores", json=CUERPO, headers=cabecera("operador")).json()
    prohibido = client.post("/v1/prestadores", json=CUERPO, headers=cabecera("asesor"))
    assert prohibido.status_code == 403
    estado = client.post(f"/v1/prestadores/{alta['id']}/estado", json={"estado": "inactivo"}, headers=cabecera("operador"))
    assert estado.status_code == 200
    oculto = client.get(f"/v1/prestadores/{alta['id']}", headers=cabecera("cliente"))
    assert oculto.status_code == 404
    visible = client.get(f"/v1/prestadores/{alta['id']}", headers=cabecera("operador"))
    assert visible.json()["estado"] == "inactivo"
    otra = client.post(f"/v1/prestadores/{alta['id']}/estado", json={"estado": "inactivo"}, headers=cabecera("operador"))
    assert otra.status_code == 200
    client.post(f"/v1/prestadores/{alta['id']}/estado", json={"estado": "activo"}, headers=cabecera("operador"))
    parche = client.patch(
        f"/v1/prestadores/{alta['id']}", json={"ramos": ["viaje"]}, headers=cabecera("operador")
    )
    assert parche.status_code == 200
    assert parche.json()["ramos"] == ["viaje"]


def test_ciudades_no_chocan_con_el_id(client):
    client.post("/v1/prestadores", json=CUERPO, headers=cabecera("operador"))
    ciudades = client.get("/v1/prestadores/ciudades", params={"pais": "CO"}, headers=cabecera("cliente"))
    assert ciudades.status_code == 200
    assert ciudades.json()["pais"] == "CO"
    assert [c["nombre"] for c in ciudades.json()["ciudades"]] == ["Bogotá"]
    todas = client.get(
        "/v1/prestadores/ciudades", params={"pais": "CO", "con_prestadores": "false"}, headers=cabecera("asesor")
    )
    assert [c["nombre"] for c in todas.json()["ciudades"]] == ["Bogotá", "Medellín", "Chía"]
    assert todas.json()["ciudades"][0]["zoom"] == 12
    pais = client.get("/v1/prestadores/ciudades", params={"pais": "AR"}, headers=cabecera("cliente"))
    assert pais.status_code == 422
    assert pais.json()["codigo"] == "pais_desconocido"


def test_area_visible(client):
    alta = client.post("/v1/prestadores", json=CUERPO, headers=cabecera("operador")).json()
    bordes = {"norte": "4.75", "sur": "4.68", "este": "-74.00", "oeste": "-74.10"}
    area = client.get("/v1/prestadores", params={**bordes, "limite": 500}, headers=cabecera("cliente"))
    assert area.status_code == 200
    cuerpo = area.json()
    assert cuerpo["truncado"] is False
    assert cuerpo["prestadores"][0]["id"] == alta["id"]
    assert cuerpo["prestadores"][0]["pais"] == "CO"
    assert cuerpo["prestadores"][0]["distancia_km"] is None
    invertida = client.get("/v1/prestadores", params={**bordes, "sur": "4.80"}, headers=cabecera("cliente"))
    assert invertida.status_code == 422
    assert invertida.json()["codigo"] == "area_invalida"
    parcial = client.get("/v1/prestadores", params={"norte": "4.75"}, headers=cabecera("cliente"))
    assert parcial.json()["codigo"] == "area_invalida"
    sin_area = client.get("/v1/prestadores", params={"ciudad": "Bogotá", "limite": 101}, headers=cabecera("cliente"))
    assert sin_area.status_code == 422


def test_alta_con_ciudad_de_otro_pais(client):
    lima = client.post("/v1/prestadores", json={**CUERPO, "ciudad": "Lima"}, headers=cabecera("operador"))
    assert lima.status_code == 422
    assert lima.json()["codigo"] == "ciudad_desconocida"
    peru = client.post(
        "/v1/prestadores", json={**CUERPO, "ciudad": "Lima", "pais": "PE"}, headers=cabecera("operador")
    )
    assert peru.status_code == 201
    assert peru.json()["pais"] == "PE"
