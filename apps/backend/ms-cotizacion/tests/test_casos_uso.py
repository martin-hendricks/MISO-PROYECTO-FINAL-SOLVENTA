from datetime import timedelta
from decimal import Decimal

import pytest

from app.application import casos_uso
from app.domain.errores import DatoRiesgoInvalido, ProductoInexistente

from .conftest import DATOS_VALIDOS, VIGENCIA


async def test_solicitud_valida_encadena_prima_y_factor(deps, prima, factor, reloj, repositorio):
    cotizacion = await casos_uso.recibir_solicitud(deps, "PROTECCION_DISPOSITIVO", DATOS_VALIDOS)

    assert prima.llamadas == [DATOS_VALIDOS]
    assert factor.llamadas == [DATOS_VALIDOS]
    assert cotizacion.prima == Decimal("115000.00")
    assert await repositorio.obtener_vigente(cotizacion.id, reloj.ahora()) == cotizacion


async def test_producto_inexistente_no_cotiza(deps, prima, factor):
    with pytest.raises(ProductoInexistente) as exc:
        await casos_uso.recibir_solicitud(deps, "SOAT_MOTO", DATOS_VALIDOS)

    assert exc.value.campo == "producto"
    assert prima.llamadas == factor.llamadas == []


async def test_dato_fuera_de_rango_no_cotiza_ni_guarda(deps, prima, factor, repositorio):
    with pytest.raises(DatoRiesgoInvalido):
        await casos_uso.recibir_solicitud(deps, "PROTECCION_DISPOSITIVO", {**DATOS_VALIDOS, "valorDispositivo": 1})

    assert prima.llamadas == factor.llamadas == []
    assert repositorio._vigentes == {}


async def test_oferta_vencida_deja_de_ser_recuperable(deps, reloj, repositorio):
    cotizacion = await casos_uso.recibir_solicitud(deps, "PROTECCION_DISPOSITIVO", DATOS_VALIDOS)

    reloj.avanzar(VIGENCIA - timedelta(seconds=1))
    assert await repositorio.obtener_vigente(cotizacion.id, reloj.ahora()) is not None

    reloj.avanzar(timedelta(seconds=1))
    assert await repositorio.obtener_vigente(cotizacion.id, reloj.ahora()) is None
    assert repositorio._vigentes == {}
