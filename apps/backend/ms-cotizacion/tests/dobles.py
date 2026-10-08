from decimal import Decimal

from app.domain.catalogo import (
    Cobertura,
    DefinicionProducto,
    RangoNumerico,
    UnidadLimite,
    ValoresPermitidos,
)
from app.domain.modelos import EventoDominio

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
        self.eventos: list[EventoDominio] = []


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento):
        self._uow.eventos_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.eventos_pendientes: list[EventoDominio] = []
        self.outbox = _Outbox(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.eventos_pendientes.clear()

    async def confirmar(self):
        self.almacen.eventos.extend(self.eventos_pendientes)
        self.eventos_pendientes.clear()
