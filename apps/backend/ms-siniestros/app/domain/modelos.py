from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
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


class TipoSiniestro(StrEnum):
    PARAMETRICO = "parametrico"
    ASISTIDO = "asistido"


class ResultadoDecision(StrEnum):
    """Distingue aprobado de rechazado dentro del estado único DECIDIDO (HU-27)."""

    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


# Transiciones válidas explícitas (HU-30): solo hacia adelante, nunca se retrocede a
# RECIBIDO y no se puede saltar directo a PAGADO sin pasar por DECIDIDO.
# EN_EVALUACION -> ENRUTADO es el envío a perito (HU-28) de un caso que no es de bajo monto.
_TRANSICIONES_VALIDAS: dict[EstadoSiniestro, frozenset[EstadoSiniestro]] = {
    EstadoSiniestro.RECIBIDO: frozenset({EstadoSiniestro.EN_EVALUACION}),
    EstadoSiniestro.EN_EVALUACION: frozenset({EstadoSiniestro.DECIDIDO, EstadoSiniestro.ENRUTADO}),
    EstadoSiniestro.DECIDIDO: frozenset({EstadoSiniestro.ENRUTADO}),
    EstadoSiniestro.ENRUTADO: frozenset({EstadoSiniestro.PAGADO}),
    EstadoSiniestro.PAGADO: frozenset(),
}


def _transiciones_permitidas(
    estado: EstadoSiniestro, resultado: ResultadoDecision | None
) -> frozenset[EstadoSiniestro]:
    """La tabla base aplica igual a los paramétricos (resultado None). Si el caso ya tiene
    resultado: aprobado puede pasar de DECIDIDO a PAGADO (pago de bajo monto, HU-29) y
    rechazado es terminal (el cliente recibe el motivo, no hay continuación)."""
    permitidos = _TRANSICIONES_VALIDAS.get(estado, frozenset())
    if estado is EstadoSiniestro.DECIDIDO and resultado is ResultadoDecision.APROBADO:
        return permitidos | {EstadoSiniestro.PAGADO}
    if estado is EstadoSiniestro.DECIDIDO and resultado is ResultadoDecision.RECHAZADO:
        return frozenset()
    return permitidos


@dataclass(frozen=True)
class TransicionEstado:
    """Un cambio de estado con marca de tiempo y origen (HU-30): traza reconstruible."""

    estado: EstadoSiniestro
    ocurrido_en: datetime
    origen: str


@dataclass(frozen=True)
class Geo:
    """Coordenada del hecho: GPS del teléfono o ubicación del navegador. Opcional en el
    aviso: si el usuario la niega, el aviso sigue sin geoetiqueta (HU-24, HU-100)."""

    lat: Decimal
    lng: Decimal
    precision_m: Decimal | None = None

    def __post_init__(self) -> None:
        if not (Decimal(-90) <= self.lat <= Decimal(90)) or not (Decimal(-180) <= self.lng <= Decimal(180)):
            raise ReglaDeNegocioViolada("geo_invalida", "La coordenada está fuera de rango")


@dataclass(frozen=True)
class SnapshotPoliza:
    """Datos de la póliza tal como los resolvió el BFF contra ms-polizas al recibir el
    aviso. ms-siniestros no llama por red a ms-polizas (misma decisión que HU-33): la
    foto viaja en el aviso y queda persistida para que el motor evalúe después."""

    poliza_id: UUID
    numero: str
    ramo: str
    estado: str
    inicio_vigencia: date
    fin_vigencia: date
    suma_asegurada: Decimal | None = None

    @property
    def vigente(self) -> bool:
        return self.estado == "vigente"


