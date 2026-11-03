from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.avisos import DetalleSiniestro, ResultadoPago
from app.domain.aviso import Adjunto, PagoSiniestro, ParametroRamo, clave_pago
from app.domain.modelos import Geo, SnapshotPoliza

from .schemas import SiniestroSalida


class PolizaAvisoEntrada(BaseModel):
    """Foto de la póliza que el BFF resolvió contra ms-polizas (ver SnapshotPoliza)."""

    poliza_id: UUID
    numero: str = Field(min_length=1, max_length=60)
    ramo: str = Field(min_length=1, max_length=80)
    estado: str = Field(min_length=1, max_length=40)
    inicio_vigencia: date
    fin_vigencia: date
    suma_asegurada: Decimal | None = Field(default=None, max_digits=14, decimal_places=2, gt=0)

    def a_dominio(self) -> SnapshotPoliza:
        return SnapshotPoliza(
            poliza_id=self.poliza_id,
            numero=self.numero,
            ramo=self.ramo,
            estado=self.estado,
            inicio_vigencia=self.inicio_vigencia,
            fin_vigencia=self.fin_vigencia,
            suma_asegurada=self.suma_asegurada,
        )


class GeoEntrada(BaseModel):
    """Mismo concepto que Geo{lat,lng,precisionM} del contrato móvil (Contratos-BFF HU-129)."""

    lat: Decimal = Field(ge=-90, le=90)
    lng: Decimal = Field(ge=-180, le=180)
    precision_m: Decimal | None = Field(default=None, ge=0)

    def a_dominio(self) -> Geo:
        return Geo(
            self.lat.quantize(Decimal("0.000001")),
            self.lng.quantize(Decimal("0.000001")),
            self.precision_m.quantize(Decimal("0.01")) if self.precision_m is not None else None,
        )


class AvisoEntrada(BaseModel):
    """Parte `datos` (JSON) del multipart de POST /v1/siniestros. Los archivos viajan en la
    parte `archivos`; `tipos_adjuntos` (opcional) dice el tipo de cada archivo, en orden."""

    usuario_id: UUID
    canal: Literal["web", "movil"]
    poliza: PolizaAvisoEntrada
    fecha_hecho: date
    descripcion: str = Field(min_length=1, max_length=1000)
    geo: GeoEntrada | None = None
    tipos_adjuntos: list[str] = Field(default_factory=list)


class AdjuntoSalida(BaseModel):
    id: UUID
    tipo: str
    nombre: str
    content_type: str
    tamano_bytes: int
    sha256: str
    cargado_en: datetime
    url: str
    url_expira_segundos: int

    @classmethod
    def desde(cls, adjunto: Adjunto, url: str, expira: int) -> AdjuntoSalida:
        return cls(
            id=adjunto.id,
            tipo=adjunto.tipo,
            nombre=adjunto.nombre_original,
            content_type=adjunto.content_type,
            tamano_bytes=adjunto.tamano_bytes,
            sha256=adjunto.sha256,
            cargado_en=adjunto.cargado_en,
            url=url,
            url_expira_segundos=expira,
        )


class ReglaSalida(BaseModel):
    codigo: str
    cumple: bool
    detalle: str


class DecisionSalida(BaseModel):
    origen: str
    actor: str
    resultado: str
    motivo: str | None
    reglas: list[ReglaSalida]
    decidida_en: datetime


class PagoSalidaAviso(BaseModel):
    clave_idempotencia: str
    comprobante: str
    monto: Decimal
    origen: str
    autorizado_por: str
    pagado_en: datetime

    @classmethod
    def desde(cls, pago: PagoSiniestro) -> PagoSalidaAviso:
        return cls(
            clave_idempotencia=pago.clave_idempotencia,
            comprobante=pago.comprobante,
            monto=pago.monto,
            origen=pago.origen.value,
            autorizado_por=pago.autorizado_por,
            pagado_en=pago.pagado_en,
        )


class IntentoPagoSalida(BaseModel):
    resultado: str
    clave_idempotencia: str
    comprobante_devuelto: str
    actor: str
    ocurrido_en: datetime


class DetalleSalida(BaseModel):
    siniestro: SiniestroSalida
    # Clave determinista del desembolso: la pantalla de pago la muestra ANTES de pagar (HU-29).
    clave_pago: str
    adjuntos: list[AdjuntoSalida]
    decisiones: list[DecisionSalida]
    pago: PagoSalidaAviso | None
    intentos_pago: list[IntentoPagoSalida]

    @classmethod
    async def desde(cls, detalle: DetalleSiniestro, almacen, expira: int) -> DetalleSalida:
        adjuntos = [
            AdjuntoSalida.desde(a, await almacen.url_lectura(a.s3_key, expira), expira) for a in detalle.adjuntos
        ]
        return cls(
            siniestro=SiniestroSalida.desde(detalle.siniestro),
            clave_pago=clave_pago(detalle.siniestro.id),
            adjuntos=adjuntos,
            decisiones=[
                DecisionSalida(
                    origen=d.origen.value,
                    actor=d.actor,
                    resultado=d.resultado.value,
                    motivo=d.motivo,
                    reglas=[ReglaSalida(**r.como_dict()) for r in d.reglas],
                    decidida_en=d.decidida_en,
                )
                for d in detalle.decisiones
            ],
            pago=PagoSalidaAviso.desde(detalle.pago) if detalle.pago else None,
            intentos_pago=[
                IntentoPagoSalida(
                    resultado=i.resultado,
                    clave_idempotencia=i.clave_idempotencia,
                    comprobante_devuelto=i.comprobante_devuelto,
                    actor=i.actor,
                    ocurrido_en=i.ocurrido_en,
                )
                for i in detalle.intentos_pago
            ],
        )


class DecisionEntrada(BaseModel):
    resultado: Literal["aprobado", "rechazado"]
    motivo: str | None = Field(default=None, max_length=1000)
    actor: str = Field(min_length=1, max_length=120)


class PeritoEntrada(BaseModel):
    motivo: str | None = Field(default=None, max_length=1000)
    actor: str = Field(min_length=1, max_length=120)


class PagoEntrada(BaseModel):
    actor: str = Field(min_length=1, max_length=120)


class PagoRealizadoSalida(BaseModel):
    pago: PagoSalidaAviso
    reintento: bool
    detalle: DetalleSalida

    @classmethod
    async def desde(cls, resultado: ResultadoPago, almacen, expira: int) -> PagoRealizadoSalida:
        return cls(
            pago=PagoSalidaAviso.desde(resultado.pago),
            reintento=resultado.reintento,
            detalle=await DetalleSalida.desde(resultado.detalle, almacen, expira),
        )


class EvaluacionPendientesSalida(BaseModel):
    procesados: int


class ParametroRamoSalida(BaseModel):
    ramo: str
    reserva_base: Decimal
    umbral_automatico: Decimal
    ventana_duplicado_dias: int

    @classmethod
    def desde(cls, p: ParametroRamo) -> ParametroRamoSalida:
        return cls(
            ramo=p.ramo,
            reserva_base=p.reserva_base,
            umbral_automatico=p.umbral_automatico,
            ventana_duplicado_dias=p.ventana_duplicado_dias,
        )
