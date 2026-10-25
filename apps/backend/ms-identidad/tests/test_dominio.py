import pytest

from app.domain.errores import CredencialesInvalidas
from app.domain.modelos import EstadoUsuario, Usuario, autenticar


def _usuario(password: str = "clave-secreta-123") -> Usuario:
    return Usuario.crear(
        tipo_documento="CC",
        numero_documento="1012345678",
        email="Camila@Correo.com",
        password_plano=password,
    )


def test_crear_normaliza_email_a_minusculas_y_documento_a_mayusculas():
    usuario = _usuario()

    assert usuario.email == "camila@correo.com"
    assert usuario.tipo_documento == "CC"
    assert usuario.estado is EstadoUsuario.ACTIVO


def test_crear_nunca_persiste_la_password_en_texto_plano():
    usuario = _usuario("clave-secreta-123")

    assert usuario.password_hash != "clave-secreta-123"
    assert usuario.password_hash.startswith("$2b$")


def test_verificar_password_acepta_la_contrasena_correcta():
    usuario = _usuario("clave-secreta-123")

    assert usuario.verificar_password("clave-secreta-123") is True


def test_verificar_password_rechaza_la_contrasena_incorrecta():
    usuario = _usuario("clave-secreta-123")

    assert usuario.verificar_password("otra-clave") is False


def test_mismo_password_genera_hashes_distintos_por_el_salt():
    uno = _usuario("clave-secreta-123")
    dos = _usuario("clave-secreta-123")

    assert uno.password_hash != dos.password_hash


def test_autenticar_con_password_correcto_devuelve_el_usuario():
    usuario = _usuario("clave-secreta-123")

    assert autenticar(usuario, "clave-secreta-123") is usuario


def test_autenticar_con_password_incorrecto_es_credenciales_invalidas():
    usuario = _usuario("clave-secreta-123")

    with pytest.raises(CredencialesInvalidas):
        autenticar(usuario, "clave-incorrecta")


def test_autenticar_sin_usuario_es_credenciales_invalidas():
    with pytest.raises(CredencialesInvalidas):
        autenticar(None, "cualquier-clave")


def test_autenticar_usuario_inexistente_y_password_incorrecto_dan_el_mismo_error():
    """No se revela cuál de los dos casos ocurrió: mismo tipo de excepción,
    mismo código, mismo mensaje."""
    usuario = _usuario("clave-secreta-123")

    with pytest.raises(CredencialesInvalidas) as con_usuario:
        autenticar(usuario, "clave-incorrecta")

    with pytest.raises(CredencialesInvalidas) as sin_usuario:
        autenticar(None, "clave-incorrecta")

    assert con_usuario.value.codigo == sin_usuario.value.codigo
    assert con_usuario.value.mensaje == sin_usuario.value.mensaje


def test_verificar_password_con_hash_corrupto_no_lanza_excepcion():
    usuario = _usuario("clave-secreta-123")
    usuario.password_hash = "no-es-un-hash-bcrypt-valido"

    assert usuario.verificar_password("clave-secreta-123") is False
