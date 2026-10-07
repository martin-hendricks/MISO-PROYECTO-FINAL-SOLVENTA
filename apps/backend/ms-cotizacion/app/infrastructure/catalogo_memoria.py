from __future__ import annotations

from app.ports.catalogo import DefinicionProducto, RangoNumerico, ValoresPermitidos

CATALOGO_SOAT_MOTOCICLETA = DefinicionProducto(
    producto="soat-motocicleta",
    coberturas=["muerte", "incapacidad_permanente", "gastos_medicos"],
    datos_riesgo={
        "cilindraje_cc": RangoNumerico(minimo=50, maximo=1800),
        "modelo_anio": RangoNumerico(minimo=2000, maximo=2026),
        "ciudad_circulacion": ValoresPermitidos(
            valores=("bogota", "medellin", "cali", "barranquilla", "bucaramanga")
        ),
    },
)


class CatalogoEnMemoria:
    """Implementación SUSTITUIBLE de CatalogoProductos: stub mientras SOLV-94 entrega
    el catálogo real. Sustituirlo por un adaptador real (HTTP o SQL) no requiere cambiar
    application/ ni domain/: solo cumplir el Protocol."""

    def __init__(self) -> None:
        self._productos = {CATALOGO_SOAT_MOTOCICLETA.producto: CATALOGO_SOAT_MOTOCICLETA}

    def obtener(self, producto: str) -> DefinicionProducto | None:
        return self._productos.get(producto)
