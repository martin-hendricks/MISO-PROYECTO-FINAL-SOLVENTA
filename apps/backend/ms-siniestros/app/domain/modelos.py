from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import EventoParametricoInvalido, ReglaDeNegocioViolada, TransicionInvalida


class EstadoSiniestro(StrEnum):
    """Modelo único de estados (HU-30): todos los canales (cola del operador, decisión,
    pago, lista del cliente) leen de aquí. No hay un modelo de estados paralelo."""

    RECIBIDO = "recibido"
    EN_EVALUACION = "en_evaluacion"
    DECIDIDO = "decidido"
    ENRUTADO = "enrutado"
    PAGADO = "pagado"


# Transiciones válidas explícitas (HU-30): solo hacia adelante, nunca se retrocede a
# RECIBIDO y no se puede saltar directo a PAGADO sin pasar por DECIDIDO.
_TRANSICIONES_VALIDAS: dict[EstadoSiniestro, frozenset[EstadoSiniestro]] = {
    EstadoSiniestro.RECIBIDO: frozenset({EstadoSiniestro.EN_EVALUACION}),
    EstadoSiniestro.EN_EVALUACION: frozenset({EstadoSiniestro.DECIDIDO}),
    EstadoSiniestro.DECIDIDO: frozenset({EstadoSiniestro.ENRUTADO}),
    EstadoSiniestro.ENRUTADO: frozenset({EstadoSiniestro.PAGADO}),
    EstadoSiniestro.PAGADO: frozenset(),
}


@dataclass(frozen=True)
class TransicionEstado:
    """Un cambio de estado con marca de tiempo y origen (HU-30): traza reconstruible."""

    estado: EstadoSiniestro
    ocurrido_en: datetime
    origen: str


@dataclass
class Siniestro:
    """Agregado raíz de siniestro. Es la fuente única de estado que consumirán otras HU
    (cola del operador, decisión, pago, lista del cliente); aquí solo se modela el
    agregado y sus transiciones de forma reutilizable, sin esas HU futuras."""

    id: UUID
    evento_id: str
    estado: EstadoSiniestro
    historial: list[TransicionEstado]
    creado_en: datetime
    # HU-61 (back-office): permite a ms-polizas/bff-web consultar si una
    # póliza tiene siniestros abiertos antes de cancelar. Opcional porque el
    # origen del evento paramétrico no siempre lo conoce (stub de ingesta).
    poliza_id: UUID | None = None

    @classmethod
    def recibir(cls, evento_id: str, origen: str, poliza_id: UUID | None = None) -> Siniestro:
        ahora = datetime.now(UTC)
        return cls(
            id=uuid4(),
            evento_id=evento_id,
            estado=EstadoSiniestro.RECIBIDO,
            historial=[TransicionEstado(EstadoSiniestro.RECIBIDO, ahora, origen)],
            creado_en=ahora,
            poliza_id=poliza_id,
        )

    def cambiar_estado(self, nuevo_estado: EstadoSiniestro, origen: str) -> None:
        """Valida la transición explícitamente; si es inválida lanza TransicionInvalida y
        el siniestro NO queda en estado intermedio (no se muta nada antes de validar)."""
        permitidos = _TRANSICIONES_VALIDAS.get(self.estado, frozenset())
        if nuevo_estado not in permitidos:
            raise TransicionInvalida(self.estado.value, nuevo_estado.value)
        self.estado = nuevo_estado
        self.historial.append(TransicionEstado(nuevo_estado, datetime.now(UTC), origen))


@dataclass
class EventoParametrico:
    """Evento simulado del stub (HU-32): identificador + un único valor comparable. El
    esquema es propio de Solventa, no el del proveedor real (vuelos/clima)."""

    evento_id: str
    valor: Decimal
    recibido_en: datetime

    @classmethod
    def recibir(cls, evento_id: str, valor: Decimal) -> EventoParametrico:
        if not evento_id or not evento_id.strip():
            raise EventoParametricoInvalido("evento_sin_id", "El evento paramétrico requiere un identificador")
        try:
            valor_decimal = Decimal(valor)
        except Exception as exc:
            raise EventoParametricoInvalido(
                "evento_valor_invalido", "El valor comparable del evento debe ser numérico"
            ) from exc
        return cls(evento_id=evento_id.strip(), valor=valor_decimal, recibido_en=datetime.now(UTC))