@dataclass
class Siniestro:
    """Agregado raíz de siniestro: fuente única de estado para la cola del operador, la
    decisión, el pago y la lista del cliente (HU-30). Cubre los dos recorridos del PDF:
    el paramétrico (evento externo, HU-32..34) y el asistido (aviso del cliente, HU-157)."""

    id: UUID
    evento_id: str | None
    estado: EstadoSiniestro
    historial: list[TransicionEstado]
    creado_en: datetime
    # HU-61 (back-office): permite a ms-polizas/bff-web consultar si una
    # póliza tiene siniestros abiertos antes de cancelar. Opcional porque el
    # origen del evento paramétrico no siempre lo conoce (stub de ingesta).
    poliza_id: UUID | None = None
    tipo: TipoSiniestro = TipoSiniestro.PARAMETRICO
    # Número visible (SIN-1001). Lo asigna la base al insertar.
    numero: str | None = None
    usuario_id: UUID | None = None
    canal: str | None = None
    poliza: SnapshotPoliza | None = None
    fecha_hecho: date | None = None
    descripcion: str | None = None
    geo: Geo | None = None
    reserva: Decimal | None = None
    umbral_automatico: Decimal | None = None
    resultado: ResultadoDecision | None = None
    requiere_revision: bool = False
    motivo_revision: str | None = None
    clave_idempotencia: str | None = None

    @classmethod
    def recibir(
        cls,
        evento_id: str,
        origen: str,
        poliza_id: UUID | None = None,
        usuario_id: UUID | None = None,
    ) -> Siniestro:
        ahora = datetime.now(UTC)
        return cls(
            id=uuid4(),
            evento_id=evento_id,
            estado=EstadoSiniestro.RECIBIDO,
            historial=[TransicionEstado(EstadoSiniestro.RECIBIDO, ahora, origen)],
            creado_en=ahora,
            poliza_id=poliza_id,
            usuario_id=usuario_id,
        )

    @classmethod
    def avisar(
        cls,
        *,
        usuario_id: UUID,
        poliza: SnapshotPoliza,
        fecha_hecho: date,
        descripcion: str,
        canal: str,
        geo: Geo | None = None,
        clave_idempotencia: str | None = None,
    ) -> Siniestro:
        """Alta del aviso asistido (N5). Solo valida forma; la vigencia, el monto y el
        fraude los decide el motor de forma asíncrona, para que el aviso nunca se pierda
        por una regla de negocio (siempre queda RECIBIDO con su traza)."""
        descripcion = (descripcion or "").strip()
        if not descripcion:
            raise ReglaDeNegocioViolada("aviso_sin_descripcion", "El aviso requiere una descripción")
        if len(descripcion) > 1000:
            raise ReglaDeNegocioViolada("aviso_descripcion_larga", "La descripción admite hasta 1000 caracteres")
        if fecha_hecho > date.today():
            raise ReglaDeNegocioViolada("fecha_hecho_futura", "La fecha del evento no puede ser futura")
        ahora = datetime.now(UTC)
        return cls(
            id=uuid4(),
            evento_id=None,
            estado=EstadoSiniestro.RECIBIDO,
            historial=[TransicionEstado(EstadoSiniestro.RECIBIDO, ahora, f"cliente:{canal}")],
            creado_en=ahora,
            poliza_id=poliza.poliza_id,
            tipo=TipoSiniestro.ASISTIDO,
            usuario_id=usuario_id,
            canal=canal,
            poliza=poliza,
            fecha_hecho=fecha_hecho,
            descripcion=descripcion,
            geo=geo,
            clave_idempotencia=clave_idempotencia,
        )

    def cambiar_estado(self, nuevo_estado: EstadoSiniestro, origen: str) -> None:
        """Valida la transición explícitamente; si es inválida lanza TransicionInvalida y
        el siniestro NO queda en estado intermedio (no se muta nada antes de validar)."""
        permitidos = _transiciones_permitidas(self.estado, self.resultado)
        if nuevo_estado not in permitidos:
            raise TransicionInvalida(self.estado.value, nuevo_estado.value)
        self.estado = nuevo_estado
        self.historial.append(TransicionEstado(nuevo_estado, datetime.now(UTC), origen))

    def tomar_para_evaluacion(self, origen: str) -> None:
        self.cambiar_estado(EstadoSiniestro.EN_EVALUACION, origen)

    def retener_para_revision(self, motivo: str) -> None:
        """El motor no resolvió el caso (o lo marcó el antifraude): queda EN_EVALUACION y
        aparece en la cola del operador (EC-SEG-08)."""
        if self.estado is not EstadoSiniestro.EN_EVALUACION:
            raise TransicionInvalida(self.estado.value, "revision")
        self.requiere_revision = True
        self.motivo_revision = motivo

    def decidir(self, resultado: ResultadoDecision, motivo: str | None, origen: str) -> None:
        """HU-27: aprobar o rechazar. Rechazar exige motivo (el cliente lo recibe)."""
        if resultado is ResultadoDecision.RECHAZADO and not (motivo or "").strip():
            raise ReglaDeNegocioViolada("motivo_requerido", "El motivo es obligatorio para rechazar")
        if self.estado is not EstadoSiniestro.EN_EVALUACION:
            raise TransicionInvalida(self.estado.value, EstadoSiniestro.DECIDIDO.value)
        self.resultado = resultado
        self.cambiar_estado(EstadoSiniestro.DECIDIDO, origen)
        self.requiere_revision = False

    def enrutar_a_perito(self, origen: str) -> None:
        """HU-28: el caso complejo sale de la cola hacia un perito (sin red de talleres)."""
        self.cambiar_estado(EstadoSiniestro.ENRUTADO, origen)
        self.requiere_revision = False

    @property
    def bajo_monto(self) -> bool:
        return (
            self.reserva is not None
            and self.umbral_automatico is not None
            and self.reserva <= self.umbral_automatico
        )


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
