import jwt
import pytest

from app.seguridad import TokenInvalido, ValidadorJWT

from .emisor import EmisorDePrueba


@pytest.fixture(scope="module")
def emisor() -> EmisorDePrueba:
    return EmisorDePrueba()


@pytest.fixture(scope="module")
def validador(emisor: EmisorDePrueba) -> ValidadorJWT:
    return ValidadorJWT(emisor.llave_publica_pem, emisor.emisor, emisor.audiencia, margen_segundos=0)


def test_token_valido_devuelve_identidad(emisor, validador):
    identidad = validador.validar(emisor.emitir("USR-9", "asesor", alcances=("polizas:leer",)))

    assert identidad.sujeto == "USR-9"
    assert identidad.rol == "asesor"
    assert identidad.alcances == {"polizas:leer"}


def test_token_expirado_se_rechaza(emisor, validador):
    with pytest.raises(TokenInvalido) as exc:
        validador.validar(emisor.emitir(expira_en=-60))
    assert exc.value.motivo == "expirado"


def test_firma_de_otro_emisor_se_rechaza(validador):
    impostor = EmisorDePrueba()
    with pytest.raises(TokenInvalido) as exc:
        validador.validar(impostor.emitir())
    assert exc.value.motivo == "firma_invalida"


def test_hs256_con_la_llave_publica_como_secreto_se_rechaza(emisor, validador):
    falso = jwt.encode(
        {"sub": "x", "rol": "operador", "typ": "access", "iss": emisor.emisor, "aud": emisor.audiencia},
        "secreto-cualquiera-de-al-menos-32-bytes",
        algorithm="HS256",
    )
    with pytest.raises(TokenInvalido):
        validador.validar(falso)


@pytest.mark.parametrize(
    ("extra", "motivo"),
    [
        ({"aud": "otra-audiencia"}, "token_invalido"),
        ({"iss": "otro-emisor"}, "token_invalido"),
        ({"typ": "refresh"}, "tipo_no_access"),
    ],
)
def test_claims_incorrectos_se_rechazan(emisor, validador, extra, motivo):
    with pytest.raises(TokenInvalido) as exc:
        validador.validar(emisor.emitir(**extra))
    assert exc.value.motivo == motivo


def test_token_basura_se_rechaza(validador):
    with pytest.raises(TokenInvalido):
        validador.validar("no-es-un-jwt")


def test_llave_vacia_no_se_acepta():
    with pytest.raises(ValueError):
        ValidadorJWT("  ", "ms-identidad", "solventa")
