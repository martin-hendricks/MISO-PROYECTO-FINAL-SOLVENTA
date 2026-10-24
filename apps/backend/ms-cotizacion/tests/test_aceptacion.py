from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app.application import casos_uso_cotizaciones as casos_uso
from app.dependencies import obtener_suscripciones
from app.domain.errores import DependenciaNoDisponible, NoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import EstadoSolicitud
from app.domain.oferta import oferta_aceptada
from app.infrastructure.sql import RepositorioSolicitudesSQL
from app.infrastructure.suscripciones import SuscripcionesHTTP
from app.ports.persistencia import AceptacionConcurrente

DATOS_RIESGO = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}
PERFIL = uuid4()
SCORE = Decimal("720")


async def _cotizada(uow, catalogo, adaptador_riesgo, config):
    registro = await casos_uso.cotizar(
        uow,
        catalogo,
        adaptador_riesgo,
        config,
        f"cotizar-{uuid4()}",
        uuid4(),
        uuid4(),
        uuid4(),
        "soat-motocicleta",
        "app-socio",
        DATOS_RIESGO,
    )
    return registro.solicitud, registro.oferta


async def _aceptar(uow, suscripciones, cotizacion_id, clave="aceptar-0001"):
    return await casos_uso.aceptar_oferta(uow, suscripciones, cotizacion_id, clave, PERFIL, SCORE)


def _vencer(almacen, oferta):
    almacen.ofertas[oferta.id].vence_en = datetime.now(UTC) - timedelta(seconds=1)


async def test_aceptacion_valida(uow, almacen, catalogo, adaptador_riesgo, config, suscripciones):
    # Dado una oferta vigente que no ha sido usada
    solicitud, oferta = await _cotizada(uow, catalogo, adaptador_riesgo, config)

    # Cuando el cliente o el asesor la acepta
    aceptacion = await _aceptar(uow, suscripciones, solicitud.id)

    # Entonces se dispara la decisión de suscripción
    assert suscripciones.llamadas == [solicitud.id]
    assert aceptacion.suscripcion.decision == "ACEPTADA"
    # Y el precio aceptado es el de la oferta original
    assert aceptacion.oferta.prima == oferta.prima
    assert aceptacion.creada
    guardada = almacen.solicitudes[solicitud.id]
    assert (guardada.estado, guardada.aceptacion_key) == (EstadoSolicitud.ACEPTADA, "aceptar-0001")
    evento = almacen.eventos[-1]
    assert evento.tipo == "OfertaAceptada"
    assert evento.payload["prima"] == str(oferta.prima)


async def test_oferta_vencida(uow, almacen, catalogo, adaptador_riesgo, config, suscripciones):
    # Dado una oferta vencida
    solicitud, oferta = await _cotizada(uow, catalogo, adaptador_riesgo, config)
    _vencer(almacen, oferta)
    eventos = len(almacen.eventos)

    # Cuando se intenta aceptarla
    with pytest.raises(ReglaDeNegocioViolada) as error:
        await _aceptar(uow, suscripciones, solicitud.id)

    # Entonces se rechaza con el motivo correspondiente
    assert error.value.codigo == "oferta_vencida"
    # Y no se genera una suscripción ni se recalcula el precio
    assert suscripciones.llamadas == []
    assert almacen.ofertas[oferta.id].prima == oferta.prima
    assert almacen.solicitudes[solicitud.id].estado is EstadoSolicitud.COTIZADA
    assert len(almacen.eventos) == eventos


async def test_oferta_ya_usada(uow, almacen, catalogo, adaptador_riesgo, config, suscripciones):
    # Dado una oferta que ya fue aceptada antes
    solicitud, _ = await _cotizada(uow, catalogo, adaptador_riesgo, config)
    original = await _aceptar(uow, suscripciones, solicitud.id)
    eventos = len(almacen.eventos)

    # Cuando se intenta aceptarla de nuevo
    with pytest.raises(ReglaDeNegocioViolada) as error:
        await _aceptar(uow, suscripciones, solicitud.id, clave="otra-aceptacion")

    # Entonces se rechaza con el motivo correspondiente
    assert error.value.codigo == "oferta_ya_usada"
    # Y no se genera una segunda suscripción
    assert suscripciones.llamadas == [solicitud.id]
    assert len(almacen.eventos) == eventos
    assert almacen.solicitudes[solicitud.id].aceptada_en == original.solicitud.aceptada_en


async def test_reintento_con_la_misma_clave_devuelve_el_resultado_original(
    uow, almacen, catalogo, adaptador_riesgo, config, suscripciones
):
    solicitud, oferta = await _cotizada(uow, catalogo, adaptador_riesgo, config)
    original = await _aceptar(uow, suscripciones, solicitud.id)
    # El reintento llega después del vencimiento: el precio ya quedó congelado.
    _vencer(almacen, oferta)
    eventos = len(almacen.eventos)

    reintento = await _aceptar(uow, suscripciones, solicitud.id)

    assert not reintento.creada
    assert reintento.suscripcion == original.suscripcion
    assert reintento.solicitud.aceptada_en == original.solicitud.aceptada_en
    assert len(almacen.eventos) == eventos


