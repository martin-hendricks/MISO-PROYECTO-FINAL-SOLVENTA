import os
from uuid import uuid4

import pytest

from app.application import casos_uso
from app.config import Settings
from app.domain.errores import CredencialesInvalidas, CuentaDuplicada
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


async def test_alta_y_autenticacion_contra_postgres_real(uow):
    email = f"{uuid4()}@correo.com"

    creado = await casos_uso.crear_usuario(
        uow,
        tipo_documento="CC",
        numero_documento=str(uuid4().int)[:10],
        email=email,
        password_plano="clave-secreta-123",
    )

    autenticado = await casos_uso.autenticar_usuario(uow, email=email, password_plano="clave-secreta-123")
    assert autenticado.id == creado.id

    with pytest.raises(CredencialesInvalidas):
        await casos_uso.autenticar_usuario(uow, email=email, password_plano="clave-incorrecta")


async def test_email_duplicado_contra_postgres_real_es_cuenta_duplicada(uow):
    email = f"{uuid4()}@correo.com"
    await casos_uso.crear_usuario(
        uow,
        tipo_documento="CC",
        numero_documento=str(uuid4().int)[:10],
        email=email,
        password_plano="clave-secreta-123",
    )

    with pytest.raises(CuentaDuplicada):
        await casos_uso.crear_usuario(
            uow,
            tipo_documento="CC",
            numero_documento=str(uuid4().int)[:10],
            email=email,
            password_plano="otra-clave",
        )
