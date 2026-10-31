import asyncio
import threading
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import uvicorn

from app import main
from app.application import casos_uso_cotizaciones as casos_uso
from app.config import Settings
from app.dependencies import obtener_suscripciones, obtener_uow
from app.infrastructure.adaptador_perfil_stub import AdaptadorPerfilRiesgoStub

from ..dobles import (
    AlmacenEnMemoria,
    CatalogoEnMemoria,
    SuscripcionesFalsas,
    UnidadDeTrabajoEnMemoria,
    regla_rating_soat_motocicleta,
)

pact_v3 = pytest.importorskip("pact.v3")

pytestmark = pytest.mark.contract

BACKEND = Path(__file__).resolve().parents[3]
PACTO_API_SOCIOS = BACKEND / "api-socios" / "pacts" / "api-socios-ms-cotizacion.json"
PACTO_BFF_WEB = BACKEND / "bff-web" / "pacts" / "bff-web-ms-cotizacion.json"
PACTO_BFF_MOVIL = BACKEND / "bff-movil" / "pacts" / "bff-movil-ms-cotizacion.json"
DATOS_RIESGO = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}


class _MotorFalso:
    async def dispose(self) -> None:
        pass


class EstadoProveedor:
    """Lo que la app real lee en vez de PostgreSQL y ms-suscripcion. Cada estado del pacto
    lo reinicia antes de sembrar, así ninguna interacción depende de la anterior."""

    def __init__(self) -> None:
        self.reiniciar()

    def reiniciar(self, decision: str = "ACEPTADA") -> None:
        self.almacen = AlmacenEnMemoria()
        regla = regla_rating_soat_motocicleta()
        self.almacen.reglas_rating[regla.id] = regla
        self.suscripciones = SuscripcionesFalsas(decision)

    def uow(self):
        return lambda: UnidadDeTrabajoEnMemoria(self.almacen)

    def sembrar_cotizacion(self, cotizacion_id: UUID | None = None, oferta_id: UUID | None = None) -> None:
        """Cotiza por el caso de uso real y fija los ids que declara el pacto."""
        registro = asyncio.run(
            casos_uso.cotizar(
                self.uow(),
                CatalogoEnMemoria(),
                AdaptadorPerfilRiesgoStub(),
                Settings(),
                f"estado-pacto-{uuid4()}",
                uuid4(),
                uuid4(),
                uuid4(),
                "soat-motocicleta",
                "web",
                DATOS_RIESGO,
            )
        )
        solicitud = self.almacen.solicitudes.pop(registro.solicitud.id)
        oferta = self.almacen.ofertas.pop(registro.oferta.id)
        solicitud.id = cotizacion_id or solicitud.id
        oferta.solicitud_id = solicitud.id
        oferta.id = oferta_id or oferta.id
        self.almacen.solicitudes[solicitud.id] = solicitud
        self.almacen.ofertas[oferta.id] = oferta

    def estados(self) -> dict:
        def cotizacion_vigente(parameters):
            self.reiniciar()
            self.sembrar_cotizacion(UUID(parameters["cotizacion_id"]))

        def cotizacion_que_la_suscripcion_rechaza(parameters):
            self.reiniciar(decision="RECHAZADA")
            self.sembrar_cotizacion(UUID(parameters["cotizacion_id"]))

        def oferta_emitida(parameters):
            self.reiniciar()
            self.sembrar_cotizacion(oferta_id=UUID(parameters["oferta_id"]))

        return {
            "existe una cotización vigente": cotizacion_vigente,
            "existe una cotización vigente que la suscripción acepta": cotizacion_vigente,
            "existe una cotización vigente que la suscripción rechaza": cotizacion_que_la_suscripcion_rechaza,
            "existe una oferta emitida": oferta_emitida,
        }

    def preparar(self, state: str | None, parameters: dict | None = None) -> None:
        """Pact también llama al handler en las interacciones sin estado: esas no siembran nada."""
        sembrar = self.estados().get(state or "")
        if sembrar is None and state:
            raise KeyError(f"Estado de proveedor no soportado: {state!r}")
        if sembrar is not None:
            sembrar(parameters or {})


@pytest.fixture
def estado() -> EstadoProveedor:
    return EstadoProveedor()


@pytest.fixture
def proveedor_url(monkeypatch, estado):
    async def cargar(_motor):
        return CatalogoEnMemoria()

    monkeypatch.setattr(main, "crear_motor", lambda _config: _MotorFalso())
    monkeypatch.setattr(main.CatalogoSQL, "cargar", cargar)

    app = main.crear_app()
    app.dependency_overrides[obtener_uow] = lambda: estado.uow()
    app.dependency_overrides[obtener_suscripciones] = lambda: estado.suscripciones

    servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning"))
    hilo = threading.Thread(target=servidor.run, daemon=True)
    hilo.start()
    listo = threading.Event()
    while not servidor.started and hilo.is_alive():
        listo.wait(0.05)
    puerto = servidor.servers[0].sockets[0].getsockname()[1]
    yield f"http://localhost:{puerto}"
    servidor.should_exit = True
    hilo.join(timeout=5)


def test_ms_cotizacion_cumple_el_pacto_de_api_socios(proveedor_url):
    assert PACTO_API_SOCIOS.is_file(), "Falta el pacto: correr primero `pytest -m contract` en api-socios"

    pact_v3.Verifier("ms-cotizacion").add_transport(url=proveedor_url).add_source(PACTO_API_SOCIOS).verify()


@pytest.mark.parametrize(
    ("consumidor", "pacto"),
    [("bff-web", PACTO_BFF_WEB), ("bff-movil", PACTO_BFF_MOVIL)],
)
def test_ms_cotizacion_cumple_el_pacto_de_cada_bff(proveedor_url, estado, consumidor, pacto):
    assert pacto.is_file(), f"Falta el pacto: correr primero `pytest -m contract` en {consumidor}"

    (
        pact_v3.Verifier("ms-cotizacion")
        .add_transport(url=proveedor_url)
        .add_source(pacto)
        .state_handler(estado.preparar, teardown=False)
        .verify()
    )
