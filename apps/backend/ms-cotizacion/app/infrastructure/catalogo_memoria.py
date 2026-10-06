"""Catálogo PROVISIONAL de un ramo, solo lectura, hasta que HU-1 (SOLV-94) entregue el oficial.

PENDIENTE HU-1: el ramo no está cerrado. Jira (SOLV-94) dice "SOAT motocicleta"; la wiki
(Contratos-BFF HU-125/126, Backlog-UI-cliente-L1) usa "Protección de dispositivo" con
valorDispositivo / marca / masDe12Meses. Se toma el de la wiki porque es el que ya tienen
los contratos de canal. Coberturas, límites y rangos son valores de referencia.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.catalogo import CampoRiesgo, Cobertura, Producto, TipoDato

PROTECCION_DISPOSITIVO = Producto(
    codigo="PROTECCION_DISPOSITIVO",
    nombre="Protección de dispositivo",
    moneda="COP",
    coberturas=(
        Cobertura("ROBO", "Robo", Decimal("8000000")),
        Cobertura("PANTALLA", "Pantalla", Decimal("1500000")),
        Cobertura("HURTO_CALIFICADO", "Hurto calificado", Decimal("8000000")),
    ),
    campos_riesgo=(
        CampoRiesgo("valorDispositivo", TipoDato.ENTERO, minimo=300_000, maximo=8_000_000),
        CampoRiesgo("marca", TipoDato.TEXTO, minimo=1, maximo=40),
        CampoRiesgo("masDe12Meses", TipoDato.BOOLEANO),
    ),
)


class CatalogoEnMemoria:
    def __init__(self, productos: tuple[Producto, ...] = (PROTECCION_DISPOSITIVO,)) -> None:
        self._productos = {p.codigo: p for p in productos}

    async def obtener(self, codigo_producto: str) -> Producto | None:
        return self._productos.get(codigo_producto)
