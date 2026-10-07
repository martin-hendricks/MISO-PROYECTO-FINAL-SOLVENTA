from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from app.domain.catalogo import (
    Cobertura,
    DefinicionDatoRiesgo,
    DefinicionProducto,
    RangoNumerico,
    UnidadLimite,
    ValoresPermitidos,
)

from .sql import ESQUEMA, Base


class ProductoFila(Base):
    __tablename__ = "producto"

    producto_id: Mapped[UUID] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String, unique=True)
    nombre: Mapped[str]
    ramo: Mapped[str]
    moneda: Mapped[str]
    coberturas: Mapped[list[CoberturaFila]] = relationship(order_by="CoberturaFila.orden")
    datos_riesgo: Mapped[list[DatoRiesgoFila]] = relationship(order_by="DatoRiesgoFila.nombre")


class CoberturaFila(Base):
    __tablename__ = "cobertura_producto"

    cobertura_id: Mapped[UUID] = mapped_column(primary_key=True)
    producto_id: Mapped[UUID] = mapped_column(ForeignKey(f"{ESQUEMA}.producto.producto_id"))
    codigo: Mapped[str]
    nombre: Mapped[str]
    limite: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    unidad_limite: Mapped[str]
    orden: Mapped[int]


class DatoRiesgoFila(Base):
    __tablename__ = "dato_riesgo_producto"

    dato_riesgo_id: Mapped[UUID] = mapped_column(primary_key=True)
    producto_id: Mapped[UUID] = mapped_column(ForeignKey(f"{ESQUEMA}.producto.producto_id"))
    nombre: Mapped[str]
    tipo: Mapped[str]
    minimo: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    maximo: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    valores: Mapped[list[str] | None] = mapped_column(ARRAY(String))


def _dato_a_dominio(fila: DatoRiesgoFila) -> DefinicionDatoRiesgo:
    if fila.tipo == "rango":
        return RangoNumerico(minimo=Decimal(fila.minimo), maximo=Decimal(fila.maximo))
    if fila.tipo == "valores":
        return ValoresPermitidos(valores=tuple(fila.valores))
    raise ValueError(f"Tipo de dato de riesgo desconocido '{fila.tipo}' en '{fila.nombre}'")


def a_definicion(fila: ProductoFila) -> DefinicionProducto:
    return DefinicionProducto(
        producto=fila.codigo,
        nombre=fila.nombre,
        moneda=fila.moneda,
        coberturas=tuple(
            Cobertura(
                codigo=c.codigo,
                nombre=c.nombre,
                limite=Decimal(c.limite),
                unidad_limite=UnidadLimite(c.unidad_limite),
            )
            for c in fila.coberturas
        ),
        datos_riesgo={d.nombre: _dato_a_dominio(d) for d in fila.datos_riesgo},
    )


class CatalogoSQL:
    """Catálogo persistido en el almacén de ms-cotizacion (HU-1).

    Se lee una sola vez al arrancar y se sirve desde memoria: el catálogo es de solo lectura
    en ejecución y así la cotización no paga un viaje a la BD (EC-LAT-01). Un producto nuevo
    se incorpora con filas en db/, no con código (EC-MOD-01).
    """

    def __init__(self, productos: Iterable[DefinicionProducto]) -> None:
        self._productos = {p.producto: p for p in productos}

    @classmethod
    async def cargar(cls, motor: AsyncEngine) -> CatalogoSQL:
        async with AsyncSession(motor) as sesion:
            filas = await sesion.scalars(
                select(ProductoFila).options(
                    selectinload(ProductoFila.coberturas), selectinload(ProductoFila.datos_riesgo)
                )
            )
            catalogo = cls(a_definicion(f) for f in filas)
        if not catalogo._productos:
            raise RuntimeError(f"El catálogo de productos de {ESQUEMA} está vacío")
        return catalogo

    def obtener(self, producto: str) -> DefinicionProducto | None:
        return self._productos.get(producto)
