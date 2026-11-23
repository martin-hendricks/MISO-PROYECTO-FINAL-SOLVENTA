"""Entidades del siniestro asistido (HU-157): evidencia, decisión auditada, parametría por
ramo y pago de bajo monto. Viven junto al agregado Siniestro de modelos.py."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada
from .modelos import EventoDominio, Siniestro

# Evidencia (N6). Web acepta PNG/JPG/PDF (Figma evidencia-siniestro); el móvil suma video.
TIPOS_CONTENIDO_PERMITIDOS = frozenset({"image/png", "image/jpeg", "application/pdf", "video/mp4"})
TIPOS_ADJUNTO = frozenset({"foto", "video", "recibo", "soporte", "documento"})
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024
MAXIMO_ADJUNTOS = 5


class OrigenDecision(StrEnum):
    MOTOR = "motor"
    OPERADOR = "operador"


class ResultadoAuditado(StrEnum):
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    REVISION = "revision"
    ENRUTADO = "enrutado"


@dataclass(frozen=True)
class ArchivoEvidencia:
    """Archivo tal como llega del canal, antes de guardarse."""

    nombre: str
    content_type: str
    contenido: bytes
    tipo: str = "documento"


@dataclass(frozen=True)
class Adjunto:
    id: UUID
    siniestro_id: UUID
    usuario_id: UUID
    tipo: str
    nombre_original: str
    content_type: str
    tamano_bytes: int
    sha256: str
    s3_bucket: str
    s3_key: str
    cargado_en: datetime

    @classmethod
    def desde_archivo(cls, archivo: ArchivoEvidencia, siniestro: Siniestro, bucket: str) -> Adjunto:
        nombre = (archivo.nombre or "").strip() or "evidencia"
        if archivo.content_type not in TIPOS_CONTENIDO_PERMITIDOS:
            raise ReglaDeNegocioViolada(
                "evidencia_tipo_no_permitido", "La evidencia debe ser PNG, JPG, PDF o MP4"
            )
        tamano = len(archivo.contenido)
        if tamano == 0:
            raise ReglaDeNegocioViolada("evidencia_vacia", f"El archivo {nombre} está vacío")
        if tamano > TAMANO_MAXIMO_BYTES:
            raise ReglaDeNegocioViolada("evidencia_muy_grande", "Cada archivo admite hasta 10 MB")
        tipo = archivo.tipo if archivo.tipo in TIPOS_ADJUNTO else "documento"
        adjunto_id = uuid4()
        return cls(
            id=adjunto_id,
            siniestro_id=siniestro.id,
            usuario_id=siniestro.usuario_id,
            tipo=tipo,
            nombre_original=nombre[:255],
            content_type=archivo.content_type,
            tamano_bytes=tamano,
            sha256=hashlib.sha256(archivo.contenido).hexdigest(),
            s3_bucket=bucket,
            # La llave no usa el nombre del cliente: evita colisiones y caracteres raros.
            s3_key=f"siniestros/{siniestro.id}/{adjunto_id}",
            cargado_en=datetime.now(UTC),
        )


def validar_cantidad_adjuntos(archivos: list[ArchivoEvidencia]) -> None:
    if not archivos:
        raise ReglaDeNegocioViolada("aviso_sin_evidencia", "El aviso requiere al menos un archivo de evidencia")
    if len(archivos) > MAXIMO_ADJUNTOS:
        raise ReglaDeNegocioViolada("evidencia_excede_maximo", f"Se admiten hasta {MAXIMO_ADJUNTOS} archivos")


@dataclass(frozen=True)
class ParametroRamo:
    """Parametría del ramo: la reserva que se le asigna al aviso y el umbral bajo el cual
    el pago es automático (PDF §2.2 "pago de siniestros de bajo monto de forma automática")."""

    ramo: str
    reserva_base: Decimal
    umbral_automatico: Decimal
    ventana_duplicado_dias: int = 30

    def reserva_para(self, suma_asegurada: Decimal | None) -> Decimal:
        """La reserva nunca supera la suma asegurada de la póliza."""
        if suma_asegurada is not None and suma_asegurada > 0:
            return min(self.reserva_base, suma_asegurada)
        return self.reserva_base


@dataclass(frozen=True)
class ReglaEvaluada:
    codigo: str
    cumple: bool
    detalle: str

    def como_dict(self) -> dict:
        return {"codigo": self.codigo, "cumple": self.cumple, "detalle": self.detalle}


@dataclass(frozen=True)
class Decision:
    """Auditoría de una decisión (HU-27, N15): quién, cuándo, por qué y con qué reglas."""

    id: UUID
    siniestro_id: UUID
    origen: OrigenDecision
    actor: str
    resultado: ResultadoAuditado
    motivo: str | None
    reglas: list[ReglaEvaluada]
    decidida_en: datetime

    @classmethod
    def registrar(
        cls,
        siniestro_id: UUID,
        origen: OrigenDecision,
        actor: str,
        resultado: ResultadoAuditado,
        motivo: str | None,
        reglas: list[ReglaEvaluada] | None = None,
    ) -> Decision:
        return cls(
            id=uuid4(),
            siniestro_id=siniestro_id,
            origen=origen,
            actor=actor,
            resultado=resultado,
            motivo=(motivo or "").strip() or None,
            reglas=list(reglas or []),
            decidida_en=datetime.now(UTC),
        )


def clave_pago(siniestro_id: UUID) -> str:
    """Determinista: el mismo siniestro siempre produce la misma clave, así un reintento
    (doble clic, timeout del canal) no puede generar un segundo desembolso."""
    return f"idem-{siniestro_id.hex[:12]}"


@dataclass(frozen=True)
class PagoSiniestro:
    id: UUID
    siniestro_id: UUID
    clave_idempotencia: str
    comprobante: str
    monto: Decimal
    origen: OrigenDecision
    autorizado_por: str
    pagado_en: datetime

    @classmethod
    def autorizar(cls, siniestro: Siniestro, origen: OrigenDecision, actor: str) -> PagoSiniestro:
        if siniestro.resultado is None or siniestro.resultado.value != "aprobado":
            raise ReglaDeNegocioViolada("siniestro_no_aprobado", "Solo se paga un siniestro aprobado")
        if not siniestro.bajo_monto:
            raise ReglaDeNegocioViolada(
                "monto_sobre_umbral", "El monto supera el umbral automático; requiere otro flujo"
            )
        pago_id = uuid4()
        return cls(
            id=pago_id,
            siniestro_id=siniestro.id,
            clave_idempotencia=clave_pago(siniestro.id),
            comprobante=f"CMP-{pago_id.hex[:10].upper()}",
            monto=siniestro.reserva,
            origen=origen,
            autorizado_por=actor,
            pagado_en=datetime.now(UTC),
        )


@dataclass(frozen=True)
class IntentoPago:
    siniestro_id: UUID
    clave_idempotencia: str
    resultado: str  # ejecutado | reintento_idempotente
    comprobante_devuelto: str
    actor: str
    ocurrido_en: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)


# --- Eventos de dominio (outbox): los consumirá el push de estado (N7) cuando exista el
# publicador del outbox (N12). Aquí solo quedan registrados en la misma transacción.


def aviso_recibido(siniestro: Siniestro) -> EventoDominio:
    return EventoDominio(
        tipo="AvisoSiniestroRecibido",
        agregado_id=siniestro.id,
        payload={
            "siniestro_id": str(siniestro.id),
            "numero": siniestro.numero,
            "usuario_id": str(siniestro.usuario_id),
            "poliza_id": str(siniestro.poliza_id),
            "canal": siniestro.canal,
        },
    )


def decision_registrada(siniestro: Siniestro, decision: Decision) -> EventoDominio:
    return EventoDominio(
        tipo="SiniestroDecidido" if decision.resultado.value in ("aprobado", "rechazado") else "SiniestroRetenido",
        agregado_id=siniestro.id,
        payload={
            "siniestro_id": str(siniestro.id),
            "usuario_id": str(siniestro.usuario_id) if siniestro.usuario_id else None,
            "resultado": decision.resultado.value,
            "origen": decision.origen.value,
            "motivo": decision.motivo,
        },
    )


def pago_siniestro_realizado(pago: PagoSiniestro) -> EventoDominio:
    return EventoDominio(
        tipo="PagoSiniestroRealizado",
        agregado_id=pago.siniestro_id,
        payload={
            "siniestro_id": str(pago.siniestro_id),
            "monto": str(pago.monto),
            "comprobante": pago.comprobante,
            "clave_idempotencia": pago.clave_idempotencia,
        },
    )
