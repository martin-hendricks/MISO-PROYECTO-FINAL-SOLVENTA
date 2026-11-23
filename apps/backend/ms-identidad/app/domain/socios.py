from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import Conflicto, NoEncontrado


class EstadoSocio(StrEnum):
    ACTIVO = "activo"
    REVOCADO = "revocado"


def huella_de(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def _ahora() -> datetime:
    return datetime.now(UTC)


@dataclass
class CredencialSocio:
    credencial_id: UUID
    huella_sha256: str = field(repr=False)
    creada_en: datetime
    revocada_en: datetime | None = None

    @property
    def vigente(self) -> bool:
        return self.revocada_en is None


@dataclass
class Socio:
    socio_id: UUID
    nombre: str
    alcances: frozenset[str]
    estado: EstadoSocio
    creado_en: datetime
    credenciales: list[CredencialSocio] = field(default_factory=list)

    @classmethod
    def nuevo(
        cls, nombre: str, alcances: frozenset[str]
    ) -> tuple[Socio, CredencialSocio, str]:
        socio = cls(
            socio_id=uuid4(),
            nombre=nombre,
            alcances=alcances,
            estado=EstadoSocio.ACTIVO,
            creado_en=_ahora(),
        )
        credencial, api_key = socio.emitir_credencial()
        return socio, credencial, api_key

    def emitir_credencial(self) -> tuple[CredencialSocio, str]:
        if self.estado is EstadoSocio.REVOCADO:
            raise Conflicto("El socio está revocado")
        api_key = secrets.token_urlsafe(32)
        credencial = CredencialSocio(
            credencial_id=uuid4(), huella_sha256=huella_de(api_key), creada_en=_ahora()
        )
        self.credenciales.append(credencial)
        return credencial, api_key

    def revocar_credencial(self, credencial_id: UUID) -> None:
        credencial = next(
            (c for c in self.credenciales if c.credencial_id == credencial_id), None
        )
        if credencial is None:
            raise NoEncontrado("Credencial no encontrada")
        if credencial.vigente:
            credencial.revocada_en = _ahora()

    def revocar(self) -> None:
        if self.estado is EstadoSocio.REVOCADO:
            return
        self.estado = EstadoSocio.REVOCADO
        momento = _ahora()
        for credencial in self.credenciales:
            if credencial.vigente:
                credencial.revocada_en = momento

    def acepta(self, huella_sha256: str) -> bool:
        return self.estado is EstadoSocio.ACTIVO and any(
            c.vigente and secrets.compare_digest(c.huella_sha256, huella_sha256)
            for c in self.credenciales
        )
