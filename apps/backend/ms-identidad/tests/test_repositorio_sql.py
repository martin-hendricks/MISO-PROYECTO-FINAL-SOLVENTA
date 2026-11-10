import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.config import Settings
from app.domain.errores import CredencialesInvalidas, CuentaDuplicada
from app.infrastructure.kyc import VerificadorKYCStub
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


async def _alta(uow, **extra):
    return await casos_uso.crear_usuario(
        uow,
        VerificadorKYCStub(),
        tipo_documento="CC",
        numero_documento=extra.get("documento", str(uuid4().int)[:12]),
        email=extra.get("email", f"{uuid4()}@correo.com"),
        password_plano="clave-secreta-123",
        nombre=extra.get("nombre", "Ana"),
        apellidos=extra.get("apellidos", "Lopez"),
    )


async def test_alta_y_autenticacion_contra_postgres_real(uow):
    email = f"{uuid4()}@correo.com"

    creado = await casos_uso.crear_usuario(
        uow,
        VerificadorKYCStub(),
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
        VerificadorKYCStub(),
        tipo_documento="CC",
        numero_documento=str(uuid4().int)[:10],
        email=email,
        password_plano="clave-secreta-123",
    )

    with pytest.raises(CuentaDuplicada):
        await casos_uso.crear_usuario(
            uow,
            VerificadorKYCStub(),
            tipo_documento="CC",
            numero_documento=str(uuid4().int)[:10],
            email=email,
            password_plano="otra-clave",
        )


async def test_listar_clientes_filtra_por_ilike_ordena_y_respeta_ids(uow):
    marca = uuid4().hex[:10]
    ana = await _alta(uow, nombre="Ana", apellidos=f"Mendez{marca}", email=f"ana-{marca}@correo.com", documento=f"1{marca}")
    ana_2 = await _alta(uow, nombre="Ana", apellidos=f"Mendez{marca}", email=f"ana2-{marca}@correo.com", documento=f"2{marca}")
    bea = await _alta(uow, nombre="Bea", apellidos=f"Mendez{marca}", email=f"bea-{marca}@correo.com", documento=f"3{marca}")
    zulu = await _alta(uow, nombre=f"Nom{marca}", apellidos=f"Zulu{marca}", email=f"zulu-{marca}@correo.com", documento=f"4{marca}")
    operador = await _alta(
        uow, nombre="Ops", apellidos=f"Mendez{marca}", email=f"ops-{marca}@correo.com", documento=f"5{marca}"
    )
    motor = crear_motor(Settings())
    try:
        async with motor.begin() as conn:
            await conn.execute(
                text("UPDATE ms_identidad.usuario SET rol = 'operador' WHERE usuario_id = :id"),
                {"id": operador.id},
            )
    finally:
        await motor.dispose()

    async with uow() as tx:
        por_apellido, _ = await tx.usuarios.listar_clientes(None, marca.upper(), None, 1)
        por_nombre, _ = await tx.usuarios.listar_clientes(None, f"nom{marca}", None, 1)
        por_correo, _ = await tx.usuarios.listar_clientes(None, f"BEA-{marca}", None, 1)
        por_documento, _ = await tx.usuarios.listar_clientes(None, f"3{marca}", None, 1)
        por_ids, hay_mas = await tx.usuarios.listar_clientes(None, None, [zulu.id, ana.id], 1)

    assert [usuario.id for usuario in por_apellido] == [
        usuario.id for usuario in sorted((ana, ana_2, bea, zulu), key=lambda usuario: (usuario.apellidos, usuario.nombre, usuario.id))
    ]
    assert [usuario.id for usuario in por_nombre] == [zulu.id]
    assert [usuario.id for usuario in por_correo] == [bea.id]
    assert [usuario.id for usuario in por_documento] == [bea.id]
    assert {usuario.id for usuario in por_ids} == {zulu.id, ana.id}
    assert hay_mas is False
    assert operador.id not in {usuario.id for usuario in por_apellido}
