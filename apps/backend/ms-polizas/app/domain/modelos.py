from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada, TransicionInvalida


class EstadoPoliza(StrEnum):
    VIGENTE = "VIGENTE"
    CANCELADA = "CANCELADA"


# Transiciones válidas explícitas (mismo patrón que ms-siniestros, HU-30):
# renovar y modificar coberturas NO son transiciones de estado (una póliza
# renovada/modificada sigue VIGENTE), solo cancelar lo es, y es terminal: una
# póliza cancelada no puede volver a VIGENTE ni cancelarse de nuevo.
_TRANSICIONES_VALIDAS: dict[EstadoPoliza, frozenset[EstadoPoliza]] = {
    EstadoPoliza.VIGENTE: frozenset({EstadoPoliza.CANCELADA}),
    EstadoPoliza.CANCELADA: frozenset(),
}

# HU-59: días tras una fin_vigencia vencida en los que renovar sigue
# permitido (el dominio no tiene un estado "VENCIDA" separado -- una póliza
# con fin_vigencia pasada sigue reportando VIGENTE hasta que algo la cambie,
# no hay job que la transicione sola).
VENTANA_GRACIA_DIAS = 30


@dataclass(frozen=True)
class Cobertura:
    nombre: str
    suma_asegurada: Decimal
    deducible: Decimal = Decimal("0")


@dataclass(frozen=True)
class Prima:
    """HU-59/61: valor de referencia para calcular la prima de renovación y
    la devolución al cancelar. L1 no tiene motor de tarificación: el valor se
    fija en emitir() como la suma de las sumas aseguradas de las coberturas,
    una heurística explícita, no un cálculo actuarial real."""

    valor: Decimal
    periodicidad: str = "ANUAL"


def _validar_coberturas(coberturas: list[Cobertura]) -> None:
    """Reglas de coberturas compartidas por emisión y modificación: al menos
    una cobertura, con nombre, suma asegurada positiva y deducible no negativo."""
    if not coberturas:
        raise ReglaDeNegocioViolada("sin_coberturas", "La póliza debe tener al menos una cobertura")
    for cobertura in coberturas:
        if not cobertura.nombre.strip():
            raise ReglaDeNegocioViolada("cobertura_sin_nombre", "Cada cobertura debe tener nombre")
        if cobertura.suma_asegurada <= 0:
            raise ReglaDeNegocioViolada(
                "suma_asegurada_no_positiva", "La suma asegurada debe ser mayor que cero"
            )
        if cobertura.deducible < 0:
            raise ReglaDeNegocioViolada("deducible_negativo", "El deducible no puede ser negativo")


def numero_de_poliza(anio: int, secuencia: int) -> str:
    """El número sale de una secuencia que nunca retrocede: no se reutiliza ni tras una cancelación (HU-61)."""
    return f"POL-{anio}-{secuencia:08d}"


def _un_anio_despues(inicio: date) -> date:
    try:
        siguiente = inicio.replace(year=inicio.year + 1)
    except ValueError:  # 29 de febrero
        siguiente = inicio.replace(year=inicio.year + 1, day=28)
    return siguiente - timedelta(days=1)


