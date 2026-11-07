from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    DateTime,
    FetchedValue,
    ForeignKey,
    MetaData,
    Numeric,
    String,
    and_,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import Settings
from app.domain.aviso import (
    Adjunto,
    Decision,
    IntentoPago,
    OrigenDecision,
    PagoSiniestro,
    ParametroRamo,
    ReglaEvaluada,
    ResultadoAuditado,
)
from app.domain.modelos import (
    EstadoSiniestro,
    EvaluacionUmbral,
    EventoDominio,
    EventoParametrico,
    Geo,
    PagoParametrico,
    ResultadoDecision,
    Siniestro,
    SnapshotPoliza,
    TipoSiniestro,
    TransicionEstado,
)
from app.ports.persistencia import ClaveIdempotenciaDuplicada, FiltroSiniestros

ESQUEMA = "ms_siniestros"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True), date: Date}


class SiniestroFila(Base):
    __tablename__ = "siniestro"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    evento_id: Mapped[str | None] = mapped_column(String, unique=True)
    estado: Mapped[str]
    creado_en: Mapped[datetime]
    poliza_id: Mapped[UUID | None]
    # numero lo asigna la base (DEFAULT 'SIN-' || nextval) y se lee de vuelta tras insertar.
    numero: Mapped[str | None] = mapped_column(String, server_default=FetchedValue())
    tipo: Mapped[str] = mapped_column(String, default=TipoSiniestro.PARAMETRICO.value)
    usuario_id: Mapped[UUID | None]
    canal: Mapped[str | None]
    ramo: Mapped[str | None]
    poliza_numero: Mapped[str | None]
    poliza_estado: Mapped[str | None]
    poliza_inicio_vigencia: Mapped[date | None]
    poliza_fin_vigencia: Mapped[date | None]
    suma_asegurada: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    fecha_hecho: Mapped[date | None]
    descripcion: Mapped[str | None]
    lugar: Mapped[str | None] = mapped_column(String(200))
    reserva: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    umbral_automatico: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    geo_lat: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    geo_lng: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    geo_precision_m: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    resultado: Mapped[str | None]
    requiere_revision: Mapped[bool] = mapped_column(default=False)
    motivo_revision: Mapped[str | None]
    clave_idempotencia: Mapped[str | None] = mapped_column(String, unique=True)


class TransicionEstadoFila(Base):
    __tablename__ = "siniestro_transicion"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    siniestro_id: Mapped[UUID] = mapped_column(ForeignKey(f"{ESQUEMA}.siniestro.id"))
    estado: Mapped[str]
    ocurrido_en: Mapped[datetime]
    origen: Mapped[str]


class EventoParametricoFila(Base):
    __tablename__ = "evento_parametrico"

    evento_id: Mapped[str] = mapped_column(String, primary_key=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    recibido_en: Mapped[datetime]


class EvaluacionUmbralFila(Base):
    __tablename__ = "evaluacion_umbral"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    evento_id: Mapped[str] = mapped_column(String, unique=True)
    umbral: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    poliza_vigente: Mapped[bool]
    decision: Mapped[bool]
    motivo: Mapped[str]
    evaluada_en: Mapped[datetime]


class PagoParametricoFila(Base):
    __tablename__ = "pago_parametrico"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    evento_id: Mapped[str] = mapped_column(String, unique=True)
    siniestro_id: Mapped[UUID]
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    pagado_en: Mapped[datetime]


class ParametroRamoFila(Base):
    __tablename__ = "parametro_ramo"

    ramo: Mapped[str] = mapped_column(String, primary_key=True)
    reserva_base: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    umbral_automatico: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    ventana_duplicado_dias: Mapped[int]
    actualizado_en: Mapped[datetime] = mapped_column(server_default=func.now())


class AdjuntoFila(Base):
    __tablename__ = "siniestro_adjunto"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    siniestro_id: Mapped[UUID] = mapped_column(ForeignKey(f"{ESQUEMA}.siniestro.id"))
    usuario_id: Mapped[UUID]
    tipo: Mapped[str]
    nombre_original: Mapped[str]
    content_type: Mapped[str]
    tamano_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str]
    s3_bucket: Mapped[str]
    s3_key: Mapped[str]
    cargado_en: Mapped[datetime]


