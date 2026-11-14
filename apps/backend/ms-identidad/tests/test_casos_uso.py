from uuid import uuid4

import pytest

from app.application import casos_uso
from app.domain.errores import (
    Conflicto,
    CredencialesInvalidas,
    CuentaDuplicada,
    CuentaInactiva,
    DependenciaNoDisponible,
    IdentidadNoVerificada,
    NoEncontrado,
    ReglaDeNegocioViolada,
)
from app.domain.modelos import EstadoUsuario
from app.infrastructure.kyc import VerificadorKYCStub
from app.ports.persistencia import CuentaYaExiste


async def _crear(
    uow, email="camila@correo.com", documento="1012345678", password="clave-secreta-123", kyc=VerificadorKYCStub()
):
    return await casos_uso.crear_usuario(
        uow,
        kyc,
        tipo_documento="CC",
        numero_documento=documento,
        email=email,
        password_plano=password,
    )


async def test_crear_usuario_persiste_con_password_hasheado(uow, almacen):
    usuario = await _crear(uow)

    assert almacen.usuarios[usuario.id].email == "camila@correo.com"
    assert almacen.usuarios[usuario.id].password_hash != "clave-secreta-123"


async def test_crear_usuario_con_canal_lo_persiste(uow):
    usuario = await casos_uso.crear_usuario(
        uow,
        VerificadorKYCStub(),
        tipo_documento="CC",
        numero_documento="1012345678",
        email="camila@correo.com",
        password_plano="clave-secreta-123",
        canal="android",
    )

    assert usuario.canal == "android"


async def test_crear_usuario_con_email_duplicado_es_cuenta_duplicada(uow):
    await _crear(uow, email="camila@correo.com", documento="1")

    with pytest.raises(CuentaDuplicada):
        await _crear(uow, email="CAMILA@correo.com", documento="2")


async def test_crear_usuario_con_documento_duplicado_es_cuenta_duplicada(uow):
    await _crear(uow, email="uno@correo.com", documento="1012345678")

    with pytest.raises(CuentaDuplicada):
        await _crear(uow, email="dos@correo.com", documento="1012345678")


async def test_crear_usuario_con_email_duplicado_no_deja_fila_a_medias(uow, almacen):
    await _crear(uow, email="camila@correo.com", documento="1")

    with pytest.raises(CuentaDuplicada):
        await _crear(uow, email="camila@correo.com", documento="2")

    assert len(almacen.usuarios) == 1


async def test_carrera_entre_dos_altas_se_traduce_a_cuenta_duplicada(uow, almacen):
    almacen.chocar_en_proximo_commit = True

    with pytest.raises(CuentaDuplicada):
        await _crear(uow)


async def test_documento_rechazado_por_kyc_no_crea_la_cuenta(uow, almacen):
    kyc = VerificadorKYCStub(documentos_rechazados=["0000000000"])

    with pytest.raises(IdentidadNoVerificada):
        await _crear(uow, documento="0000000000", kyc=kyc)

    assert almacen.usuarios == {}


async def test_el_doble_de_kyc_sin_configurar_aprueba_cualquier_documento(uow, almacen):
    await _crear(uow, documento="0000000000")

    assert len(almacen.usuarios) == 1


async def test_el_doble_de_kyc_solo_rechaza_los_documentos_configurados(uow, almacen):
    kyc = VerificadorKYCStub(documentos_rechazados=["111", "222"])

    await _crear(uow, email="ok@correo.com", documento="333", kyc=kyc)
    with pytest.raises(IdentidadNoVerificada):
        await _crear(uow, email="no@correo.com", documento="222", kyc=kyc)

    assert [u.numero_documento for u in almacen.usuarios.values()] == ["333"]


async def test_kyc_caido_no_crea_la_cuenta(uow, almacen):
    with pytest.raises(DependenciaNoDisponible):
        await _crear(uow, kyc=VerificadorKYCStub(fallar=True))

    assert almacen.usuarios == {}


async def test_el_kyc_recibe_el_documento_normalizado(uow):
    class KycEspia:
        recibido = None

        async def verificar(self, tipo_documento, numero_documento):
            KycEspia.recibido = (tipo_documento, numero_documento)
            return True

    await casos_uso.crear_usuario(
        uow, KycEspia(), tipo_documento=" cc ", numero_documento=" 123 ", email="a@b.co", password_plano="clave-secreta-123"
    )

    assert KycEspia.recibido == ("CC", "123")


async def test_autenticar_con_credenciales_correctas_devuelve_el_usuario(uow):
    creado = await _crear(uow, email="camila@correo.com", password="clave-secreta-123")

    autenticado = await casos_uso.autenticar_usuario(uow, email="camila@correo.com", password_plano="clave-secreta-123")

    assert autenticado.id == creado.id


async def test_autenticar_es_insensible_a_mayusculas_en_el_email(uow):
    await _crear(uow, email="camila@correo.com", password="clave-secreta-123")

    autenticado = await casos_uso.autenticar_usuario(uow, email="CAMILA@Correo.com", password_plano="clave-secreta-123")

    assert autenticado.email == "camila@correo.com"


