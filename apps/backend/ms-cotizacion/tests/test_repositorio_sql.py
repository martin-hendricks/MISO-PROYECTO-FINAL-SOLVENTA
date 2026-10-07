import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.config import Settings
from app.infrastructure.adaptador_perfil_stub import AdaptadorPerfilRiesgoStub
from app.infrastructure.catalogo_memoria import CatalogoEnMemoria
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]

DATOS_VALIDOS = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


@pytest.fixture
def catalogo():
    return CatalogoEnMemoria()


async def test_recibir_solicitud_idempotente_y_outbox_en_la_misma_transaccion(uow, catalogo):
    clave = f"it-{uuid4()}"

    primero = await casos_uso.recibir_solicitud(
        uow, catalogo, clave, uuid4(), uuid4(), uuid4(), "soat-motocicleta", "app-socio", DATOS_VALIDOS
    )
    segundo = await casos_uso.recibir_solicitud(
        uow, catalogo, clave, uuid4(), uuid4(), uuid4(), "soat-motocicleta", "app-socio", DATOS_VALIDOS
    )

    assert primero.creada and not segundo.creada
    assert segundo.solicitud.id == primero.solicitud.id
    async with uow() as tx:
        eventos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.outbox_evento WHERE agregado_id = :id"),
            {"id": primero.solicitud.id},
        )
    assert eventos == 1


async def test_obtener_vigente_devuelve_la_ultima_version_sembrada(uow):
    regla, resultado = await casos_uso.calcular_prima_solicitud(uow, "soat-motocicleta", {"cilindraje_cc": 150})

    assert regla.producto == "soat-motocicleta"
    assert resultado.prima_total == resultado.prima_neta + resultado.gastos_expedicion


async def test_cotizar_persiste_oferta_completa(uow, catalogo):
    clave = f"it-{uuid4()}"
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=1)

    resultado = await casos_uso.cotizar(
        uow, catalogo, adaptador, Settings(), clave,
        uuid4(), uuid4(), uuid4(), "soat-motocicleta", "app-socio", DATOS_VALIDOS,
    )

    assert resultado.creada
    async with uow() as tx:
        oferta_persistida = await tx.ofertas.obtener_por_solicitud(resultado.solicitud.id)
    assert oferta_persistida is not None
    assert oferta_persistida.prima == resultado.oferta.prima


async def test_reconsultar_oferta_contra_postgres_real(uow, catalogo):
    clave = f"it-{uuid4()}"
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=1)

    registrada = await casos_uso.cotizar(
        uow, catalogo, adaptador, Settings(), clave,
        uuid4(), uuid4(), uuid4(), "soat-motocicleta", "app-socio", DATOS_VALIDOS,
    )

    reconsultada = await casos_uso.reconsultar_oferta(uow, registrada.solicitud.id)

    assert not reconsultada.consulta.vencida
    assert reconsultada.consulta.oferta.prima == registrada.oferta.prima
