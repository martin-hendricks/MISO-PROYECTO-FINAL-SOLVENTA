"""Cubre crear_app() (TestClient, sin servidor real) y main() (con los
constructores de infraestructura real mockeados -- sin Postgres/MSK)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import crear_app, main


def test_crear_app_expone_health():
    app = crear_app()
    client = TestClient(app)

    respuesta = client.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_crear_app_expone_metrics():
    app = crear_app()
    client = TestClient(app)

    respuesta = client.get("/metrics")

    assert respuesta.status_code == 200
    assert "http_request_duration_seconds" in respuesta.text


def test_crear_app_agrega_cabecera_de_correlacion():
    app = crear_app()
    client = TestClient(app)

    respuesta = client.get("/health")

    assert "X-Correlation-Id" in respuesta.headers


async def test_main_arma_solo_los_repositorios_con_url_configurada(monkeypatch):
    """Settings con solo 2 de las 6 DATABASE_URL configuradas: main() debe
    construir un motor/repositorio por cada una, y omitir las vacías sin
    fallar (fuente_outbox_sin_configurar)."""
    config = Settings(
        database_url_ms_cotizacion="postgresql+asyncpg://x/y",
        database_url_ms_polizas="postgresql+asyncpg://x/z",
        msk_bootstrap_brokers="b-1:9098",
    )
    monkeypatch.setattr("app.main.Settings", lambda: config)

    motor_falso = MagicMock()
    motor_falso.dispose = AsyncMock()
    crear_motor_mock = MagicMock(return_value=motor_falso)
    monkeypatch.setattr("app.main.crear_motor", crear_motor_mock)

    repos_construidos: list[str] = []

    class _RepoFalso:
        def __init__(self, motor, esquema):
            repos_construidos.append(esquema)

    monkeypatch.setattr("app.main.RepositorioOutboxSQL", _RepoFalso)

    publicador_falso = MagicMock()
    publicador_falso.cerrar = AsyncMock()
    monkeypatch.setattr("app.main.PublicadorMSK", lambda _config: publicador_falso)

    bucle_relay_mock = AsyncMock()
    monkeypatch.setattr("app.main.bucle_relay", bucle_relay_mock)

    with patch("app.main.uvicorn.Server") as ServerMock:
        instancia_servidor = ServerMock.return_value
        instancia_servidor.serve = AsyncMock()

        await main()

    assert sorted(repos_construidos) == ["ms_cotizacion", "ms_polizas"]
    assert crear_motor_mock.call_count == 2
    motor_falso.dispose.assert_awaited()
    publicador_falso.cerrar.assert_awaited_once()
    bucle_relay_mock.assert_awaited_once()
    instancia_servidor.serve.assert_awaited_once()


async def test_main_sin_ninguna_url_configurada_no_construye_repositorios(monkeypatch):
    config = Settings()  # las 6 DATABASE_URL_* quedan vacías por defecto
    monkeypatch.setattr("app.main.Settings", lambda: config)
    monkeypatch.setattr("app.main.crear_motor", MagicMock())

    publicador_falso = MagicMock()
    publicador_falso.cerrar = AsyncMock()
    monkeypatch.setattr("app.main.PublicadorMSK", lambda _config: publicador_falso)

    bucle_relay_mock = AsyncMock()
    monkeypatch.setattr("app.main.bucle_relay", bucle_relay_mock)

    with patch("app.main.uvicorn.Server") as ServerMock:
        ServerMock.return_value.serve = AsyncMock()
        await main()

    # bucle_relay recibe una lista vacía de repositorios -- no lanza, solo
    # no publica nada (ya cubierto por ejecutar_ciclo en test_relay.py).
    repositorios_pasados = bucle_relay_mock.await_args.args[0]
    assert repositorios_pasados == []
