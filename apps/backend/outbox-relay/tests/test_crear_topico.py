"""Cubre la parte pura de app/crear_topico.py (sin MSK ni credenciales)."""

from __future__ import annotations

import ssl

from app.crear_topico import crear, faltantes, main


def test_faltantes_ignora_los_que_ya_existen():
    assert faltantes(["BusEventos"], ["BusEventos", "ColaPagos"]) == ["ColaPagos"]


def test_faltantes_deduplica_conservando_el_orden():
    assert faltantes([], ["BusEventos", "Otro", "BusEventos"]) == [
        "BusEventos",
        "Otro",
    ]


def test_faltantes_sin_existentes_devuelve_todos():
    assert faltantes([], ["BusEventos"]) == ["BusEventos"]


async def test_crear_pasa_un_contexto_tls_explicito(monkeypatch):
    """El Job de bootstrap fallaría igual que el resto: aiokafka >= 0.13 exige
    ssl_context cuando el protocolo es SASL_SSL."""
    import aiokafka.admin as admin_module

    class _AdminFalso:
        instancias: list["_AdminFalso"] = []

        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            self.cerrado = False
            _AdminFalso.instancias.append(self)

        async def start(self) -> None:
            pass

        async def create_topics(self, topicos) -> None:
            pass

        async def close(self) -> None:
            self.cerrado = True

    monkeypatch.setattr(admin_module, "AIOKafkaAdminClient", _AdminFalso)

    creados = await crear(
        brokers="b-1.example:9098",
        topicos=["BusEventos"],
        particiones=6,
        replicas=2,
        region="us-east-1",
    )

    admin = _AdminFalso.instancias[0]
    assert creados == ["BusEventos"]
    assert isinstance(admin.kwargs["ssl_context"], ssl.SSLContext)
    assert admin.kwargs["ssl_context"].verify_mode == ssl.CERT_REQUIRED
    assert admin.cerrado is True


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
