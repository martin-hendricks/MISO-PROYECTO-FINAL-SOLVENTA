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


@dataclass(frozen=True)
class Cobertura:
    nombre: str
    suma_asegurada: Decimal
    deducible: Decimal = Decimal("0")


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
    motivo_cancelacion: str | None = None
    cancelada_en: date | None = None
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
            firma_hash=firma_hash,
        )

    def _exigir_vigente(self) -> None:
        """Renovar y modificar no son transiciones de estado, pero sí exigen
        que la póliza esté VIGENTE hoy; se expresa como el mismo error
        tipificado de transición inválida (destino implícito: seguir VIGENTE)."""
        if self.estado is not EstadoPoliza.VIGENTE:
            raise TransicionInvalida(self.estado.value, EstadoPoliza.VIGENTE.value)

    def renovar(self, nueva_fin_vigencia: date) -> None:
        """HU-59: renovar no cambia el estado (sigue VIGENTE), solo extiende la
        vigencia. Una póliza cancelada no se puede renovar."""
        self._exigir_vigente()
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

    def cancelar(self, motivo: str, hoy: date) -> None:
        """HU-61: única transición de estado real. Es terminal: no se puede
        cancelar una póliza ya cancelada."""
        if not motivo or not motivo.strip():
            raise ReglaDeNegocioViolada("motivo_requerido", "La cancelación requiere un motivo")
        if EstadoPoliza.CANCELADA not in _TRANSICIONES_VALIDAS.get(self.estado, frozenset()):
            raise TransicionInvalida(self.estado.value, EstadoPoliza.CANCELADA.value)
        self.estado = EstadoPoliza.CANCELADA
        self.motivo_cancelacion = motivo.strip()
        self.cancelada_en = hoy


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
            "estado": poliza.estado.value,
        },
    )
