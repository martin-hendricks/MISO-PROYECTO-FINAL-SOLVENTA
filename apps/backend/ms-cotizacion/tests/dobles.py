from copy import deepcopy
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.catalogo import (
    Cobertura,
    DefinicionProducto,
    RangoNumerico,
    UnidadLimite,
    ValoresPermitidos,
)
from app.domain.modelos import EstadoSolicitud, EventoDominio, SolicitudCotizacion
from app.domain.oferta import Oferta
from app.domain.rating import ReglaRating
from app.ports.persistencia import AceptacionConcurrente, ClaveIdempotenciaDuplicada
from app.ports.suscripcion import DecisionSuscripcion

SOAT_MOTOCICLETA = DefinicionProducto(
    producto="soat-motocicleta",
    nombre="SOAT motocicleta",
    moneda="COP",
    coberturas=(
        Cobertura("gastos_medicos", "Gastos médicos", Decimal("800"), UnidadLimite.SMLDV),
        Cobertura("incapacidad_permanente", "Incapacidad permanente", Decimal("180"), UnidadLimite.SMLDV),
        Cobertura("muerte", "Muerte y gastos funerarios", Decimal("750"), UnidadLimite.SMLDV),
        Cobertura("gastos_transporte", "Gastos de transporte", Decimal("10"), UnidadLimite.SMLDV),
    ),
    datos_riesgo={
        "cilindraje_cc": RangoNumerico(Decimal("50"), Decimal("1800")),
        "modelo_anio": RangoNumerico(Decimal("2000"), Decimal("2026")),
        "ciudad_circulacion": ValoresPermitidos(("bogota", "medellin", "cali", "barranquilla", "bucaramanga")),
    },
)


class CatalogoEnMemoria:
    def __init__(self, *productos: DefinicionProducto) -> None:
        self._productos = {p.producto: p for p in productos or (SOAT_MOTOCICLETA,)}

    def obtener(self, producto: str) -> DefinicionProducto | None:
        return self._productos.get(producto)

    def listar(self) -> list[DefinicionProducto]:
        return list(self._productos.values())


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.solicitudes: dict[UUID, SolicitudCotizacion] = {}
        self.reglas_rating: dict[str, ReglaRating] = {}
        self.ofertas: dict[UUID, Oferta] = {}
        self.eventos: list[EventoDominio] = []
        self.chocar_en_proximo_commit: SolicitudCotizacion | None = None
        # Simula otra aceptación que confirmó entre la lectura y la escritura condicional.
        self.aceptar_antes: SolicitudCotizacion | None = None


class _RepoSolicitudes:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, SolicitudCotizacion]:
        return {**self._uow.almacen.solicitudes, **self._uow.pendientes}

    async def obtener(self, solicitud_id):
        s = self._vista().get(solicitud_id)
        return deepcopy(s) if s else None

    async def obtener_por_clave(self, clave):
        return next((deepcopy(s) for s in self._vista().values() if s.idempotency_key == clave), None)

    async def agregar(self, solicitud):
        self._uow.pendientes[solicitud.id] = solicitud

    async def actualizar(self, solicitud):
        self._uow.pendientes[solicitud.id] = solicitud

    async def registrar_aceptacion(self, solicitud):
        ganadora = self._uow.almacen.aceptar_antes
        if ganadora is not None:
            self._uow.almacen.aceptar_antes = None
            self._uow.almacen.solicitudes[ganadora.id] = ganadora
        if self._uow.almacen.solicitudes[solicitud.id].estado is not EstadoSolicitud.COTIZADA:
            raise AceptacionConcurrente
        self._uow.pendientes[solicitud.id] = solicitud

    async def listar_por_asesor(self, asesor_id, estados, vigentes_desde, desplazamiento, limite):
        ofertas = {o.solicitud_id: o for o in self._uow.almacen.ofertas.values()}
        filas = [
            (s, ofertas[s.id])
            for s in self._vista().values()
            if s.asesor_id == asesor_id
            and s.estado in estados
            and s.id in ofertas
            and (vigentes_desde is None or ofertas[s.id].vence_en > vigentes_desde)
        ]
        filas.sort(key=lambda f: (f[0].creada_en, f[0].id), reverse=True)
        return deepcopy(filas[desplazamiento : desplazamiento + limite])


class _RepoOfertas:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, Oferta]:
        return {**self._uow.almacen.ofertas, **self._uow.ofertas_pendientes}

    async def obtener(self, oferta_id):
        o = self._vista().get(oferta_id)
        return deepcopy(o) if o else None

    async def obtener_por_solicitud(self, solicitud_id):
        return next((deepcopy(o) for o in self._vista().values() if o.solicitud_id == solicitud_id), None)

    async def agregar(self, oferta):
        self._uow.ofertas_pendientes[oferta.id] = oferta


class _RepoReglasRating:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def obtener_vigente(self, producto: str) -> ReglaRating | None:
        candidatas = [r for r in self._uow.almacen.reglas_rating.values() if r.producto == producto]
        if not candidatas:
            return None
        return max(candidatas, key=lambda r: r.version)


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento):
        self._uow.eventos_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, SolicitudCotizacion] = {}
        self.ofertas_pendientes: dict[UUID, Oferta] = {}
        self.eventos_pendientes: list[EventoDominio] = []
        self.solicitudes = _RepoSolicitudes(self)
        self.reglas_rating = _RepoReglasRating(self)
        self.ofertas = _RepoOfertas(self)
        self.outbox = _Outbox(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.pendientes.clear()
        self.ofertas_pendientes.clear()
        self.eventos_pendientes.clear()

    async def confirmar(self):
        ganador = self.almacen.chocar_en_proximo_commit
        if ganador is not None:
            self.almacen.chocar_en_proximo_commit = None
            self.almacen.solicitudes[ganador.id] = ganador
            raise ClaveIdempotenciaDuplicada
        self.almacen.solicitudes.update(self.pendientes)
        self.almacen.ofertas.update(self.ofertas_pendientes)
        self.almacen.eventos.extend(self.eventos_pendientes)
        self.pendientes.clear()
        self.ofertas_pendientes.clear()
        self.eventos_pendientes.clear()


def regla_rating_soat_motocicleta() -> ReglaRating:
    return ReglaRating(
        id=uuid4(),
        producto="soat-motocicleta",
        version="0001",
        formula={
            "insumos_requeridos": ["cilindraje_cc"],
            "base": "120000",
            "gastos_fijos": "8500",
            "moneda": "COP",
        },
    )


class SuscripcionesFalsas:
    """Doble de ms-suscripcion: idempotente por solicitud, como HU-13."""

    def __init__(self, decision: str = "ACEPTADA") -> None:
        self.decision = decision
        self.caida: Exception | None = None
        self.llamadas: list[UUID] = []
        self._decisiones: dict[UUID, DecisionSuscripcion] = {}

    async def evaluar(self, solicitud_id, perfil_id, score):
        self.llamadas.append(solicitud_id)
        if self.caida is not None:
            raise self.caida
        return self._decisiones.setdefault(
            solicitud_id, DecisionSuscripcion(uuid4(), self.decision, "regla de suscripción")
        )
