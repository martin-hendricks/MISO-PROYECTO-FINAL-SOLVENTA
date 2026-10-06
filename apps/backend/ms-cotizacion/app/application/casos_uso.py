from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from app.domain.errores import ProductoInexistente
from app.domain.modelos import Cotizacion
from app.ports.cotizacion import (
    CalculadoraPrima,
    Catalogo,
    FuenteFactorRiesgo,
    Reloj,
    RepositorioCotizaciones,
)


@dataclass(frozen=True)
class Colaboradores:
    catalogo: Catalogo
    calculadora_prima: CalculadoraPrima
    factor_riesgo: FuenteFactorRiesgo
    cotizaciones: RepositorioCotizaciones
    reloj: Reloj
    vigencia_oferta: timedelta


async def recibir_solicitud(
    deps: Colaboradores, codigo_producto: str, datos_riesgo: dict[str, Any]
) -> Cotizacion:
    """HU-3: valida contra el catálogo antes de cotizar y encadena prima (HU-4) y factor (HU-5).

    Una solicitud inválida lanza un error de negocio y no genera cotizacionId.
    """
    producto = await deps.catalogo.obtener(codigo_producto)
    if producto is None:
        raise ProductoInexistente(codigo_producto)

    datos = producto.validar_datos_riesgo(datos_riesgo)
    prima_base = await deps.calculadora_prima.calcular(producto, datos)
    factor = await deps.factor_riesgo.obtener(producto, datos)

    cotizacion = Cotizacion.ofertar(
        producto, datos, prima_base, factor, deps.reloj.ahora(), deps.vigencia_oferta
    )
    await deps.cotizaciones.guardar(cotizacion)
    return cotizacion
