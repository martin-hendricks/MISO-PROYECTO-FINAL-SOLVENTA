import os
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.config import Settings
from app.domain.modelos import EstadoSiniestro
from app.infrastructure.pagos import AdaptadorDesembolsoStub
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


@pytest.fixture
def adaptador_desembolso() -> AdaptadorDesembolsoStub:
    return AdaptadorDesembolsoStub()


async def test_ingesta_idempotente_persiste_evento_evaluacion_y_pago(uow, adaptador_desembolso):
    evento_id = f"it-{uuid4()}"

    primero = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, evento_id, Decimal("100"), Decimal("80"), True, Decimal("500.00")
    )
    segundo = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, evento_id, Decimal("100"), Decimal("80"), True, Decimal("500.00")
    )

    assert primero.procesado and not segundo.procesado
    assert segundo.pago.id == primero.pago.id
    assert len(adaptador_desembolso.desembolsos) == 1

    async with uow() as tx:
        total_pagos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.pago_parametrico WHERE evento_id = :id"),
            {"id": evento_id},
        )
    assert total_pagos == 1


async def test_cambiar_estado_persiste_historial(uow, adaptador_desembolso):
    evento_id = f"it-{uuid4()}"
    resultado = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, evento_id, Decimal("10"), Decimal("80"), True, Decimal("1")
    )  # queda en 'decidido' (umbral no cumplido)

    siniestro = await casos_uso.cambiar_estado_siniestro(
        uow, resultado.siniestro.id, EstadoSiniestro.ENRUTADO, "operador-it"
    )

    assert siniestro.estado is EstadoSiniestro.ENRUTADO
    releido = await casos_uso.consultar_siniestro(uow, resultado.siniestro.id)
    assert releido.estado is EstadoSiniestro.ENRUTADO
    assert any(t.origen == "operador-it" for t in releido.historial)


async def test_siniestros_abiertos_de_poliza_persisten_y_excluyen_pagados(uow, adaptador_desembolso):
    poliza_id = uuid4()
    abierto = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, f"it-abierto-{uuid4()}", Decimal("10"), Decimal("80"), True, Decimal("1"), poliza_id
    )  # decidido (umbral no cumplido) -> abierto
    await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, f"it-pagado-{uuid4()}", Decimal("100"), Decimal("80"), True, Decimal("1"), poliza_id
    )  # pagado -> no cuenta como abierto

    abiertos = await casos_uso.listar_siniestros_abiertos_de_poliza(uow, poliza_id)

    assert [s.id for s in abiertos] == [abierto.siniestro.id]


async def test_pagos_recibidos_le_pertenecen_al_dueno(uow, adaptador_desembolso):
    from pathlib import Path

    migracion = Path(__file__).resolve().parents[1] / "db" / "07_pago_parametrico_comprobante.sql"
    async with uow() as tx:
        await tx._sesion.execute(text(migracion.read_text()))
        await tx.confirmar()

    dueno = uuid4()
    evento = f"it-billetera-{uuid4()}"
    primero = await casos_uso.recibir_evento_parametrico(
        uow,
        adaptador_desembolso,
        evento,
        Decimal("100"),
        Decimal("80"),
        True,
        Decimal("180000.00"),
        usuario_id=dueno,
        ramo="clima-vuelos",
        poliza_numero="POL-11002-CO",
        descripcion="retraso de vuelo",
    )
    segundo = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, evento, Decimal("100"), Decimal("80"), True, Decimal("180000.00")
    )

    assert segundo.pago.comprobante == primero.pago.comprobante
    billetera = await casos_uso.listar_pagos_recibidos(uow, dueno)
    assert billetera.total == Decimal("180000.00")
    assert billetera.pagos[0].comprobante == primero.pago.comprobante
    assert billetera.pagos[0].ramo == "clima-vuelos"
    assert (await casos_uso.listar_pagos_recibidos(uow, uuid4())).pagos == []


async def test_pagos_recibidos_persisten_comprobante_y_no_duplican(uow, adaptador_desembolso):
    dueno = uuid4()
    evento_id = f"it-billetera-{uuid4()}"
    primero = await casos_uso.recibir_evento_parametrico(
        uow,
        adaptador_desembolso,
        evento_id,
        Decimal("100"),
        Decimal("80"),
        True,
        Decimal("180000.00"),
        usuario_id=dueno,
        ramo="clima-vuelos",
        poliza_numero="POL-11002-CO",
        descripcion="retraso de vuelo",
    )
    await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, evento_id, Decimal("100"), Decimal("80"), True, Decimal("180000.00")
    )

    billetera = await casos_uso.listar_pagos_recibidos(uow, dueno)

    assert len(billetera.pagos) == 1
    assert billetera.pagos[0].comprobante == primero.pago.comprobante
    assert billetera.total == Decimal("180000.00")


async def test_ingestas_concurrentes_del_mismo_evento_desembolsan_una_sola_vez(uow):
    """Carrera real contra PostgreSQL: la colision del evento_id salta en el flush
    (no en el commit) y quien pierde lee al ganador. Las entregas que llegan con el
    ganador aun en ENRUTADO reintentan el desembolso con la MISMA clave: un solo pago,
    una sola clave, y el adaptador idempotente absorbe las repeticiones."""
    import asyncio

    llamadas: list[str] = []

    class AdaptadorQueCuenta:
        async def desembolsar(self, evento_id, monto):
            llamadas.append(evento_id)

    evento_id = f"it-carrera-{uuid4()}"
    resultados = await asyncio.gather(
        *(
            casos_uso.recibir_evento_parametrico(
                uow, AdaptadorQueCuenta(), evento_id, Decimal("100"), Decimal("80"), True, Decimal("500.00")
            )
            for _ in range(10)
        )
    )

    assert sum(r.procesado for r in resultados) == 1
    assert len({r.pago.id for r in resultados}) == 1
    assert set(llamadas) == {evento_id}
    async with uow() as tx:
        pagos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.pago_parametrico WHERE evento_id = :id"), {"id": evento_id}
        )
        siniestros = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.siniestro WHERE evento_id = :id"), {"id": evento_id}
        )
    assert (pagos, siniestros) == (1, 1)


async def test_falla_del_desembolso_deja_enrutado_y_la_reingesta_lo_cierra(uow):
    llamadas: list[str] = []

    class AdaptadorQueFallaUnaVez:
        async def desembolsar(self, evento_id, monto):
            llamadas.append(evento_id)
            if len(llamadas) == 1:
                raise ConnectionError("pasarela caida")

    adaptador = AdaptadorQueFallaUnaVez()
    evento_id = f"it-medias-{uuid4()}"
    with pytest.raises(ConnectionError):
        await casos_uso.recibir_evento_parametrico(
            uow, adaptador, evento_id, Decimal("100"), Decimal("80"), True, Decimal("500.00")
        )
    async with uow() as tx:
        a_medias = await tx.siniestros.obtener_por_evento(evento_id)
    assert a_medias.estado is EstadoSiniestro.ENRUTADO

    final = await casos_uso.recibir_evento_parametrico(
        uow, adaptador, evento_id, Decimal("100"), Decimal("80"), True, Decimal("500.00")
    )

    assert final.siniestro.estado is EstadoSiniestro.PAGADO
    assert llamadas == [evento_id, evento_id]
    releido = await casos_uso.consultar_siniestro(uow, final.siniestro.id)
    assert [t.estado for t in releido.historial][-2:] == [EstadoSiniestro.ENRUTADO, EstadoSiniestro.PAGADO]