@dataclass
class EvaluacionUmbral:
    """Resultado persistido de comparar el valor del evento contra el umbral 'de la
    póliza' (HU-33). El umbral y la vigencia viajan en la solicitud de evaluación: este
    servicio NO llama por red a ms-polizas (ver decisión documentada en el README)."""

    id: UUID
    evento_id: str
    umbral: Decimal
    valor: Decimal
    poliza_vigente: bool
    decision: bool
    motivo: str
    evaluada_en: datetime

    @classmethod
    def evaluar(cls, evento: EventoParametrico, umbral: Decimal, poliza_vigente: bool) -> EvaluacionUmbral:
        """Determinista: mismo evento + mismo umbral + misma vigencia -> misma decisión."""
        if not poliza_vigente:
            return cls(
                id=uuid4(),
                evento_id=evento.evento_id,
                umbral=umbral,
                valor=evento.valor,
                poliza_vigente=False,
                decision=False,
                motivo="poliza_no_vigente",
                evaluada_en=datetime.now(UTC),
            )
        cumple = evento.valor >= umbral
        return cls(
            id=uuid4(),
            evento_id=evento.evento_id,
            umbral=umbral,
            valor=evento.valor,
            poliza_vigente=True,
            decision=cumple,
            motivo="umbral_cumplido" if cumple else "umbral_no_alcanzado",
            evaluada_en=datetime.now(UTC),
        )


@dataclass
class PagoParametrico:
    """Desembolso simulado (HU-34), disparado sin intervención humana cuando la
    evaluación determina que el umbral se cumple."""

    id: UUID
    evento_id: str
    siniestro_id: UUID
    monto: Decimal
    pagado_en: datetime

    @classmethod
    def disparar(cls, evaluacion: EvaluacionUmbral, siniestro_id: UUID, monto: Decimal) -> PagoParametrico:
        if not evaluacion.decision:
            raise ReglaDeNegocioViolada(
                "umbral_no_cumplido", "No se puede disparar un pago cuando el umbral no se cumplió"
            )
        if monto <= 0:
            raise ReglaDeNegocioViolada("monto_no_positivo", "El monto del pago debe ser mayor que cero")
        return cls(
            id=uuid4(),
            evento_id=evaluacion.evento_id,
            siniestro_id=siniestro_id,
            monto=monto,
            pagado_en=datetime.now(UTC),
        )


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    agregado_id: UUID
    payload: dict
    id: UUID = field(default_factory=uuid4)


def evento_parametrico_recibido(evento: EventoParametrico, siniestro: Siniestro) -> EventoDominio:
    return EventoDominio(
        tipo="EventoParametricoRecibido",
        agregado_id=siniestro.id,
        payload={"evento_id": evento.evento_id, "valor": str(evento.valor), "siniestro_id": str(siniestro.id)},
    )


def siniestro_cambio_estado(siniestro: Siniestro, transicion: TransicionEstado) -> EventoDominio:
    return EventoDominio(
        tipo="SiniestroCambioEstado",
        agregado_id=siniestro.id,
        payload={
            "siniestro_id": str(siniestro.id),
            "estado": transicion.estado.value,
            "origen": transicion.origen,
            "ocurrido_en": transicion.ocurrido_en.isoformat(),
        },
    )


def umbral_evaluado(evaluacion: EvaluacionUmbral, siniestro: Siniestro) -> EventoDominio:
    return EventoDominio(
        tipo="UmbralEvaluado",
        agregado_id=siniestro.id,
        payload={
            "evento_id": evaluacion.evento_id,
            "umbral": str(evaluacion.umbral),
            "valor": str(evaluacion.valor),
            "decision": evaluacion.decision,
            "motivo": evaluacion.motivo,
        },
    )


def pago_parametrico_disparado(pago: PagoParametrico) -> EventoDominio:
    return EventoDominio(
        tipo="PagoParametricoDisparado",
        agregado_id=pago.siniestro_id,
        payload={"evento_id": pago.evento_id, "monto": str(pago.monto), "siniestro_id": str(pago.siniestro_id)},
    )
