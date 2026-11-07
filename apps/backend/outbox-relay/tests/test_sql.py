import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.infrastructure.sql import RepositorioOutboxSQL, crear_motor

from .dobles import PublicadorDoble

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]

ESQUEMA = "ms_cotizacion"


@pytest.fixture
async def motor():
    motor = crear_motor(os.environ["DATABASE_URL"])
    # asyncpg no permite varios statements en un solo execute (a diferencia
    # de psycopg2) -- cada DDL va en su propia llamada.
    async with motor.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {ESQUEMA}"))
        await conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {ESQUEMA}.outbox_evento (
                    id UUID PRIMARY KEY,
                    tipo TEXT NOT NULL,
                    agregado_id UUID NOT NULL,
                    payload JSONB NOT NULL,
                    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
                    publicado_en TIMESTAMPTZ
                )
                """
            )
        )
        await conn.execute(text(f"TRUNCATE {ESQUEMA}.outbox_evento"))
    yield motor
    await motor.dispose()


async def _insertar_evento(motor, **cambios):
    datos = {
        "id": uuid4(),
        "tipo": "PolizaEmitida",
        "agregado_id": uuid4(),
        "payload": {"usuario_id": str(uuid4())},
    }
    datos.update(cambios)
    async with motor.begin() as conn:
        await conn.execute(
            text(
                f"""
                INSERT INTO {ESQUEMA}.outbox_evento (id, tipo, agregado_id, payload)
                VALUES (:id, :tipo, :agregado_id, :payload)
                """
            ),
            {**datos, "payload": __import__("json").dumps(datos["payload"])},
        )
    return datos["id"]


async def test_publica_pendientes_y_marca_publicado_en(motor):
    evento_id = await _insertar_evento(motor)
    repositorio = RepositorioOutboxSQL(motor, ESQUEMA)
    publicador = PublicadorDoble()

    total = await repositorio.publicar_pendientes(publicador, lote=10, ahora=datetime.now(UTC))

    assert total == 1
    assert len(publicador.publicados) == 1
    assert publicador.publicados[0].evento_id == evento_id

    async with motor.begin() as conn:
        publicado_en = await conn.scalar(
            text(f"SELECT publicado_en FROM {ESQUEMA}.outbox_evento WHERE id = :id"),
            {"id": evento_id},
        )
    assert publicado_en is not None


async def test_no_reprocesa_eventos_ya_publicados(motor):
    await _insertar_evento(motor)
    repositorio = RepositorioOutboxSQL(motor, ESQUEMA)
    publicador = PublicadorDoble()

    await repositorio.publicar_pendientes(publicador, lote=10, ahora=datetime.now(UTC))
    segunda_vuelta = await repositorio.publicar_pendientes(
        publicador, lote=10, ahora=datetime.now(UTC)
    )

    assert segunda_vuelta == 0
    assert len(publicador.publicados) == 1


async def test_respeta_el_tamano_de_lote(motor):
    for _ in range(3):
        await _insertar_evento(motor)
    repositorio = RepositorioOutboxSQL(motor, ESQUEMA)
    publicador = PublicadorDoble()

    total = await repositorio.publicar_pendientes(publicador, lote=2, ahora=datetime.now(UTC))

    assert total == 2


async def test_un_fallo_del_publicador_no_marca_nada_como_publicado(motor):
    evento_id = await _insertar_evento(motor)
    repositorio = RepositorioOutboxSQL(motor, ESQUEMA)
    publicador = PublicadorDoble()
    publicador.fallar = RuntimeError("kafka no disponible")

    with pytest.raises(RuntimeError):
        await repositorio.publicar_pendientes(publicador, lote=10, ahora=datetime.now(UTC))

    async with motor.begin() as conn:
        publicado_en = await conn.scalar(
            text(f"SELECT publicado_en FROM {ESQUEMA}.outbox_evento WHERE id = :id"),
            {"id": evento_id},
        )
    assert publicado_en is None


def test_constructor_valida_el_esquema(motor):
    with pytest.raises(ValueError, match="no permitido"):
        RepositorioOutboxSQL(motor, "esquema_no_permitido")