@dataclass
class Poliza:
    id: UUID
    oferta_id: UUID
    usuario_id: UUID
    numero: str
    inicio_vigencia: date
    fin_vigencia: date
    estado: EstadoPoliza
    coberturas: tuple[Cobertura, ...]
    prima: Prima
    motivo_cancelacion: str | None = None
    cancelada_en: date | None = None
    cancelada_por: str | None = None
    devolucion_estimada: Decimal | None = None
    firma_hash: str | None = None

    @classmethod
    def emitir(
        cls,
        oferta_id: UUID,
        usuario_id: UUID,
        numero: str,
        coberturas: list[Cobertura],
        hoy: date,
        firma_hash: str | None = None,
    ) -> Poliza:
        _validar_coberturas(coberturas)
        return cls(
            id=uuid4(),
            oferta_id=oferta_id,
            usuario_id=usuario_id,
            numero=numero,
            inicio_vigencia=hoy,
            fin_vigencia=_un_anio_despues(hoy),
            estado=EstadoPoliza.VIGENTE,
            coberturas=tuple(coberturas),
            prima=Prima(valor=sum((c.suma_asegurada for c in coberturas), Decimal("0"))),
            firma_hash=firma_hash,
        )

    def _exigir_vigente(self) -> None:
        """Modificar coberturas no es una transición de estado, pero sí exige
        que la póliza esté VIGENTE hoy (sin tolerancia de ventana de gracia,
        a diferencia de renovar -- ver _exigir_renovable); se expresa como el
        mismo error tipificado de transición inválida (destino implícito:
        seguir VIGENTE)."""
        if self.estado is not EstadoPoliza.VIGENTE:
            raise TransicionInvalida(self.estado.value, EstadoPoliza.VIGENTE.value)

    def en_ventana_gracia(self, hoy: date) -> bool:
        """HU-59: una póliza VIGENTE con fin_vigencia ya pasada sigue siendo
        renovable hasta VENTANA_GRACIA_DIAS después de vencer. No aplica a una
        póliza CANCELADA (cancelar es terminal, ver cancelar())."""
        return self.estado is EstadoPoliza.VIGENTE and hoy > self.fin_vigencia

    def renovable(self, hoy: date) -> bool:
        """Predicado sin lanzar excepción, usado por la API (PolizaSalida.renovable)
        para que el canal web deshabilite el CTA sin duplicar esta regla en el
        frontend. Misma condición que _exigir_renovable()."""
        if self.estado is not EstadoPoliza.VIGENTE:
            return False
        return not (hoy > self.fin_vigencia and (hoy - self.fin_vigencia).days > VENTANA_GRACIA_DIAS)

    def _exigir_renovable(self, hoy: date) -> None:
        """HU-59: renovar tolera fin_vigencia vencida dentro de la ventana de
        gracia; fuera de esa ventana (o si la póliza está CANCELADA) es la
        misma transición inválida que exige modificar_coberturas()."""
        if not self.renovable(hoy):
            raise TransicionInvalida(self.estado.value, EstadoPoliza.VIGENTE.value)

    def renovar(self, nueva_fin_vigencia: date, hoy: date) -> None:
        """HU-59: renovar no cambia el estado (sigue VIGENTE), solo extiende la
        vigencia. Una póliza cancelada no se puede renovar, y una vencida hace
        más que la ventana de gracia tampoco (ver _exigir_renovable)."""
        self._exigir_renovable(hoy)
        if nueva_fin_vigencia <= self.fin_vigencia:
            raise ReglaDeNegocioViolada(
                "nueva_vigencia_no_posterior", "La nueva fecha de fin de vigencia debe ser posterior a la actual"
            )
        self.fin_vigencia = nueva_fin_vigencia

    def modificar_coberturas(self, nuevas_coberturas: list[Cobertura]) -> None:
        """HU-60: modificar no cambia el estado (sigue VIGENTE), solo reemplaza
        el conjunto de coberturas. Reusa las mismas validaciones que emitir()."""
        self._exigir_vigente()
        _validar_coberturas(nuevas_coberturas)
        self.coberturas = tuple(nuevas_coberturas)

    def _devolucion_estimada(self, hoy: date) -> Decimal:
        """HU-61: prorrata simple de la prima sobre los días de vigencia que
        quedaban por correr; estimada, no un cálculo actuarial exacto (fuera
        de alcance en L1). Nunca negativa: una póliza ya vencida al cancelar
        no genera devolución."""
        dias_totales = (self.fin_vigencia - self.inicio_vigencia).days
        dias_restantes = (self.fin_vigencia - hoy).days
        if dias_totales <= 0 or dias_restantes <= 0:
            return Decimal("0")
        return (self.prima.valor * dias_restantes / dias_totales).quantize(Decimal("0.01"))

    def cancelar(self, motivo: str, hoy: date, cancelada_por: str) -> None:
        """HU-61: única transición de estado real. Es terminal: no se puede
        cancelar una póliza ya cancelada. Registra quién canceló (auditoría)
        y calcula la devolución estimada una sola vez."""
        if not motivo or not motivo.strip():
            raise ReglaDeNegocioViolada("motivo_requerido", "La cancelación requiere un motivo")
        if not cancelada_por or not cancelada_por.strip():
            raise ReglaDeNegocioViolada("operador_requerido", "La cancelación requiere el operador que la ejecuta")
        if EstadoPoliza.CANCELADA not in _TRANSICIONES_VALIDAS.get(self.estado, frozenset()):
            raise TransicionInvalida(self.estado.value, EstadoPoliza.CANCELADA.value)
        self.devolucion_estimada = self._devolucion_estimada(hoy)
        self.estado = EstadoPoliza.CANCELADA
        self.motivo_cancelacion = motivo.strip()
        self.cancelada_en = hoy
        self.cancelada_por = cancelada_por.strip()


@dataclass(frozen=True)
class ConstanciaFirma:
    """HU-17: registro auditable del resultado de la firma de una oferta,
    exitosa o no. Una oferta puede acumular varias (un rechazo y un reintento);
    la vigente es la más reciente."""

    oferta_id: UUID
    exitosa: bool
    firmada_en: datetime
    motivo: str | None = None
    firma_hash: str | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    agregado_id: UUID
    payload: dict
    id: UUID = field(default_factory=uuid4)


def poliza_emitida(poliza: Poliza) -> EventoDominio:
    return EventoDominio(
        tipo="PolizaEmitida",
        agregado_id=poliza.id,
        payload={
            "poliza_id": str(poliza.id),
            "oferta_id": str(poliza.oferta_id),
            "usuario_id": str(poliza.usuario_id),
            "numero": poliza.numero,
            "inicio_vigencia": poliza.inicio_vigencia.isoformat(),
            "fin_vigencia": poliza.fin_vigencia.isoformat(),
            "estado": poliza.estado.value,
        },
    )


def poliza_renovada(poliza: Poliza) -> EventoDominio:
    return EventoDominio(
        tipo="PolizaRenovada",
        agregado_id=poliza.id,
        payload={
            "poliza_id": str(poliza.id),
            "numero": poliza.numero,
            "fin_vigencia": poliza.fin_vigencia.isoformat(),
            "estado": poliza.estado.value,
        },
    )


def poliza_modificada(poliza: Poliza) -> EventoDominio:
    return EventoDominio(
        tipo="PolizaModificada",
        agregado_id=poliza.id,
        payload={
            "poliza_id": str(poliza.id),
            "numero": poliza.numero,
            "coberturas": [
                {"nombre": c.nombre, "suma_asegurada": str(c.suma_asegurada), "deducible": str(c.deducible)}
                for c in poliza.coberturas
            ],
            "estado": poliza.estado.value,
        },
    )


def poliza_cancelada(poliza: Poliza) -> EventoDominio:
    return EventoDominio(
        tipo="PolizaCancelada",
        agregado_id=poliza.id,
        payload={
            "poliza_id": str(poliza.id),
            "numero": poliza.numero,
            "motivo_cancelacion": poliza.motivo_cancelacion,
            "cancelada_en": poliza.cancelada_en.isoformat() if poliza.cancelada_en else None,
            "cancelada_por": poliza.cancelada_por,
            "devolucion_estimada": str(poliza.devolucion_estimada) if poliza.devolucion_estimada is not None else None,
            "estado": poliza.estado.value,
        },
    )
