from decimal import Decimal

from app.infrastructure.pagos import AdaptadorDesembolsoStub


async def test_adaptador_desembolso_stub_registra_el_desembolso():
    adaptador = AdaptadorDesembolsoStub()

    await adaptador.desembolsar("evt-1", Decimal("250.00"))

    assert adaptador.desembolsos == [("evt-1", Decimal("250.00"))]


async def test_adaptador_desembolso_stub_acumula_varios_desembolsos():
    adaptador = AdaptadorDesembolsoStub()

    await adaptador.desembolsar("evt-1", Decimal("250.00"))
    await adaptador.desembolsar("evt-2", Decimal("10.00"))

    assert adaptador.desembolsos == [("evt-1", Decimal("250.00")), ("evt-2", Decimal("10.00"))]
