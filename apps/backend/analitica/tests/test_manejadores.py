from datetime import date, datetime, timezone
from uuid import uuid4

from app.application.manejadores import manejar_evento
from app.domain.eventos import EventoBus


_SIN_FECHA = object()


def _evento(tipo="PolizaEmitida", ocurrido_en=_SIN_FECHA, evento_id=None):
    if ocurrido_en is _SIN_FECHA:
        ocurrido_en = datetime(2026, 3, 1, tzinfo=timezone.utc)
    return EventoBus(
        evento_id=evento_id or uuid4(),
        tipo=tipo,
        agregado_id=uuid4(),
        ocurrido_en=ocurrido_en,
        origen="ms_polizas",
        payload={"usuario_id": str(uuid4())},
    )


async def test_manejar_evento_incrementa_el_conteo(uow, almacen):
    evento = _evento("PolizaEmitida")

    resultado = await manejar_evento(uow, evento)

    assert resultado is True
    assert almacen.conteos[("PolizaEmitida", date(2026, 3, 1))] == 1


async def test_manejar_evento_tipo_no_soportado_se_ignora(uow, almacen):
    evento = _evento("TipoNoSoportado")

    resultado = await manejar_evento(uow, evento)

    assert resultado is False
    assert not almacen.conteos


async def test_manejar_evento_sin_fecha_se_ignora(uow, almacen):
    evento = _evento("PolizaEmitida", ocurrido_en=None)

    resultado = await manejar_evento(uow, evento)

    assert resultado is False
    assert not almacen.conteos


async def test_manejar_evento_repetido_no_duplica(uow, almacen):
    evento_id = uuid4()
    primero = _evento("PolizaEmitida", evento_id=evento_id)
    repetido = _evento("PolizaEmitida", evento_id=evento_id)

    assert await manejar_evento(uow, primero) is True
    assert await manejar_evento(uow, repetido) is False
    assert almacen.conteos[("PolizaEmitida", date(2026, 3, 1))] == 1


async def test_manejar_evento_acumula_varios_del_mismo_tipo_y_fecha(uow, almacen):
    for _ in range(3):
        await manejar_evento(uow, _evento("PolizaCancelada"))

    assert almacen.conteos[("PolizaCancelada", date(2026, 3, 1))] == 3


async def test_poliza_por_vencer_es_soportado(uow, almacen):
    resultado = await manejar_evento(uow, _evento("PolizaPorVencer"))
    assert resultado is True
    assert almacen.conteos[("PolizaPorVencer", date(2026, 3, 1))] == 1


async def test_manejar_evento_captura_excepcion_inesperada():
    class UowQueRevienta:
        def __call__(self):
            return self

        async def __aenter__(self):
            class Metricas:
                async def incrementar(self, *a, **k):
                    raise RuntimeError("fallo inesperado")

            self.metricas = Metricas()
            return self

        async def __aexit__(self, *exc):
            return None

        async def confirmar(self):
            return None

    resultado = await manejar_evento(UowQueRevienta(), _evento("PolizaEmitida"))
    assert resultado is False
