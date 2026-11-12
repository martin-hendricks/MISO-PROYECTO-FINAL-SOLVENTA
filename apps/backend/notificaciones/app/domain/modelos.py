from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada, TransicionInvalida


class EstadoNotificacion(StrEnum):
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    FALLIDA = "fallida"
    LEIDA = "leida"


class CanalNotificacion(StrEnum):
    PUSH = "push"
    EMAIL = "email"


PLATAFORMAS = frozenset({"android", "ios"})


@dataclass
class Notificacion:
    notificacion_id: UUID
    usuario_id: UUID
    evento_origen_id: UUID | None
    canal: str
    tipo: str
    titulo: str
    cuerpo: str
    destino: str | None
    estado: str
    creada_en: datetime
    enviada_en: datetime | None = None
    leida_en: datetime | None = None
    proveedor_id: str | None = None

    @classmethod
    def crear(
        cls,
        usuario_id: UUID,
        evento_origen_id: UUID | None,
        canal: str,
        tipo: str,
        titulo: str,
        cuerpo: str,
        destino: str | None = None,
        ahora: datetime | None = None,
    ) -> Notificacion:
        try:
            canal_normalizado = CanalNotificacion((canal or "").strip().lower()).value
        except ValueError as exc:
            raise ReglaDeNegocioViolada("canal_invalido", f"Canal '{canal}' no soportado") from exc
        if not tipo.strip():
            raise ReglaDeNegocioViolada("tipo_vacio", "El tipo de notificación es obligatorio")
        if not titulo.strip():
            raise ReglaDeNegocioViolada("titulo_vacio", "El título de la notificación es obligatorio")
        if not cuerpo.strip():
            raise ReglaDeNegocioViolada("cuerpo_vacio", "El cuerpo de la notificación es obligatorio")
        return cls(
            notificacion_id=uuid4(),
            usuario_id=usuario_id,
            evento_origen_id=evento_origen_id,
            canal=canal_normalizado,
            tipo=tipo.strip(),
            titulo=titulo.strip(),
            cuerpo=cuerpo.strip(),
            destino=destino.strip() if destino and destino.strip() else None,
            estado=EstadoNotificacion.PENDIENTE.value,
            creada_en=ahora or datetime.now(UTC),
        )

    def marcar_enviada(self, proveedor_id: str | None = None, ahora: datetime | None = None) -> None:
        if self.estado == EstadoNotificacion.LEIDA:
            raise TransicionInvalida(self.estado, EstadoNotificacion.ENVIADA)
        if self.estado == EstadoNotificacion.ENVIADA:
            return
        self.estado = EstadoNotificacion.ENVIADA.value
        self.enviada_en = ahora or datetime.now(UTC)
        self.proveedor_id = proveedor_id

    def marcar_fallida(self) -> None:
        if self.estado in (EstadoNotificacion.ENVIADA, EstadoNotificacion.LEIDA):
            raise TransicionInvalida(self.estado, EstadoNotificacion.FALLIDA)
        self.estado = EstadoNotificacion.FALLIDA.value

    def marcar_leida(self, ahora: datetime | None = None) -> None:
        """Idempotente: volver a marcarla leída no cambia la fecha original."""
        if self.estado == EstadoNotificacion.LEIDA:
            return
        self.estado = EstadoNotificacion.LEIDA.value
        self.leida_en = ahora or datetime.now(UTC)


@dataclass
class DispositivoPush:
    dispositivo_id: UUID
    usuario_id: UUID
    plataforma: str
    token: str
    activo: bool
    creado_en: datetime
    actualizado_en: datetime

    @classmethod
    def registrar(
        cls,
        usuario_id: UUID,
        plataforma: str,
        token: str,
        ahora: datetime | None = None,
    ) -> DispositivoPush:
        plataforma_normalizada = (plataforma or "").strip().lower()
        if plataforma_normalizada not in PLATAFORMAS:
            raise ReglaDeNegocioViolada(
                "plataforma_invalida",
                f"Plataforma '{plataforma}' no soportada; use android o ios",
            )
        token_normalizado = (token or "").strip()
        if not token_normalizado:
            raise ReglaDeNegocioViolada("token_vacio", "El token del dispositivo es obligatorio")
        momento = ahora or datetime.now(UTC)
        return cls(
            dispositivo_id=uuid4(),
            usuario_id=usuario_id,
            plataforma=plataforma_normalizada,
            token=token_normalizado,
            activo=True,
            creado_en=momento,
            actualizado_en=momento,
        )

    def activar(self, ahora: datetime | None = None) -> None:
        self.activo = True
        self.actualizado_en = ahora or datetime.now(UTC)

    def desactivar(self, ahora: datetime | None = None) -> None:
        self.activo = False
        self.actualizado_en = ahora or datetime.now(UTC)
