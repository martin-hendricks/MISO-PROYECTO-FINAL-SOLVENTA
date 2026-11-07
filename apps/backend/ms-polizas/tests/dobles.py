from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from app.application.casos_uso import SolicitudEmision
from app.domain.modelos import Cobertura, ConstanciaFirma, EstadoPoliza, EventoDominio, Poliza, Prima
from app.ports.firma import ResultadoFirma
from app.ports.persistencia import PolizaYaEmitida
from app.ports.reportes import ReporteGenerado


def coberturas() -> list[Cobertura]:
    return [
        Cobertura(nombre="Responsabilidad civil", suma_asegurada=Decimal("50000000.00"), deducible=Decimal("0")),
        Cobertura(nombre="Daños totales", suma_asegurada=Decimal("80000000.00"), deducible=Decimal("1000000.00")),
    ]


def solicitud(oferta_id: UUID | None = None) -> SolicitudEmision:
    return SolicitudEmision(
        solicitud_id=uuid4(),
        oferta_id=oferta_id or uuid4(),
        usuario_id=uuid4(),
        token_pago_confirmado=uuid4(),
        coberturas=coberturas(),
    )


def poliza_de_prueba(
    usuario_id: UUID | None = None,
    fin_vigencia: date | None = None,
    inicio_vigencia: date | None = None,
    estado: EstadoPoliza = EstadoPoliza.VIGENTE,
    cancelada_en: date | None = None,
) -> Poliza:
    """Construye una Poliza con fechas/estado controlados, sin pasar por
    emitir_poliza() (que siempre usa la fecha real de hoy) -- necesario para
    probar listar_por_vencer/listar_emitidas_entre/listar_canceladas_entre
    con ventanas de tiempo determinísticas."""
    hoy = date.today()
    return Poliza(
        id=uuid4(),
        oferta_id=uuid4(),
        usuario_id=usuario_id or uuid4(),
        numero=f"POL-{hoy.year}-{uuid4().hex[:8]}",
        inicio_vigencia=inicio_vigencia or (hoy - timedelta(days=335)),
        fin_vigencia=fin_vigencia or (hoy + timedelta(days=30)),
        estado=estado,
        coberturas=tuple(coberturas()),
        prima=Prima(valor=Decimal("130000000.00")),
        cancelada_en=cancelada_en,
        cancelada_por="operador@solventa.co" if estado == EstadoPoliza.CANCELADA else None,
        motivo_cancelacion="Solicitud del cliente" if estado == EstadoPoliza.CANCELADA else None,
        devolucion_estimada=Decimal("1000.00") if estado == EstadoPoliza.CANCELADA else None,
    )


class SuscripcionesFalsas:
    def __init__(self, aceptada: bool = True) -> None:
        self.respuesta = aceptada
        self.consultas: list[UUID] = []

    async def aceptada(self, solicitud_id):
        self.consultas.append(solicitud_id)
        return self.respuesta


class CobrosFalsos:
    def __init__(self, exitoso: bool = True) -> None:
        self.respuesta = exitoso

    async def exitoso(self, oferta_id, token_pago_confirmado):
        return self.respuesta


class FirmaFalsa:
    def __init__(self, exitosa: bool = True) -> None:
        self.exitosa = exitosa
        self.firmadas: list[UUID] = []

    async def firmar(self, oferta_id):
        self.firmadas.append(oferta_id)
        if self.exitosa:
            return ResultadoFirma(exitosa=True, firma_hash=f"hash-{oferta_id}")
        return ResultadoFirma(exitosa=False, motivo="Firma rechazada por el firmante")


class ReportesFalsos:
    """Doble de GeneradorReportes: no genera CSV real, solo registra qué se
    le pidió, para que los tests verifiquen que el caso de uso reunió los
    datos correctos sin acoplarse al formato real del stub."""

    def __init__(self) -> None:
        self.llamadas_regulador: list[tuple[list, "date", "date"]] = []
        self.llamadas_reaseguradora: list[tuple[list, "date", "date"]] = []

    async def reporte_regulador(self, polizas, desde, hasta):
        self.llamadas_regulador.append((polizas, desde, hasta))
        return ReporteGenerado(
            nombre_archivo="regulador.csv", tipo_contenido="text/csv", contenido=f"{len(polizas)} filas"
        )

    async def reporte_reaseguradora(self, canceladas, desde, hasta):
        self.llamadas_reaseguradora.append((canceladas, desde, hasta))
        return ReporteGenerado(
            nombre_archivo="reaseguradora.csv", tipo_contenido="text/csv", contenido=f"{len(canceladas)} filas"
        )


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.polizas: dict[UUID, Poliza] = {}
        self.constancias: list[ConstanciaFirma] = []
        self.eventos: list[EventoDominio] = []
        self.secuencia = 0
        self.chocar_en_proximo_commit: Poliza | None = None


