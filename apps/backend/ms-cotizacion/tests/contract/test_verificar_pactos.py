"""Verificación de proveedor: ms-cotizacion cumple el pacto que publica :APISocios (HU-2, PI-01).

El pacto lo genera y versiona api-socios en api-socios/pacts/. Si un cambio del catálogo
rompe lo que el socio consume, esta prueba falla. Correr con `pytest -m contract`
(requiere `pip install -e ".[test,contract]"`).
"""

import threading
from pathlib import Path

import pytest
import uvicorn

from app import main

from ..dobles import CatalogoEnMemoria

pact_v3 = pytest.importorskip("pact.v3")

pytestmark = pytest.mark.contract

PACTO = Path(__file__).resolve().parents[3] / "api-socios" / "pacts" / "api-socios-ms-cotizacion.json"


class _MotorFalso:
    async def dispose(self) -> None:
        pass


@pytest.fixture
def proveedor_url(monkeypatch):
    async def cargar(_motor):
        return CatalogoEnMemoria()

    monkeypatch.setattr(main, "crear_motor", lambda _config: _MotorFalso())
    monkeypatch.setattr(main.CatalogoSQL, "cargar", cargar)

    servidor = uvicorn.Server(uvicorn.Config(main.crear_app(), host="127.0.0.1", port=0, log_level="warning"))
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
    assert PACTO.is_file(), "Falta el pacto: correr primero `pytest -m contract` en api-socios"

    pact_v3.Verifier("ms-cotizacion").add_transport(url=proveedor_url).add_source(PACTO).verify()
