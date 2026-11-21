from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import crear_app
from app.ports.publicador import PublicadorNoDisponible, PublicadorSaturado

from .conftest import CABECERAS, config_prueba, medicion_clima, reporte_vuelo


def _post(client, proveedor, carga, cabeceras=CABECERAS):
    return client.post(f"/v1/telemetria/{proveedor}/eventos", json=carga, headers=cabeceras)


def test_reporte_de_vuelo_se_acepta_con_202_y_se_publica_traducido(client, publicador):
    respuesta = _post(client, "vuelos", reporte_vuelo())

    assert respuesta.status_code == 202
    assert respuesta.json() == {"evento_id": "vuelos:R-1", "aceptado": True}
    [evento] = publicador.publicados
    assert evento.tipo == "retraso_vuelo"
    assert evento.valor == Decimal("190")
    assert evento.cobertura.umbral == Decimal("120")
    assert evento.cobertura.poliza_numero == "POL-77310"
    assert "AV234" in evento.descripcion


def test_medicion_de_clima_usa_su_propio_adaptador(client, publicador):
    respuesta = _post(client, "clima", medicion_clima())

    assert respuesta.status_code == 202
    [evento] = publicador.publicados
    assert evento.evento_id == "clima:M-9"
    assert evento.tipo == "precipitacion"
    assert evento.valor == Decimal("85.5")


def test_proveedor_no_registrado_es_404(client, publicador):
    assert _post(client, "sismos", {"x": 1}).status_code == 404
    assert publicador.publicados == []


def test_carga_que_no_cumple_el_esquema_del_proveedor_es_422_y_no_se_publica(client, publicador):
    respuesta = _post(client, "vuelos", reporte_vuelo(retraso_minutos=-5))

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "esquema_proveedor_invalido"
    assert "retraso_minutos" in respuesta.json()["mensaje"]
    assert publicador.publicados == []


def test_campos_desconocidos_del_proveedor_se_rechazan(client, publicador):
    # El esquema del proveedor no se filtra hacia adentro: lo que el adaptador no conoce, no entra.
    assert _post(client, "vuelos", reporte_vuelo(asiento="12A")).status_code == 422
    assert publicador.publicados == []


def test_monto_no_positivo_se_rechaza(client, publicador):
    carga = reporte_vuelo(cobertura={"umbral": "120", "monto": "0"})
    assert _post(client, "vuelos", carga).status_code == 422


def test_sin_credenciales_es_401(client, publicador):
    assert _post(client, "vuelos", reporte_vuelo(), cabeceras={}).status_code == 401
    assert publicador.publicados == []


def test_credenciales_incorrectas_es_401(client, publicador):
    cabeceras = {**CABECERAS, "X-Telemetria-Secreto": "otro"}
    assert _post(client, "vuelos", reporte_vuelo(), cabeceras=cabeceras).status_code == 401


def test_sin_credenciales_configuradas_no_acepta_nada(publicador):
    config = config_prueba(TELEMETRIA_CLIENT_SECRET="")
    with TestClient(crear_app(config, publicador=publicador)) as client:
        assert _post(client, "vuelos", reporte_vuelo()).status_code == 500
    assert publicador.publicados == []


class _PublicadorQueFalla:
    def __init__(self, error):
        self._error = error

    async def publicar(self, evento):
        raise self._error

    def listo(self):
        return True


def test_contrapresion_responde_429_con_retry_after():
    with TestClient(crear_app(config_prueba(), publicador=_PublicadorQueFalla(PublicadorSaturado()))) as client:
        respuesta = _post(client, "vuelos", reporte_vuelo())

    assert respuesta.status_code == 429
    assert respuesta.headers["Retry-After"] == "2"
    assert respuesta.json()["codigo"] == "contrapresion"


def test_topico_caido_responde_503_y_el_evento_no_se_da_por_aceptado():
    with TestClient(crear_app(config_prueba(), publicador=_PublicadorQueFalla(PublicadorNoDisponible()))) as client:
        respuesta = _post(client, "vuelos", reporte_vuelo())

    assert respuesta.status_code == 503
    assert "Retry-After" in respuesta.headers
    assert respuesta.json()["codigo"] == "topico_no_disponible"


def test_health_y_metricas(client):
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200
    _post(client, "vuelos", reporte_vuelo())
    assert 'solventa_telemetria_eventos_total{proveedor="vuelos",resultado="aceptado"}' in client.get("/metrics").text
