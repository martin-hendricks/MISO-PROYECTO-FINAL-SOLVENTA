"""Cubre la parte pura de app/crear_topico.py (sin MSK ni credenciales)."""

from __future__ import annotations

from app.crear_topico import faltantes, main


def test_faltantes_ignora_los_que_ya_existen():
    assert faltantes(["BusEventos"], ["BusEventos", "ColaPagos"]) == ["ColaPagos"]


def test_faltantes_deduplica_conservando_el_orden():
    assert faltantes([], ["BusEventos", "Otro", "BusEventos"]) == [
        "BusEventos",
        "Otro",
    ]


def test_faltantes_sin_existentes_devuelve_todos():
    assert faltantes([], ["BusEventos"]) == ["BusEventos"]


def test_main_sin_brokers_falla_con_codigo_2(monkeypatch):
    monkeypatch.delenv("MSK_BOOTSTRAP_BROKERS", raising=False)

    assert main(["BusEventos"]) == 2


def test_main_crea_el_topico_con_los_argumentos_recibidos(monkeypatch):
    llamadas = {}

    async def crear_falso(**kwargs):
        llamadas.update(kwargs)
        return list(kwargs["topicos"])

    monkeypatch.setattr("app.crear_topico.crear", crear_falso)

    codigo = main(
        [
            "BusEventos",
            "--brokers",
            "b-1.example:9098",
            "--particiones",
            "3",
            "--replicas",
            "2",
            "--region",
            "us-east-1",
        ]
    )

    assert codigo == 0
    assert llamadas == {
        "brokers": "b-1.example:9098",
        "topicos": ["BusEventos"],
        "particiones": 3,
        "replicas": 2,
        "region": "us-east-1",
    }
