from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada

_DOS_DECIMALES = Decimal("0.01")


class OrigenAdaptador(StrEnum):
    OPEN_FINANCE = "open_finance"
    OPEN_DATA = "open_data"


@dataclass
class Consentimiento:
    """Consentimiento de PERFILAMIENTO (HU-53): distinto e independiente de cualquier
    otro consentimiento de datos general que exista en el resto de la plataforma (otra
    HU, otro microservicio). Se otorga y revoca únicamente dentro de ms-perfilamiento."""

    id: UUID
    cliente_id: str
    otorgado_en: datetime
    revocado_en: datetime | None

    @classmethod
    def otorgar(cls, cliente_id: str) -> Consentimiento:
        if not cliente_id.strip():
            raise ReglaDeNegocioViolada("cliente_id_vacio", "El cliente_id es obligatorio")
        return cls(id=uuid4(), cliente_id=cliente_id.strip(), otorgado_en=datetime.now(UTC), revocado_en=None)

    @property
    def vigente(self) -> bool:
        return self.revocado_en is None

    def revocar(self) -> None:
        if self.revocado_en is None:
            self.revocado_en = datetime.now(UTC)


class EstadoAdaptador(StrEnum):
    EXITO = "exito"
    DEGRADADO = "degradado"
    ERROR = "error"


@dataclass(frozen=True)
class AtributoPerfil:
    """Un atributo propio de Solventa devuelto por UN adaptador (HU-54). `valor` ya es
    el atributo inventado por Solventa (p.ej. "nivel_ingresos_estimado"), nunca el
    payload crudo del proveedor real. `degradado` indica si este atributo en particular
    vino del valor de respaldo (timeout o fallo del adaptador, HU-56)."""

    nombre: str
    valor: Decimal
    origen: OrigenAdaptador
    estado: EstadoAdaptador
    degradado: bool


@dataclass(frozen=True)
class Perfil:
    """El perfil lo arma Solventa combinando los atributos de los adaptadores (HU-55):
    no es un passthrough de ninguna respuesta de terceros."""

    cliente_id: str
    atributos: tuple[AtributoPerfil, ...]

    @classmethod
    def armar(cls, cliente_id: str, atributos: list[AtributoPerfil]) -> Perfil:
        return cls(cliente_id=cliente_id, atributos=tuple(atributos))

    def atributo(self, nombre: str) -> AtributoPerfil | None:
        return next((a for a in self.atributos if a.nombre == nombre), None)

    @property
    def degradado(self) -> bool:
        return any(a.degradado for a in self.atributos)


@dataclass(frozen=True)
class FactorInterno:
    """Factor en lenguaje de negocio que explica la oferta (HU-55): nunca el detalle
    crudo del proveedor, siempre un nombre de atributo propio de Solventa + el impacto
    cualitativo sobre el precio."""

    factor: str
    impacto: str
    peso: Decimal


def ajuste_por_factores(factores: tuple[FactorInterno, ...], atributos: tuple[AtributoPerfil, ...]) -> Decimal:
    """`1 + sum(peso_i * valor_i)`: el multiplicador que el perfil aplica sobre una
    tarifa base (HU-55). Se recalcula siempre desde los factores y el snapshot
    persistidos, así que es reconstruible sin guardar un dato aparte."""
    valores = {a.nombre: a.valor for a in atributos}
    return Decimal("1") + sum(
        (f.peso * valores[f.factor] for f in factores if f.factor in valores), Decimal("0")
    )


@dataclass(frozen=True)
class Oferta:
    """Precio + factores internos explicables, con snapshot completo de insumos para
    que la decisión sea 100% reconstruible aunque las reglas cambien después (HU-55)."""

    id: UUID
    cliente_id: str
    precio: Decimal
    moneda: str
    factores: tuple[FactorInterno, ...]
    degradado: bool
    snapshot_atributos: tuple[AtributoPerfil, ...]
    creado_en: datetime

    @classmethod
    def armar(
        cls,
        cliente_id: str,
        precio: Decimal,
        factores: list[FactorInterno],
        perfil: Perfil,
    ) -> Oferta:
        precio_redondeado = precio.quantize(_DOS_DECIMALES, rounding=ROUND_HALF_EVEN)
        if precio_redondeado <= 0:
            raise ReglaDeNegocioViolada("precio_no_positivo", "El precio de la oferta debe ser mayor que cero")
        return cls(
            id=uuid4(),
            cliente_id=cliente_id,
            precio=precio_redondeado,
            moneda="COP",
            factores=tuple(factores),
            degradado=perfil.degradado,
            snapshot_atributos=perfil.atributos,
            creado_en=datetime.now(UTC),
        )

    @property
    def factor_ajuste(self) -> Decimal:
        """Multiplicador del perfil sobre la tarifa base. Es lo que consume
        ms-cotizacion por IPerfilRiesgo para que la prima cotizada use este mismo
        perfil (una sola fuente de precio para vida crediticia)."""
        return ajuste_por_factores(self.factores, self.snapshot_atributos)


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    agregado_id: UUID
    payload: dict
    id: UUID = field(default_factory=uuid4)


def consentimiento_otorgado(consentimiento: Consentimiento) -> EventoDominio:
    return EventoDominio(
        tipo="ConsentimientoPerfilamientoOtorgado",
        agregado_id=consentimiento.id,
        payload={
            "id": str(consentimiento.id),
            "cliente_id": consentimiento.cliente_id,
            "otorgado_en": consentimiento.otorgado_en.isoformat(),
        },
    )


def consentimiento_revocado(consentimiento: Consentimiento) -> EventoDominio:
    return EventoDominio(
        tipo="ConsentimientoPerfilamientoRevocado",
        agregado_id=consentimiento.id,
        payload={
            "id": str(consentimiento.id),
            "cliente_id": consentimiento.cliente_id,
            "revocado_en": consentimiento.revocado_en.isoformat() if consentimiento.revocado_en else None,
        },
    )


def oferta_emitida(oferta: Oferta) -> EventoDominio:
    return EventoDominio(
        tipo="OfertaHipotecarioEmitida",
        agregado_id=oferta.id,
        payload={
            "id": str(oferta.id),
            "cliente_id": oferta.cliente_id,
            "precio": str(oferta.precio),
            "degradado": oferta.degradado,
        },
    )
