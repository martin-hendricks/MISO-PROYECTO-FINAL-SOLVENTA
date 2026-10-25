from __future__ import annotations

import bcrypt
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import CredencialesInvalidas

# Costo de bcrypt: 12 es el default moderno recomendado (ni tan barato que
# sea crackeable en GPU, ni tan caro que convierta el login en un cuello de
# botella). No se expone como configuración: es una decisión de seguridad,
# no una perilla operativa.
_COSTO_BCRYPT = 12


class EstadoUsuario(StrEnum):
    ACTIVO = "ACTIVO"
    # No hay flujo de bloqueo/inactivación en el alcance de hoy (SOLV-215 no
    # pide suspensión de cuentas), pero el campo existe en el schema oficial
    # y el dominio deja la puerta abierta para cuando exista esa HU.
    INACTIVO = "INACTIVO"


def _hash_password(password_plano: str) -> str:
    return bcrypt.hashpw(password_plano.encode("utf-8"), bcrypt.gensalt(_COSTO_BCRYPT)).decode("ascii")


def _verificar_password(password_plano: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password_plano.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        # Hash corrupto o en un formato que bcrypt no reconoce: nunca es una
        # coincidencia válida, pero tampoco debe tumbar el login con un 500.
        return False


@dataclass
class Usuario:
    """Identidad y credenciales. Nombre/apellidos NO se persisten aquí: el
    schema oficial (db/schema/01_ms_identidad.sql) no tiene esas columnas --
    hoy solo bff-web los recibe en el alta y los devuelve en la respuesta de
    registro sin guardarlos en ningún microservicio (ninguna tabla oficial
    del dominio los tiene todavía); ms-identidad es responsable únicamente
    de documento, correo y contraseña."""

    id: UUID
    tipo_documento: str
    numero_documento: str
    email: str
    password_hash: str
    estado: EstadoUsuario

    @classmethod
    def crear(
        cls,
        *,
        tipo_documento: str,
        numero_documento: str,
        email: str,
        password_plano: str,
    ) -> Usuario:
        return cls(
            id=uuid4(),
            tipo_documento=tipo_documento.strip().upper(),
            numero_documento=numero_documento.strip(),
            email=email.strip().lower(),
            password_hash=_hash_password(password_plano),
            estado=EstadoUsuario.ACTIVO,
        )

    def verificar_password(self, password_plano: str) -> bool:
        return _verificar_password(password_plano, self.password_hash)


def autenticar(usuario: Usuario | None, password_plano: str) -> Usuario:
    """Valida credenciales de forma indistinguible entre "no existe" y
    "contraseña incorrecta": ambos casos levantan el mismo error de dominio,
    con el mismo mensaje, y ambos ejecutan un hash de bcrypt (aunque sea
    contra un hash señuelo cuando el usuario no existe) para no delatar por
    temporización cuál de los dos casos ocurrió."""
    hash_a_verificar = usuario.password_hash if usuario is not None else _HASH_SENUELO
    coincide = _verificar_password(password_plano, hash_a_verificar)

    if usuario is None or not coincide:
        raise CredencialesInvalidas()
    return usuario


# Hash fijo precomputado (no corresponde a ninguna contraseña real) usado
# solo para igualar el costo de cómputo de bcrypt cuando el correo no existe.
_HASH_SENUELO = _hash_password(uuid4().hex)
