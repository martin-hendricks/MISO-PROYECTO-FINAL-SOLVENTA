from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada


class EstadoPoliza(StrEnum):
    VIGENTE = "VIGENTE"


@dataclass(frozen=True)
class Cobertura:
    nombre: str
    suma_asegurada: Decimal
    deducible: Decimal = Decimal("0")


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

    @classmethod
    def emitir(
        cls,
        oferta_id: UUID,
        usuario_id: UUID,
        numero: str,
        coberturas: list[Cobertura],
        hoy: date,
    ) -> Poliza:
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
        return cls(
            id=uuid4(),
            oferta_id=oferta_id,
            usuario_id=usuario_id,
            numero=numero,
            inicio_vigencia=hoy,
            fin_vigencia=_un_anio_despues(hoy),
            estado=EstadoPoliza.VIGENTE,
            coberturas=tuple(coberturas),
        )


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
