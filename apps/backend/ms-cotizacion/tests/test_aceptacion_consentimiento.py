from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app.application import casos_uso_cotizaciones as casos_uso
from app.dependencies import obtener_adaptador_perfil_riesgo, obtener_consentimientos
from app.domain.errores import ConsentimientoRevocado, DependenciaNoDisponible
from app.domain.modelos import EstadoSolicitud
from app.infrastructure.consentimiento_perfilamiento import ConsentimientoPerfilamientoHTTP
from tests.dobles import ConsentimientosFalsos

PRODUCTO = "soat-motocicleta"
DATOS_RIESGO = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}
PERFIL = uuid4()
SCORE = Decimal("720")


class PerfilInmediato:
    async def obtener_factor(self, usuario_id, producto):
        return Decimal("1.2")


class PerfilCaido:
    async def obtener_factor(self, usuario_id, producto):
        raise RuntimeError("sin perfil")


async def _cotizada(uow, catalogo, config, adaptador=None):
    registro = await casos_uso.cotizar(
        uow,
        catalogo,
        adaptador or PerfilInmediato(),
        config,
        f"cotizar-{uuid4()}",
        uuid4(),
        uuid4(),
        uuid4(),
        PRODUCTO,
        "web",
        DATOS_RIESGO,
    )
    return registro.solicitud


async def _aceptar(uow, suscripciones, consentimientos, cotizacion_id, clave="aceptar-0001"):
    return await casos_uso.aceptar_oferta(uow, suscripciones, consentimientos, cotizacion_id, clave, PERFIL, SCORE)


async def test_consentimiento_revocado_despues_de_cotizar_rechaza_la_aceptacion(
    uow, almacen, catalogo, config, suscripciones
):
    solicitud = await _cotizada(uow, catalogo, config)
    consentimientos = ConsentimientosFalsos(productos={PRODUCTO}, vigentes=set())

    with pytest.raises(ConsentimientoRevocado) as error:
        await _aceptar(uow, suscripciones, consentimientos, solicitud.id)

    assert error.value.codigo == "consentimiento_revocado"
    assert consentimientos.consultas == [solicitud.usuario_id]
    assert suscripciones.llamadas == []
    assert almacen.solicitudes[solicitud.id].estado != EstadoSolicitud.ACEPTADA
    assert almacen.solicitudes[solicitud.id].aceptacion_key is None


async def test_consentimiento_vigente_permite_aceptar(uow, catalogo, config, suscripciones):
    solicitud = await _cotizada(uow, catalogo, config)
    consentimientos = ConsentimientosFalsos(productos={PRODUCTO}, vigentes={solicitud.usuario_id})

    aceptacion = await _aceptar(uow, suscripciones, consentimientos, solicitud.id)

    assert aceptacion.creada is True
    assert suscripciones.llamadas == [solicitud.id]


async def test_producto_que_no_usa_el_perfil_no_consulta_el_consentimiento(uow, catalogo, config, suscripciones):
    solicitud = await _cotizada(uow, catalogo, config)
    consentimientos = ConsentimientosFalsos(productos={"vida-crediticia"}, vigentes=set())

    aceptacion = await _aceptar(uow, suscripciones, consentimientos, solicitud.id)

    assert aceptacion.creada is True
    assert consentimientos.consultas == []


async def test_oferta_con_factor_de_respaldo_no_uso_el_perfil_y_se_acepta(uow, catalogo, config, suscripciones):
    solicitud = await _cotizada(uow, catalogo, config, PerfilCaido())
    consentimientos = ConsentimientosFalsos(productos={PRODUCTO}, vigentes=set())

    aceptacion = await _aceptar(uow, suscripciones, consentimientos, solicitud.id)

    assert aceptacion.creada is True
    assert consentimientos.consultas == []


