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
    poliza: str | None
    difusion_id: UUID | None
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
        poliza: str | None = None,
        difusion_id: UUID | None = None,
        ahora: datetime | None = None,
    ) -> Notificacion:
        try:
            canal_normalizado = CanalNotificacion((canal or "").strip().lower()).value
        except ValueError as exc:
            raise ReglaDeNegocioViolada("canal_invalido", f"Canal '{canal}' no soportado") from exc
        if not tipo.strip():
            raise ReglaDeNegocioViolada("tipo_vacio", "El tipo de notificación es obligatorio")
        titulo_limpio = titulo.strip()
        cuerpo_limpio = cuerpo.strip()
        if not titulo_limpio:
            raise ReglaDeNegocioViolada("titulo_vacio", "El título de la notificación es obligatorio")
        if not cuerpo_limpio:
            raise ReglaDeNegocioViolada("cuerpo_vacio", "El cuerpo de la notificación es obligatorio")
        if len(titulo_limpio) > 80:
            raise ReglaDeNegocioViolada("titulo_largo", "El título admite como máximo 80 caracteres")
        if len(cuerpo_limpio) > 240:
            raise ReglaDeNegocioViolada("cuerpo_largo", "El cuerpo admite como máximo 240 caracteres")
        poliza_limpia = poliza.strip() if poliza and poliza.strip() else None
        destino_limpio = destino.strip() if destino and destino.strip() else None
        if destino_limpio == "poliza-detalle" and poliza_limpia is None:
            destino_limpio = "inicio"
        return cls(
            notificacion_id=uuid4(),
            usuario_id=usuario_id,
            evento_origen_id=evento_origen_id,
            canal=canal_normalizado,
            tipo=tipo.strip(),
            titulo=titulo_limpio,
            cuerpo=cuerpo_limpio,
            destino=destino_limpio,
            poliza=poliza_limpia,
            difusion_id=difusion_id,
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


MAX_AUDIENCIA = 500


def resolver_audiencia(tipo: str, usuario_ids: list[UUID] | None) -> tuple[str, list[UUID]]:
    """Normaliza la audiencia de una difusión. `todos` ignora la lista."""
    tipo_limpio = (tipo or "").strip().lower()
    if tipo_limpio == "todos":
        return "todos", []
    if tipo_limpio != "usuarios":
        raise ReglaDeNegocioViolada("audiencia_invalida", "La audiencia debe ser todos o usuarios")
    vistos: list[UUID] = []
    for usuario_id in usuario_ids or []:
        if usuario_id not in vistos:
            vistos.append(usuario_id)
    if not vistos:
        raise ReglaDeNegocioViolada("audiencia_vacia", "La audiencia no puede estar vacía")
    if len(vistos) > MAX_AUDIENCIA:
        raise ReglaDeNegocioViolada(
            "audiencia_larga", f"La audiencia admite como máximo {MAX_AUDIENCIA} usuarios"
        )
    return "usuarios", vistos


@dataclass
class Difusion:
    difusion_id: UUID
    autor_id: UUID
    titulo: str
    cuerpo: str
    poliza: str | None
    audiencia: str
    destinatarios: int
    enviadas: int
    fallidas: int
    sin_dispositivo: int
    creada_en: datetime

    @classmethod
    def crear(
        cls,
        autor_id: UUID,
        titulo: str,
        cuerpo: str,
        audiencia: str,
        destinatarios: int,
        poliza: str | None = None,
        ahora: datetime | None = None,
    ) -> Difusion:
        # Reusa los topes de Notificacion sin persistir una fila.
        muestra = Notificacion.crear(
            usuario_id=autor_id,
            evento_origen_id=None,
            canal="push",
            tipo="mensaje_operador",
            titulo=titulo,
            cuerpo=cuerpo,
            destino="poliza-detalle" if poliza else "inicio",
            poliza=poliza,
        )
        return cls(
            difusion_id=uuid4(),
            autor_id=autor_id,
            titulo=muestra.titulo,
            cuerpo=muestra.cuerpo,
            poliza=muestra.poliza,
            audiencia=audiencia,
            destinatarios=destinatarios,
            enviadas=0,
            fallidas=0,
            sin_dispositivo=0,
            creada_en=ahora or datetime.now(UTC),
        )

    def registrar_totales(self, enviadas: int, fallidas: int, sin_dispositivo: int) -> None:
        if enviadas + fallidas + sin_dispositivo != self.destinatarios:
            raise ReglaDeNegocioViolada(
                "totales_inconsistentes",
                "enviadas, fallidas y sin dispositivo deben sumar los destinatarios",
            )
        self.enviadas = enviadas
        self.fallidas = fallidas
        self.sin_dispositivo = sin_dispositivo