async def test_si_ms_suscripcion_falla_el_reintento_retoma_la_decision(
    uow, almacen, catalogo, adaptador_riesgo, config, suscripciones
):
    solicitud, _ = await _cotizada(uow, catalogo, adaptador_riesgo, config)
    suscripciones.caida = DependenciaNoDisponible("ms-suscripcion")

    with pytest.raises(DependenciaNoDisponible):
        await _aceptar(uow, suscripciones, solicitud.id)
    suscripciones.caida = None
    reintento = await _aceptar(uow, suscripciones, solicitud.id)

    assert almacen.solicitudes[solicitud.id].estado is EstadoSolicitud.ACEPTADA
    assert not reintento.creada
    assert reintento.suscripcion.decision == "ACEPTADA"
    assert [e.tipo for e in almacen.eventos].count("OfertaAceptada") == 1


async def test_aceptacion_concurrente_con_otra_clave_es_oferta_ya_usada(
    uow, almacen, catalogo, adaptador_riesgo, config, suscripciones
):
    solicitud, oferta = await _cotizada(uow, catalogo, adaptador_riesgo, config)
    ganadora = deepcopy(solicitud)
    ganadora.aceptar(oferta, "clave-ganadora")
    almacen.aceptar_antes = ganadora

    with pytest.raises(ReglaDeNegocioViolada) as error:
        await _aceptar(uow, suscripciones, solicitud.id)

    assert error.value.codigo == "oferta_ya_usada"
    assert suscripciones.llamadas == []


async def test_aceptacion_concurrente_con_la_misma_clave_devuelve_la_ganadora(
    uow, almacen, catalogo, adaptador_riesgo, config, suscripciones
):
    solicitud, oferta = await _cotizada(uow, catalogo, adaptador_riesgo, config)
    ganadora = deepcopy(solicitud)
    ganadora.aceptar(oferta, "aceptar-0001")
    almacen.aceptar_antes = ganadora

    aceptacion = await _aceptar(uow, suscripciones, solicitud.id)

    assert not aceptacion.creada
    assert aceptacion.solicitud.aceptada_en == ganadora.aceptada_en
    assert suscripciones.llamadas == [solicitud.id]


async def test_cotizacion_inexistente(uow, suscripciones):
    with pytest.raises(NoEncontrado):
        await _aceptar(uow, suscripciones, uuid4())


async def test_solicitud_sin_cotizar_no_se_puede_aceptar(uow, catalogo, adaptador_riesgo, config):
    solicitud, oferta = await _cotizada(uow, catalogo, adaptador_riesgo, config)
    solicitud.estado = EstadoSolicitud.RECIBIDA

    with pytest.raises(TransicionInvalida):
        solicitud.aceptar(oferta, "aceptar-0001")


async def test_evento_oferta_aceptada_lleva_el_precio_congelado(uow, catalogo, adaptador_riesgo, config):
    solicitud, oferta = await _cotizada(uow, catalogo, adaptador_riesgo, config)
    solicitud.aceptar(oferta, "aceptar-0001")

    evento = oferta_aceptada(solicitud, oferta)

    assert evento.agregado_id == oferta.id
    assert evento.payload == {
        "oferta_id": str(oferta.id),
        "solicitud_id": str(solicitud.id),
        "usuario_id": str(solicitud.usuario_id),
        "prima": str(oferta.prima),
        "moneda": oferta.moneda,
        "aceptada_en": solicitud.aceptada_en.isoformat(),
    }


# --- API ---

CABECERAS = {"Idempotency-Key": "aceptar-0001"}
CUERPO = {"perfil_id": str(PERFIL), "score": "720"}


def _cotizar_por_api(client) -> dict:
    cuerpo = {
        "usuario_id": str(uuid4()),
        "socio_id": str(uuid4()),
        "consentimiento_id": str(uuid4()),
        "producto": "soat-motocicleta",
        "canal": "app-socio",
        "datos_riesgo": DATOS_RIESGO,
    }
    return client.post("/v1/cotizaciones", json=cuerpo, headers={"Idempotency-Key": f"cot-{uuid4()}"}).json()


def test_api_aceptar_devuelve_201_con_la_decision_y_200_al_reintentar(client):
    cotizacion = _cotizar_por_api(client)
    ruta = f"/v1/cotizaciones/{cotizacion['cotizacion_id']}/aceptacion"

    primera = client.post(ruta, json=CUERPO, headers=CABECERAS)
    reintento = client.post(ruta, json=CUERPO, headers=CABECERAS)

    assert primera.status_code == 201
    cuerpo = primera.json()
    assert cuerpo["estado"] == "aceptada"
    assert cuerpo["prima"] == cotizacion["prima"]
    assert cuerpo["decision"] == "ACEPTADA"
    assert reintento.status_code == 200
    assert reintento.json() == cuerpo