async def test_reintento_con_la_misma_clave_tras_revocar_devuelve_la_aceptacion_original(
    uow, catalogo, config, suscripciones
):
    solicitud = await _cotizada(uow, catalogo, config)
    consentimientos = ConsentimientosFalsos(productos={PRODUCTO}, vigentes={solicitud.usuario_id})
    original = await _aceptar(uow, suscripciones, consentimientos, solicitud.id)
    consentimientos.vigentes = set()

    reintento = await _aceptar(uow, suscripciones, consentimientos, solicitud.id)

    assert reintento.creada is False
    assert reintento.suscripcion == original.suscripcion


async def test_ms_perfilamiento_caido_no_acepta(uow, almacen, catalogo, config, suscripciones):
    solicitud = await _cotizada(uow, catalogo, config)
    consentimientos = ConsentimientosFalsos(productos={PRODUCTO})
    consentimientos.caida = DependenciaNoDisponible("ms-perfilamiento")

    with pytest.raises(DependenciaNoDisponible):
        await _aceptar(uow, suscripciones, consentimientos, solicitud.id)

    assert almacen.solicitudes[solicitud.id].aceptacion_key is None


def _http(manejador) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url="http://ms-perfilamiento", transport=httpx.MockTransport(manejador))


@pytest.mark.parametrize(("estado", "vigente"), [(200, True), (404, False), (403, False)])
async def test_adaptador_http_interpreta_la_respuesta_de_ms_perfilamiento(estado, vigente):
    usuario = uuid4()
    rutas = []

    def manejador(peticion):
        rutas.append((peticion.method, peticion.url.path))
        return httpx.Response(estado, json={})

    async with _http(manejador) as http:
        adaptador = ConsentimientoPerfilamientoHTTP(http, ["vida-crediticia"])
        assert await adaptador.vigente(usuario) is vigente

    assert rutas == [("GET", f"/v1/consentimientos/{usuario}")]


async def test_adaptador_http_error_del_servicio_es_dependencia_no_disponible():
    async with _http(lambda _: httpx.Response(500)) as http:
        with pytest.raises(DependenciaNoDisponible):
            await ConsentimientoPerfilamientoHTTP(http, []).vigente(uuid4())


async def test_adaptador_http_sin_red_es_dependencia_no_disponible():
    def manejador(peticion):
        raise httpx.ConnectError("sin red", request=peticion)

    async with _http(manejador) as http:
        with pytest.raises(DependenciaNoDisponible):
            await ConsentimientoPerfilamientoHTTP(http, []).vigente(uuid4())


def test_adaptador_http_requiere_solo_los_productos_configurados():
    adaptador = ConsentimientoPerfilamientoHTTP(httpx.AsyncClient(), ["vida-crediticia"])

    assert adaptador.requiere("vida-crediticia") is True
    assert adaptador.requiere("soat-motocicleta") is False


def test_api_consentimiento_revocado_responde_422(client, consentimientos):
    consentimientos.productos = {PRODUCTO}
    consentimientos.vigentes = set()
    cuerpo = {
        "usuario_id": str(uuid4()),
        "socio_id": str(uuid4()),
        "consentimiento_id": str(uuid4()),
        "producto": PRODUCTO,
        "canal": "web",
        "datos_riesgo": DATOS_RIESGO,
    }
    client.app.dependency_overrides[obtener_adaptador_perfil_riesgo] = PerfilInmediato
    cotizacion = client.post("/v1/cotizaciones", json=cuerpo, headers={"Idempotency-Key": f"cot-{uuid4()}"}).json()

    respuesta = client.post(
        f"/v1/cotizaciones/{cotizacion['cotizacion_id']}/aceptacion",
        json={"perfil_id": str(PERFIL), "score": "720"},
        headers={"Idempotency-Key": "aceptar-0001"},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "consentimiento_revocado"


def test_obtener_consentimientos_lee_el_adaptador_del_estado_de_la_app():
    estado = SimpleNamespace(consentimientos=ConsentimientosFalsos())

    assert obtener_consentimientos(SimpleNamespace(app=SimpleNamespace(state=estado))) is estado.consentimientos
