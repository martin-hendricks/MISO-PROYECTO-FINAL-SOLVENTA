import json
from datetime import datetime
from uuid import uuid4

import pytest

from app.domain.eventos import EventoBus

EVENTO_ID = "0f8fad5b-d9cb-469f-a165-70867728950e"
AGREGADO_ID = "7c9e6679-7425-40de-944b-e07fc1f90ae7"


def _mensaje(**cambios):
    datos = {
        "evento_id": EVENTO_ID,
        "tipo": "PolizaEmitida",
        "agregado_id": AGREGADO_ID,
        "ocurrido_en": "2026-11-06T12:00:00+00:00",
        "origen": "ms_polizas",
        "payload": {"usuario_id": str(uuid4()), "numero": "POL-1"},
    }
    datos.update(cambios)
    return datos


def test_parsea_bytes_str_y_dict():
    datos = _mensaje()
    crudo = json.dumps(datos).encode("utf-8")

    desde_bytes = EventoBus.desde_mensaje(crudo)
    desde_str = EventoBus.desde_mensaje(crudo.decode("utf-8"))
    desde_dict = EventoBus.desde_mensaje(datos)

    for evento in (desde_bytes, desde_str, desde_dict):
        assert evento is not None
        assert str(evento.evento_id) == EVENTO_ID
        assert str(evento.agregado_id) == AGREGADO_ID
        assert evento.tipo == "PolizaEmitida"
        assert evento.origen == "ms_polizas"
        assert evento.payload["numero"] == "POL-1"
    assert desde_bytes.ocurrido_en == datetime.fromisoformat("2026-11-06T12:00:00+00:00")


def test_ocurrido_en_y_origen_son_opcionales():
    datos = _mensaje()
    del datos["ocurrido_en"]
    del datos["origen"]

    evento = EventoBus.desde_mensaje(datos)

    assert evento is not None
    assert evento.ocurrido_en is None
    assert evento.origen is None


@pytest.mark.parametrize("campo", ["evento_id", "tipo", "agregado_id", "payload"])
def test_campos_obligatorios_faltantes_lanzan_value_error(campo):
    datos = _mensaje()
    del datos[campo]

    with pytest.raises(ValueError):
        EventoBus.desde_mensaje(datos)


@pytest.mark.parametrize("crudo", [b"{no es json", "{'comillas': 'simples'}", b""])
def test_json_invalido_lanza_value_error(crudo):
    with pytest.raises(ValueError):
        EventoBus.desde_mensaje(crudo)


@pytest.mark.parametrize("crudo", ['["una", "lista"]', "42", '"texto"', b"null"])
def test_json_que_no_es_objeto_devuelve_none(crudo):
    assert EventoBus.desde_mensaje(crudo) is None


def test_payload_que_no_es_dict_devuelve_none():
    assert EventoBus.desde_mensaje(_mensaje(payload=["no", "es", "dict"])) is None
