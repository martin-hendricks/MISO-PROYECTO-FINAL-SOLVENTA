import json
from uuid import uuid4

import pytest

from app.domain.eventos import EventoBus


def _mensaje(**cambios):
    datos = {
        "evento_id": str(uuid4()),
        "tipo": "PolizaEmitida",
        "agregado_id": str(uuid4()),
        "ocurrido_en": "2026-01-01T00:00:00+00:00",
        "origen": "ms_polizas",
        "payload": {"usuario_id": str(uuid4())},
    }
    datos.update(cambios)
    return datos


def test_desde_mensaje_dict_valido():
    datos = _mensaje()
    evento = EventoBus.desde_mensaje(datos)
    assert evento is not None
    assert evento.tipo == "PolizaEmitida"
    assert evento.payload == datos["payload"]


def test_desde_mensaje_bytes_valido():
    datos = _mensaje()
    evento = EventoBus.desde_mensaje(json.dumps(datos).encode("utf-8"))
    assert evento is not None
    assert str(evento.evento_id) == datos["evento_id"]


def test_desde_mensaje_str_valido():
    datos = _mensaje()
    evento = EventoBus.desde_mensaje(json.dumps(datos))
    assert evento is not None


def test_desde_mensaje_payload_no_dict_devuelve_none():
    assert EventoBus.desde_mensaje(_mensaje(payload="no es un dict")) is None


def test_desde_mensaje_no_dict_devuelve_none():
    assert EventoBus.desde_mensaje(json.dumps(["lista"])) is None


def test_desde_mensaje_sin_campos_obligatorios_lanza():
    datos = _mensaje()
    del datos["tipo"]
    with pytest.raises(ValueError, match="campos obligatorios"):
        EventoBus.desde_mensaje(datos)


def test_desde_mensaje_tipo_invalido_lanza():
    with pytest.raises(ValueError):
        EventoBus.desde_mensaje(12345)


def test_desde_mensaje_sin_ocurrido_en_queda_none():
    datos = _mensaje()
    del datos["ocurrido_en"]
    evento = EventoBus.desde_mensaje(datos)
    assert evento is not None
    assert evento.ocurrido_en is None


def test_desde_mensaje_ocurrido_en_ilegible_queda_none():
    evento = EventoBus.desde_mensaje(_mensaje(ocurrido_en="no-es-una-fecha"))
    assert evento is not None
    assert evento.ocurrido_en is None


def test_desde_mensaje_origen_vacio_queda_none():
    evento = EventoBus.desde_mensaje(_mensaje(origen="   "))
    assert evento is not None
    assert evento.origen is None
