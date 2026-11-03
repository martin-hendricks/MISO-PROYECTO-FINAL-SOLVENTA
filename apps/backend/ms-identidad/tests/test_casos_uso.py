import pytest

from app.application import casos_uso
from app.domain.errores import CredencialesInvalidas, CuentaDuplicada, DependenciaNoDisponible, IdentidadNoVerificada
from app.infrastructure.kyc import VerificadorKYCStub


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