class DecisionFila(Base):
    __tablename__ = "siniestro_decision"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    siniestro_id: Mapped[UUID] = mapped_column(ForeignKey(f"{ESQUEMA}.siniestro.id"))
    origen: Mapped[str]
    actor: Mapped[str]
    resultado: Mapped[str]
    motivo: Mapped[str | None]
    reglas: Mapped[list] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    decidida_en: Mapped[datetime]


class PagoSiniestroFila(Base):
    __tablename__ = "pago_siniestro"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    siniestro_id: Mapped[UUID] = mapped_column(ForeignKey(f"{ESQUEMA}.siniestro.id"), unique=True)
    clave_idempotencia: Mapped[str] = mapped_column(String, unique=True)
    comprobante: Mapped[str] = mapped_column(String, unique=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    origen: Mapped[str]
    autorizado_por: Mapped[str]
    pagado_en: Mapped[datetime]


class IntentoPagoFila(Base):
    __tablename__ = "pago_siniestro_intento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    siniestro_id: Mapped[UUID] = mapped_column(ForeignKey(f"{ESQUEMA}.siniestro.id"))
    clave_idempotencia: Mapped[str]
    resultado: Mapped[str]
    comprobante_devuelto: Mapped[str]
    actor: Mapped[str]
    ocurrido_en: Mapped[datetime]


class OutboxFila(Base):
    __tablename__ = "outbox_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str]
    agregado_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    publicado_en: Mapped[datetime | None]


def _siniestro_a_dominio(fila: SiniestroFila, transiciones: list[TransicionEstadoFila]) -> Siniestro:
    historial = [
        TransicionEstado(EstadoSiniestro(t.estado), t.ocurrido_en, t.origen)
        for t in sorted(transiciones, key=lambda t: t.ocurrido_en)
    ]
    poliza = None
    if fila.poliza_id and fila.poliza_numero and fila.poliza_inicio_vigencia and fila.poliza_fin_vigencia:
        poliza = SnapshotPoliza(
            poliza_id=fila.poliza_id,
            numero=fila.poliza_numero,
            ramo=fila.ramo or "",
            estado=fila.poliza_estado or "",
            inicio_vigencia=fila.poliza_inicio_vigencia,
            fin_vigencia=fila.poliza_fin_vigencia,
            suma_asegurada=fila.suma_asegurada,
        )
    geo = (
        Geo(fila.geo_lat, fila.geo_lng, fila.geo_precision_m)
        if fila.geo_lat is not None and fila.geo_lng is not None
        else None
    )
    return Siniestro(
        id=fila.id,
        evento_id=fila.evento_id,
        estado=EstadoSiniestro(fila.estado),
        historial=historial,
        creado_en=fila.creado_en,
        poliza_id=fila.poliza_id,
        tipo=TipoSiniestro(fila.tipo or TipoSiniestro.PARAMETRICO.value),
        numero=fila.numero,
        usuario_id=fila.usuario_id,
        canal=fila.canal,
        poliza=poliza,
        fecha_hecho=fila.fecha_hecho,
        descripcion=fila.descripcion,
        lugar=fila.lugar,
        geo=geo,
        reserva=fila.reserva,
        umbral_automatico=fila.umbral_automatico,
        resultado=ResultadoDecision(fila.resultado) if fila.resultado else None,
        requiere_revision=bool(fila.requiere_revision),
        motivo_revision=fila.motivo_revision,
        clave_idempotencia=fila.clave_idempotencia,
    )


def _copiar_a_fila(siniestro: Siniestro, fila: SiniestroFila) -> None:
    """Columnas mutables del agregado. id, creado_en y numero no cambian nunca."""
    fila.evento_id = siniestro.evento_id
    fila.estado = siniestro.estado.value
    fila.poliza_id = siniestro.poliza_id
    fila.tipo = siniestro.tipo.value
    fila.usuario_id = siniestro.usuario_id
    fila.canal = siniestro.canal
    poliza = siniestro.poliza
    fila.ramo = poliza.ramo if poliza else None
    fila.poliza_numero = poliza.numero if poliza else None
    fila.poliza_estado = poliza.estado if poliza else None
    fila.poliza_inicio_vigencia = poliza.inicio_vigencia if poliza else None
    fila.poliza_fin_vigencia = poliza.fin_vigencia if poliza else None
    fila.suma_asegurada = poliza.suma_asegurada if poliza else None
    fila.fecha_hecho = siniestro.fecha_hecho
    fila.descripcion = siniestro.descripcion
    fila.lugar = siniestro.lugar
    fila.reserva = siniestro.reserva
    fila.umbral_automatico = siniestro.umbral_automatico
    fila.geo_lat = siniestro.geo.lat if siniestro.geo else None
    fila.geo_lng = siniestro.geo.lng if siniestro.geo else None
    fila.geo_precision_m = siniestro.geo.precision_m if siniestro.geo else None
    fila.resultado = siniestro.resultado.value if siniestro.resultado else None
    fila.requiere_revision = siniestro.requiere_revision
    fila.motivo_revision = siniestro.motivo_revision
    fila.clave_idempotencia = siniestro.clave_idempotencia


def _evaluacion_a_dominio(fila: EvaluacionUmbralFila) -> EvaluacionUmbral:
    return EvaluacionUmbral(
        id=fila.id,
        evento_id=fila.evento_id,
        umbral=fila.umbral,
        valor=fila.valor,
        poliza_vigente=fila.poliza_vigente,
        decision=fila.decision,
        motivo=fila.motivo,
        evaluada_en=fila.evaluada_en,
    )


def _pago_a_dominio(fila: PagoParametricoFila) -> PagoParametrico:
    return PagoParametrico(
        id=fila.id,
        evento_id=fila.evento_id,
        siniestro_id=fila.siniestro_id,
        monto=fila.monto,
        pagado_en=fila.pagado_en,
    )


def _evento_a_dominio(fila: EventoParametricoFila) -> EventoParametrico:
    return EventoParametrico(evento_id=fila.evento_id, valor=fila.valor, recibido_en=fila.recibido_en)


class RepositorioSiniestrosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def _transiciones(self, siniestro_id: UUID) -> list[TransicionEstadoFila]:
        return list(
            await self._s.scalars(
                select(TransicionEstadoFila).where(TransicionEstadoFila.siniestro_id == siniestro_id)
            )
        )

    async def _a_dominio(self, filas) -> list[Siniestro]:
        return [_siniestro_a_dominio(f, await self._transiciones(f.id)) for f in filas]

    async def obtener(self, siniestro_id: UUID) -> Siniestro | None:
        fila = await self._s.get(SiniestroFila, siniestro_id)
        if fila is None:
            return None
        return _siniestro_a_dominio(fila, await self._transiciones(siniestro_id))

    async def obtener_por_evento(self, evento_id: str) -> Siniestro | None:
        fila = await self._s.scalar(select(SiniestroFila).where(SiniestroFila.evento_id == evento_id))
        if fila is None:
            return None
        return await self.obtener(fila.id)

    async def obtener_por_clave_idempotencia(self, clave: str) -> Siniestro | None:
        fila = await self._s.scalar(select(SiniestroFila).where(SiniestroFila.clave_idempotencia == clave))
        if fila is None:
            return None
        return await self.obtener(fila.id)

    async def listar(self, limite: int, usuario_id: UUID | None = None) -> list[Siniestro]:
        return await self.filtrar(FiltroSiniestros(limite=limite, usuario_id=usuario_id))

    async def filtrar(self, filtro: FiltroSiniestros) -> list[Siniestro]:
        consulta = select(SiniestroFila)
        if filtro.usuario_id is not None:
            consulta = consulta.where(SiniestroFila.usuario_id == filtro.usuario_id)
        if filtro.tipo is not None:
            consulta = consulta.where(SiniestroFila.tipo == filtro.tipo.value)
        if filtro.estado is not None:
            consulta = consulta.where(SiniestroFila.estado == filtro.estado.value)
        if filtro.resultado is not None:
            consulta = consulta.where(SiniestroFila.resultado == filtro.resultado.value)
        if filtro.requiere_revision is not None:
            consulta = consulta.where(SiniestroFila.requiere_revision == filtro.requiere_revision)
        consulta = consulta.order_by(SiniestroFila.creado_en.desc()).limit(filtro.limite)
        return await self._a_dominio(await self._s.scalars(consulta))

    async def listar_abiertos_por_poliza(self, poliza_id: UUID) -> list[Siniestro]:
        """HU-61: abierto = cualquier estado salvo PAGADO, y sin rechazo (también terminal)."""
        filas = await self._s.scalars(
            select(SiniestroFila).where(
                and_(
                    SiniestroFila.poliza_id == poliza_id,
                    SiniestroFila.estado != EstadoSiniestro.PAGADO.value,
                    func.coalesce(SiniestroFila.resultado, "") != ResultadoDecision.RECHAZADO.value,
                )
            )
        )
        return await self._a_dominio(filas)

    async def contar_avisos_de_poliza_desde(self, poliza_id: UUID, desde: datetime, excluir: UUID) -> int:
        return int(
            await self._s.scalar(
                select(func.count())
                .select_from(SiniestroFila)
                .where(
                    SiniestroFila.poliza_id == poliza_id,
                    SiniestroFila.tipo == TipoSiniestro.ASISTIDO.value,
                    SiniestroFila.creado_en >= desde,
                    SiniestroFila.id != excluir,
                )
            )
            or 0
        )

    async def tomar_pendientes_de_evaluacion(self, limite: int) -> list[Siniestro]:
        filas = await self._s.scalars(
            select(SiniestroFila)
            .where(
                SiniestroFila.tipo == TipoSiniestro.ASISTIDO.value,
                SiniestroFila.estado == EstadoSiniestro.RECIBIDO.value,
            )
            .order_by(SiniestroFila.creado_en)
            .limit(limite)
            .with_for_update(skip_locked=True)
        )
        return await self._a_dominio(filas)

    async def agregar(self, siniestro: Siniestro) -> None:
        fila = SiniestroFila(id=siniestro.id, creado_en=siniestro.creado_en)
        _copiar_a_fila(siniestro, fila)
        self._s.add(fila)
        await self._s.flush()
        for transicion in siniestro.historial:
            self._agregar_transicion(siniestro.id, transicion)
        # Flush inmediato: las filas de transición referencian siniestro_id por FK y deben
        # verse antes de que termine el bloque, igual que el patrón de ms-cotizacion.
        await self._s.flush()
        await self._s.refresh(fila, ["numero"])
        siniestro.numero = fila.numero

    async def actualizar(self, siniestro: Siniestro) -> None:
        fila = await self._s.get(SiniestroFila, siniestro.id)
        _copiar_a_fila(siniestro, fila)
        # Persiste solo las transiciones que aún no están en la base: un caso de uso puede
        # llamar actualizar() varias veces en la misma transacción sin duplicar la traza.
        guardadas = await self._s.scalar(
            select(func.count())
            .select_from(TransicionEstadoFila)
            .where(TransicionEstadoFila.siniestro_id == siniestro.id)
        )
        for transicion in siniestro.historial[int(guardadas or 0) :]:
            self._agregar_transicion(siniestro.id, transicion)
        await self._s.flush()

    def _agregar_transicion(self, siniestro_id: UUID, transicion: TransicionEstado) -> None:
        self._s.add(
            TransicionEstadoFila(
                id=uuid4(),
                siniestro_id=siniestro_id,
                estado=transicion.estado.value,
                ocurrido_en=transicion.ocurrido_en,
                origen=transicion.origen,
            )
        )


class RepositorioEventosParametricosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_por_clave(self, evento_id: str) -> EventoParametrico | None:
        fila = await self._s.get(EventoParametricoFila, evento_id)
        return _evento_a_dominio(fila) if fila else None

    async def agregar(self, evento: EventoParametrico) -> None:
        self._s.add(
            EventoParametricoFila(evento_id=evento.evento_id, valor=evento.valor, recibido_en=evento.recibido_en)
        )
        await self._s.flush()


class RepositorioEvaluacionesSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_por_evento(self, evento_id: str) -> EvaluacionUmbral | None:
        fila = await self._s.scalar(select(EvaluacionUmbralFila).where(EvaluacionUmbralFila.evento_id == evento_id))
        return _evaluacion_a_dominio(fila) if fila else None

    async def agregar(self, evaluacion: EvaluacionUmbral) -> None:
        self._s.add(
            EvaluacionUmbralFila(
                id=evaluacion.id,
                evento_id=evaluacion.evento_id,
                umbral=evaluacion.umbral,
                valor=evaluacion.valor,
                poliza_vigente=evaluacion.poliza_vigente,
                decision=evaluacion.decision,
                motivo=evaluacion.motivo,
                evaluada_en=evaluacion.evaluada_en,
            )
        )


class RepositorioPagosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_por_evento(self, evento_id: str) -> PagoParametrico | None:
        fila = await self._s.scalar(select(PagoParametricoFila).where(PagoParametricoFila.evento_id == evento_id))
        return _pago_a_dominio(fila) if fila else None

    async def agregar(self, pago: PagoParametrico) -> None:
        self._s.add(
            PagoParametricoFila(
                id=pago.id,
                evento_id=pago.evento_id,
                siniestro_id=pago.siniestro_id,
                monto=pago.monto,
                pagado_en=pago.pagado_en,
            )
        )


class RepositorioAdjuntosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def listar_de(self, siniestro_id: UUID) -> list[Adjunto]:
        filas = await self._s.scalars(
            select(AdjuntoFila).where(AdjuntoFila.siniestro_id == siniestro_id).order_by(AdjuntoFila.cargado_en)
        )
        return [
            Adjunto(
                id=f.id,
                siniestro_id=f.siniestro_id,
                usuario_id=f.usuario_id,
                tipo=f.tipo,
                nombre_original=f.nombre_original,
                content_type=f.content_type,
                tamano_bytes=f.tamano_bytes,
                sha256=f.sha256,
                s3_bucket=f.s3_bucket,
                s3_key=f.s3_key,
                cargado_en=f.cargado_en,
            )
            for f in filas
        ]

    async def agregar(self, adjunto: Adjunto) -> None:
        self._s.add(
            AdjuntoFila(
                id=adjunto.id,
                siniestro_id=adjunto.siniestro_id,
                usuario_id=adjunto.usuario_id,
                tipo=adjunto.tipo,
                nombre_original=adjunto.nombre_original,
                content_type=adjunto.content_type,
                tamano_bytes=adjunto.tamano_bytes,
                sha256=adjunto.sha256,
                s3_bucket=adjunto.s3_bucket,
                s3_key=adjunto.s3_key,
                cargado_en=adjunto.cargado_en,
            )
        )


class RepositorioDecisionesSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def listar_de(self, siniestro_id: UUID) -> list[Decision]:
        filas = await self._s.scalars(
            select(DecisionFila).where(DecisionFila.siniestro_id == siniestro_id).order_by(DecisionFila.decidida_en)
        )
        return [
            Decision(
                id=f.id,
                siniestro_id=f.siniestro_id,
                origen=OrigenDecision(f.origen),
                actor=f.actor,
                resultado=ResultadoAuditado(f.resultado),
                motivo=f.motivo,
                reglas=[ReglaEvaluada(r["codigo"], bool(r["cumple"]), r["detalle"]) for r in (f.reglas or [])],
                decidida_en=f.decidida_en,
            )
            for f in filas
        ]

    async def agregar(self, decision: Decision) -> None:
        self._s.add(
            DecisionFila(
                id=decision.id,
                siniestro_id=decision.siniestro_id,
                origen=decision.origen.value,
                actor=decision.actor,
                resultado=decision.resultado.value,
                motivo=decision.motivo,
                reglas=[r.como_dict() for r in decision.reglas],
                decidida_en=decision.decidida_en,
            )
        )


class RepositorioPagosSiniestroSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_de(self, siniestro_id: UUID) -> PagoSiniestro | None:
        f = await self._s.scalar(select(PagoSiniestroFila).where(PagoSiniestroFila.siniestro_id == siniestro_id))
        if f is None:
            return None
        return PagoSiniestro(
            id=f.id,
            siniestro_id=f.siniestro_id,
            clave_idempotencia=f.clave_idempotencia,
            comprobante=f.comprobante,
            monto=f.monto,
            origen=OrigenDecision(f.origen),
            autorizado_por=f.autorizado_por,
            pagado_en=f.pagado_en,
        )

    async def agregar(self, pago: PagoSiniestro) -> None:
        self._s.add(
            PagoSiniestroFila(
                id=pago.id,
                siniestro_id=pago.siniestro_id,
                clave_idempotencia=pago.clave_idempotencia,
                comprobante=pago.comprobante,
                monto=pago.monto,
                origen=pago.origen.value,
                autorizado_por=pago.autorizado_por,
                pagado_en=pago.pagado_en,
            )
        )

    async def registrar_intento(self, intento: IntentoPago) -> None:
        self._s.add(
            IntentoPagoFila(
                id=intento.id,
                siniestro_id=intento.siniestro_id,
                clave_idempotencia=intento.clave_idempotencia,
                resultado=intento.resultado,
                comprobante_devuelto=intento.comprobante_devuelto,
                actor=intento.actor,
                ocurrido_en=intento.ocurrido_en,
            )
        )

    async def listar_intentos(self, siniestro_id: UUID) -> list[IntentoPago]:
        filas = await self._s.scalars(
            select(IntentoPagoFila)
            .where(IntentoPagoFila.siniestro_id == siniestro_id)
            .order_by(IntentoPagoFila.ocurrido_en)
        )
        return [
            IntentoPago(
                siniestro_id=f.siniestro_id,
                clave_idempotencia=f.clave_idempotencia,
                resultado=f.resultado,
                comprobante_devuelto=f.comprobante_devuelto,
                actor=f.actor,
                ocurrido_en=f.ocurrido_en,
                id=f.id,
            )
            for f in filas
        ]


class RepositorioParametrosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    @staticmethod
    def _a_dominio(f: ParametroRamoFila) -> ParametroRamo:
        return ParametroRamo(f.ramo, f.reserva_base, f.umbral_automatico, f.ventana_duplicado_dias)

    async def obtener(self, ramo: str) -> ParametroRamo | None:
        fila = await self._s.get(ParametroRamoFila, ramo)
        return self._a_dominio(fila) if fila else None

    async def listar(self) -> list[ParametroRamo]:
        return [self._a_dominio(f) for f in await self._s.scalars(select(ParametroRamoFila).order_by(ParametroRamoFila.ramo))]


class OutboxSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def agregar(self, evento: EventoDominio) -> None:
        self._s.add(
            OutboxFila(id=evento.id, tipo=evento.tipo, agregado_id=evento.agregado_id, payload=evento.payload)
        )


class UnidadDeTrabajoSQL:
    def __init__(self, fabrica: async_sessionmaker[AsyncSession]) -> None:
        self._fabrica = fabrica

    async def __aenter__(self) -> UnidadDeTrabajoSQL:
        self._sesion = self._fabrica()
        self.siniestros = RepositorioSiniestrosSQL(self._sesion)
        self.eventos_parametricos = RepositorioEventosParametricosSQL(self._sesion)
        self.evaluaciones = RepositorioEvaluacionesSQL(self._sesion)
        self.pagos = RepositorioPagosSQL(self._sesion)
        self.adjuntos = RepositorioAdjuntosSQL(self._sesion)
        self.decisiones = RepositorioDecisionesSQL(self._sesion)
        self.pagos_siniestro = RepositorioPagosSiniestroSQL(self._sesion)
        self.parametros = RepositorioParametrosSQL(self._sesion)
        self.outbox = OutboxSQL(self._sesion)
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._sesion.rollback()
        await self._sesion.close()

    async def confirmar(self) -> None:
        try:
            await self._sesion.commit()
        except IntegrityError as exc:
            await self._sesion.rollback()
            mensaje = str(exc.orig)
            if "evento_id" in mensaje or "uq_" in mensaje.lower():
                raise ClaveIdempotenciaDuplicada from exc
            raise


def crear_motor(config: Settings) -> AsyncEngine:
    return create_async_engine(config.database_url, pool_size=config.db_pool_size, pool_pre_ping=True)


def fabrica_unidad_de_trabajo(motor: AsyncEngine):
    sesiones = async_sessionmaker(motor, expire_on_commit=False)
    return lambda: UnidadDeTrabajoSQL(sesiones)