def test_api_oferta_ya_usada_responde_422(client):
    cotizacion = _cotizar_por_api(client)
    ruta = f"/v1/cotizaciones/{cotizacion['cotizacion_id']}/aceptacion"
    client.post(ruta, json=CUERPO, headers=CABECERAS)

    respuesta = client.post(ruta, json=CUERPO, headers={"Idempotency-Key": "otra-aceptacion"})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "oferta_ya_usada"


def test_api_ms_suscripcion_caida_responde_503(client, suscripciones):
    cotizacion = _cotizar_por_api(client)
    suscripciones.caida = DependenciaNoDisponible("ms-suscripcion")

    respuesta = client.post(
        f"/v1/cotizaciones/{cotizacion['cotizacion_id']}/aceptacion", json=CUERPO, headers=CABECERAS
    )

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "dependencia_no_disponible"


def test_api_exige_idempotency_key(client):
    respuesta = client.post(f"/v1/cotizaciones/{uuid4()}/aceptacion", json=CUERPO)

    assert respuesta.status_code == 422


# --- Infraestructura ---


class _SesionUpdate:
    def __init__(self, filas_afectadas: int) -> None:
        self.filas_afectadas = filas_afectadas
        self.consultas: list = []

    async def execute(self, consulta):
        self.consultas.append(consulta)
        return SimpleNamespace(rowcount=self.filas_afectadas)


async def _aceptada(uow, catalogo, adaptador_riesgo, config):
    solicitud, oferta = await _cotizada(uow, catalogo, adaptador_riesgo, config)
    solicitud.aceptar(oferta, "aceptar-0001")
    return solicitud


async def test_registrar_aceptacion_es_un_update_condicional(uow, catalogo, adaptador_riesgo, config):
    sesion = _SesionUpdate(filas_afectadas=1)
    solicitud = await _aceptada(uow, catalogo, adaptador_riesgo, config)

    await RepositorioSolicitudesSQL(sesion).registrar_aceptacion(solicitud)

    sql = str(sesion.consultas[0])
    assert sql.startswith("UPDATE ms_cotizacion.solicitud_cotizacion")
    assert "solicitud_cotizacion.estado = :estado_1" in sql


async def test_registrar_aceptacion_sin_fila_afectada_es_concurrente(uow, catalogo, adaptador_riesgo, config):
    solicitud = await _aceptada(uow, catalogo, adaptador_riesgo, config)

    with pytest.raises(AceptacionConcurrente):
        await RepositorioSolicitudesSQL(_SesionUpdate(filas_afectadas=0)).registrar_aceptacion(solicitud)


def _suscripciones_http(manejador) -> SuscripcionesHTTP:
    return SuscripcionesHTTP(
        httpx.AsyncClient(base_url="http://ms-suscripcion", transport=httpx.MockTransport(manejador))
    )


@pytest.mark.parametrize("estado", [200, 201])
async def test_suscripciones_http_envia_la_solicitud_y_lee_la_decision(estado):
    solicitud_id, suscripcion_id = uuid4(), uuid4()
    recibidas = []

    def manejador(request):
        recibidas.append((request.url.path, request.read()))
        return httpx.Response(
            estado, json={"suscripcion_id": str(suscripcion_id), "decision": "RECHAZADA", "motivo": "score bajo"}
        )

    decision = await _suscripciones_http(manejador).evaluar(solicitud_id, PERFIL, SCORE)

    assert (decision.suscripcion_id, decision.decision, decision.motivo) == (suscripcion_id, "RECHAZADA", "score bajo")
    ruta, cuerpo = recibidas[0]
    assert ruta == "/v1/suscripciones"
    assert httpx.Response(200, content=cuerpo).json() == {
        "solicitud_id": str(solicitud_id),
        "perfil_id": str(PERFIL),
        "score": "720",
    }


async def test_suscripciones_http_con_error_no_esta_disponible():
    with pytest.raises(DependenciaNoDisponible):
        await _suscripciones_http(lambda _r: httpx.Response(422)).evaluar(uuid4(), PERFIL, SCORE)


async def test_suscripciones_http_sin_red_no_esta_disponible():
    def manejador(request):
        raise httpx.ConnectError("sin red", request=request)

    with pytest.raises(DependenciaNoDisponible):
        await _suscripciones_http(manejador).evaluar(uuid4(), PERFIL, SCORE)


def test_obtener_suscripciones_lee_el_estado_de_la_app():
    estado = SimpleNamespace(suscripciones=object())

    assert obtener_suscripciones(SimpleNamespace(app=SimpleNamespace(state=estado))) is estado.suscripciones
