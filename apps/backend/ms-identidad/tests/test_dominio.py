import pytest

from app.domain.errores import CredencialesInvalidas, CuentaInactiva, ReglaDeNegocioViolada
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


def test_cuenta_inactiva_no_autentica():
    usuario = _usuario()
    usuario.estado = EstadoUsuario.INACTIVO

    with pytest.raises(CuentaInactiva):
        autenticar(usuario, "clave-secreta-123")


def test_perfil_se_guarda_en_la_cuenta():
    usuario = Usuario.crear(
        tipo_documento="CC",
        numero_documento="1012345678",
        email="Camila@Correo.com",
        password_plano="clave-secreta-123",
        nombre="Camila",
        apellidos="Restrepo",
    )
    usuario.actualizar_perfil(nombre="Ana", apellidos="Lopez")

    assert (usuario.nombre, usuario.apellidos, usuario.email) == ("Ana", "Lopez", "camila@correo.com")


def test_inactivar_emite_evento_y_repetir_no_emite_nada():
    usuario = _usuario()

    evento = usuario.inactivar()

    assert usuario.estado is EstadoUsuario.INACTIVO
    assert evento is not None
    assert evento.tipo == "UsuarioInactivado"
    assert evento.agregado_id == usuario.id
    assert evento.payload["usuario_id"] == str(usuario.id)
    assert evento.payload["ocurrido_en"].endswith("Z")
    assert usuario.inactivar() is None


def test_activar_en_cuenta_activa_no_emite_y_desde_inactiva_si():
    usuario = _usuario()

    assert usuario.activar() is None

    usuario.inactivar()
    evento = usuario.activar()

    assert usuario.estado is EstadoUsuario.ACTIVO
    assert evento is not None
    assert evento.tipo == "UsuarioReactivado"
    assert set(evento.payload) == {"usuario_id", "ocurrido_en"}


def test_editar_recorta_y_pasa_el_correo_a_minusculas():
    usuario = _usuario()

    usuario.editar(nombre=" Ana ", apellidos=" Lopez ", email=" ANA@Correo.com ")

    assert (usuario.nombre, usuario.apellidos, usuario.email) == ("Ana", "Lopez", "ana@correo.com")
    usuario.editar(nombre="n" * 80, apellidos="a" * 80, email="ana@correo.com")
    assert len(usuario.nombre) == 80 and len(usuario.apellidos) == 80


@pytest.mark.parametrize(
    ("nombre", "apellidos", "email"),
    [
        ("", "Lopez", "ana@correo.com"),
        (" ", "Lopez", "ana@correo.com"),
        ("n" * 81, "Lopez", "ana@correo.com"),
        ("Ana", "", "ana@correo.com"),
        ("Ana", "a" * 81, "ana@correo.com"),
        ("Ana", "Lopez", "no-es-correo"),
        ("Ana", "Lopez", "ana@correo"),
    ],
)
def test_editar_rechaza_nombre_apellidos_o_correo_invalidos(nombre, apellidos, email):
    usuario = _usuario()

    with pytest.raises(ReglaDeNegocioViolada):
        usuario.editar(nombre=nombre, apellidos=apellidos, email=email)


def test_verificar_password_con_hash_corrupto_no_lanza_excepcion():
    usuario = _usuario("clave-secreta-123")
    usuario.password_hash = "no-es-un-hash-bcrypt-valido"

    assert usuario.verificar_password("clave-secreta-123") is False
