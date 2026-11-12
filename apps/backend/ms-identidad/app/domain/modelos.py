from __future__ import annotations

import re
from datetime import datetime, timezone

import bcrypt
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import CredencialesInvalidas, CuentaInactiva, ReglaDeNegocioViolada

# Costo de bcrypt: 12 es el default moderno recomendado (ni tan barato que
# sea crackeable en GPU, ni tan caro que convierta el login en un cuello de
# botella). No se expone como configuración: es una decisión de seguridad,
# no una perilla operativa.
_COSTO_BCRYPT = 12


class EstadoUsuario(StrEnum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    agregado_id: UUID
    payload: dict
    id: UUID = field(default_factory=uuid4)


def _texto_persona(valor: str, codigo: str, etiqueta: str) -> str:
    limpio = valor.strip()
    if not 1 <= len(limpio) <= 80:
        raise ReglaDeNegocioViolada(codigo, f"{etiqueta} debe tener entre 1 y 80 caracteres")
    return limpio


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
    """Identidad, credenciales y el perfil compartido por web y móvil.

    Nombre y apellidos viven en la misma cuenta: los dos canales leen y
    escriben este agregado. Biometría y permisos del dispositivo no entran
    aquí."""

    id: UUID
    tipo_documento: str
    numero_documento: str
    email: str
    password_hash: str
    estado: EstadoUsuario
    nombre: str = ""
    apellidos: str = ""
    ingresos_mensuales: Decimal | None = None
    gastos_mensuales: Decimal | None = None
    rol: str = "cliente"
    prueba_de_vida: str = "no"

    @classmethod
    def crear(
        cls,
        *,
        tipo_documento: str,
        numero_documento: str,
        email: str,
        password_plano: str,
        nombre: str = "",
        apellidos: str = "",
        ingresos_mensuales: Decimal | None = None,
        gastos_mensuales: Decimal | None = None,
        prueba_de_vida: str = "no",
    ) -> Usuario:
        if ingresos_mensuales is not None and ingresos_mensuales <= 0:
            raise ValueError("ingresos_mensuales debe ser mayor que cero")
        if gastos_mensuales is not None and gastos_mensuales < 0:
            raise ValueError("gastos_mensuales no puede ser negativo")
        if prueba_de_vida not in {"ok", "no"}:
            raise ReglaDeNegocioViolada("prueba_de_vida_invalida", "La prueba de vida es ok o no")
        return cls(
            id=uuid4(),
            tipo_documento=tipo_documento.strip().upper(),
            numero_documento=numero_documento.strip(),
            email=email.strip().lower(),
            password_hash=_hash_password(password_plano),
            estado=EstadoUsuario.ACTIVO,
            nombre=nombre.strip(),
            apellidos=apellidos.strip(),
            ingresos_mensuales=ingresos_mensuales,
            gastos_mensuales=gastos_mensuales,
            rol="cliente",
            prueba_de_vida=prueba_de_vida,
        )

    def registrar_prueba_de_vida(self, valor: str) -> None:
        if valor not in {"ok", "no"}:
            raise ReglaDeNegocioViolada("prueba_de_vida_invalida", "La prueba de vida es ok o no")
        self.prueba_de_vida = valor

    def actualizar_perfil(self, *, nombre: str, apellidos: str) -> None:
        self.nombre = nombre.strip()
        self.apellidos = apellidos.strip()

    def editar(self, *, nombre: str, apellidos: str, email: str) -> None:
        self.nombre = _texto_persona(nombre, "nombre_invalido", "El nombre")
        self.apellidos = _texto_persona(apellidos, "apellidos_invalidos", "Los apellidos")
        correo = email.strip().lower()
        if len(correo) > 254 or not _EMAIL.fullmatch(correo):
            raise ReglaDeNegocioViolada("email_invalido", "El correo no es válido")
        self.email = correo

    def inactivar(self) -> EventoDominio | None:
        if self.estado is EstadoUsuario.INACTIVO:
            return None
        self.estado = EstadoUsuario.INACTIVO
        return self._evento_estado("UsuarioInactivado")

    def activar(self) -> EventoDominio | None:
        if self.estado is EstadoUsuario.ACTIVO:
            return None
        self.estado = EstadoUsuario.ACTIVO
        return self._evento_estado("UsuarioReactivado")

    def _evento_estado(self, tipo: str) -> EventoDominio:
        ocurrido_en = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return EventoDominio(
            tipo=tipo,
            agregado_id=self.id,
            payload={"usuario_id": str(self.id), "ocurrido_en": ocurrido_en},
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
    if usuario.estado is not EstadoUsuario.ACTIVO:
        raise CuentaInactiva()
    return usuario


# Hash fijo precomputado (no corresponde a ninguna contraseña real) usado
# solo para igualar el costo de cómputo de bcrypt cuando el correo no existe.
_HASH_SENUELO = _hash_password(uuid4().hex)