class _Polizas:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self):
        return {**self._uow.almacen.polizas, **self._uow.pendientes}

    async def obtener(self, poliza_id):
        poliza = self._vista().get(poliza_id)
        return deepcopy(poliza) if poliza else None

    async def obtener_por_oferta(self, oferta_id):
        return next((deepcopy(p) for p in self._vista().values() if p.oferta_id == oferta_id), None)

    async def obtener_por_numero(self, numero):
        return next((deepcopy(p) for p in self._vista().values() if p.numero == numero), None)

    async def ofertas_con_poliza(self, oferta_ids):
        return {p.oferta_id for p in self._vista().values() if p.oferta_id in oferta_ids}

    async def listar_por_vencer(self, hoy, hasta, usuario_id=None):
        polizas = [
            p
            for p in self._vista().values()
            if p.estado == EstadoPoliza.VIGENTE and hoy <= p.fin_vigencia <= hasta
        ]
        if usuario_id is not None:
            polizas = [p for p in polizas if p.usuario_id == usuario_id]
        return [deepcopy(p) for p in sorted(polizas, key=lambda p: p.fin_vigencia)]

    async def listar_emitidas_entre(self, desde, hasta):
        polizas = [p for p in self._vista().values() if desde <= p.inicio_vigencia <= hasta]
        return [deepcopy(p) for p in sorted(polizas, key=lambda p: p.inicio_vigencia)]

    async def listar_canceladas_entre(self, desde, hasta):
        polizas = [
            p
            for p in self._vista().values()
            if p.estado == EstadoPoliza.CANCELADA and p.cancelada_en is not None and desde <= p.cancelada_en <= hasta
        ]
        return [deepcopy(p) for p in sorted(polizas, key=lambda p: p.cancelada_en)]

    async def listar_por_usuario(self, usuario_id, limite):
        polizas = sorted(
            (p for p in self._vista().values() if p.usuario_id == usuario_id),
            key=lambda p: p.inicio_vigencia,
            reverse=True,
        )
        return [deepcopy(p) for p in polizas[:limite]]

    async def siguiente_secuencia(self):
        # Como una secuencia de PostgreSQL: avanza aunque la transacción se revierta.
        self._uow.almacen.secuencia += 1
        return self._uow.almacen.secuencia

    async def agregar(self, poliza):
        self._uow.pendientes[poliza.id] = poliza

    async def actualizar(self, poliza):
        self._uow.pendientes[poliza.id] = poliza


class _Firmas:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, constancia):
        self._uow.constancias_pendientes.append(constancia)

    async def ultima_por_oferta(self, oferta_id):
        todas = [*self._uow.almacen.constancias, *self._uow.constancias_pendientes]
        return next((c for c in reversed(todas) if c.oferta_id == oferta_id), None)


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento):
        self._uow.eventos_pendientes.append(evento)

    async def existe_para_agregado(self, tipo, agregado_id):
        todos = [*self._uow.almacen.eventos, *self._uow.eventos_pendientes]
        return any(e.tipo == tipo and e.agregado_id == agregado_id for e in todos)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, Poliza] = {}
        self.eventos_pendientes: list[EventoDominio] = []
        self.constancias_pendientes: list[ConstanciaFirma] = []
        self.polizas = _Polizas(self)
        self.firmas = _Firmas(self)
        self.outbox = _Outbox(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.pendientes.clear()
        self.eventos_pendientes.clear()
        self.constancias_pendientes.clear()

    async def confirmar(self):
        ganadora = self.almacen.chocar_en_proximo_commit
        if ganadora is not None:
            self.almacen.chocar_en_proximo_commit = None
            self.almacen.polizas[ganadora.id] = ganadora
            raise PolizaYaEmitida
        self.almacen.polizas.update(self.pendientes)
        self.almacen.eventos.extend(self.eventos_pendientes)
        self.almacen.constancias.extend(self.constancias_pendientes)
        self.pendientes.clear()
        self.eventos_pendientes.clear()
        self.constancias_pendientes.clear()