async def test_autenticar_con_password_incorrecto_es_credenciales_invalidas(uow):
    await _crear(uow, email="camila@correo.com", password="clave-secreta-123")

    with pytest.raises(CredencialesInvalidas):
        await casos_uso.autenticar_usuario(uow, email="camila@correo.com", password_plano="otra-clave")


async def test_autenticar_email_inexistente_es_credenciales_invalidas(uow):
    with pytest.raises(CredencialesInvalidas):
        await casos_uso.autenticar_usuario(uow, email="nadie@correo.com", password_plano="clave-secreta-123")


async def test_cambiar_estado_escribe_un_evento_y_bloquea_el_login(uow, almacen):
    creado = await _crear(uow, email="camila@correo.com", password="clave-secreta-123")

    inactivo = await casos_uso.cambiar_estado_cliente(uow, creado.id, "INACTIVO")

    assert inactivo.estado is EstadoUsuario.INACTIVO
    assert len(almacen.outbox) == 1
    evento = almacen.outbox[0]
    assert evento.tipo == "UsuarioInactivado"
    assert evento.agregado_id == creado.id
    assert evento.payload["usuario_id"] == str(creado.id)
    assert "ocurrido_en" in evento.payload
    with pytest.raises(CuentaInactiva):
        await casos_uso.autenticar_usuario(uow, email="camila@correo.com", password_plano="clave-secreta-123")

    await casos_uso.cambiar_estado_cliente(uow, creado.id, "INACTIVO")
    assert len(almacen.outbox) == 1

    activo = await casos_uso.cambiar_estado_cliente(uow, creado.id, "ACTIVO")
    assert activo.estado is EstadoUsuario.ACTIVO
    assert almacen.outbox[-1].tipo == "UsuarioReactivado"
    assert almacen.outbox[-1].payload["usuario_id"] == str(creado.id)
    assert (await casos_uso.autenticar_usuario(uow, email="camila@correo.com", password_plano="clave-secreta-123")).id == creado.id


async def test_el_estado_y_el_evento_se_confirman_en_la_misma_unidad_de_trabajo(uow, almacen):
    creado = await _crear(uow)
    almacen.chocar_en_proximo_commit = True

    with pytest.raises(CuentaYaExiste):
        await casos_uso.cambiar_estado_cliente(uow, creado.id, "INACTIVO")

    assert almacen.usuarios[creado.id].estado is EstadoUsuario.ACTIVO
    assert almacen.outbox == []


async def test_editar_cliente_normaliza_el_correo_y_rechaza_duplicado(uow, almacen):
    uno = await _crear(uow, email="uno@correo.com", documento="1")
    await _crear(uow, email="dos@correo.com", documento="2")

    editado = await casos_uso.editar_cliente(
        uow, uno.id, nombre=" Ana ", apellidos=" Lopez ", email=" ANA@correo.com "
    )
    assert editado.email == "ana@correo.com"
    assert almacen.usuarios[uno.id].nombre == "Ana"

    with pytest.raises(Conflicto):
        await casos_uso.editar_cliente(uow, uno.id, nombre="Ana", apellidos="Lopez", email="DOS@correo.com")
    assert almacen.usuarios[uno.id].email == "ana@correo.com"


async def test_editar_o_cambiar_estado_de_desconocido_o_no_cliente_es_404(uow, almacen):
    with pytest.raises(NoEncontrado):
        await casos_uso.editar_cliente(uow, uuid4(), nombre="Ana", apellidos="Lopez", email="ana@correo.com")

    creado = await _crear(uow, email="staff@correo.com", documento="9")
    almacen.usuarios[creado.id].rol = "operador"
    with pytest.raises(NoEncontrado):
        await casos_uso.cambiar_estado_cliente(uow, creado.id, "INACTIVO")
    assert almacen.outbox == []


async def test_listar_clientes_rechaza_rol_consulta_e_ids(uow):
    with pytest.raises(ReglaDeNegocioViolada) as rol:
        await casos_uso.listar_clientes(uow, rol="asesor", estado=None, q=None, ids=None, pagina=1)
    assert rol.value.codigo == "rol_no_soportado"

    with pytest.raises(ReglaDeNegocioViolada) as corta:
        await casos_uso.listar_clientes(uow, rol="cliente", estado=None, q="a", ids=None, pagina=1)
    assert corta.value.codigo == "consulta_corta"

    with pytest.raises(ReglaDeNegocioViolada) as larga:
        await casos_uso.listar_clientes(uow, rol="cliente", estado=None, q="x" * 81, ids=None, pagina=1)
    assert larga.value.codigo == "consulta_larga"

    with pytest.raises(ReglaDeNegocioViolada) as ids:
        await casos_uso.listar_clientes(
            uow, rol="cliente", estado=None, q=None, ids=[uuid4() for _ in range(51)], pagina=1
        )
    assert ids.value.codigo == "ids_largos"
