from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import (
    EstadoPago,
    Pago,
    ResultadoPasarela,
    clave_cobro_prima,
    pago_prima_registrado,
)
from app.infrastructure.externos import TOKEN_RECHAZO, PasarelaStub

APROBADO = ResultadoPasarela(EstadoPago.APROBADO, "stub", "stub-1")


def test_la_clave_se_deriva_de_la_oferta_y_no_cambia_entre_intentos():
    oferta = uuid4()

    assert clave_cobro_prima(oferta) == clave_cobro_prima(oferta) == f"cobro-prima:{oferta}"


def test_el_pago_registra_el_resultado_de_la_pasarela_con_su_clave():
    oferta = uuid4()

    pago = Pago.registrar_prima(oferta, uuid4(), Decimal("100.00"), APROBADO)

    assert pago.estado is EstadoPago.APROBADO
    assert pago.idempotency_key == clave_cobro_prima(oferta)
    assert (pago.proveedor, pago.referencia_externa) == ("stub", "stub-1")


@pytest.mark.parametrize("monto", ["0", "-1"])
def test_monto_no_positivo_se_rechaza(monto):
    with pytest.raises(ReglaDeNegocioViolada) as error:
        Pago.registrar_prima(uuid4(), uuid4(), Decimal(monto), APROBADO)

    assert error.value.codigo == "monto_no_positivo"


def test_evento_pago_prima_registrado_lleva_oferta_y_estado():
    pago = Pago.registrar_prima(uuid4(), uuid4(), Decimal("100.00"), APROBADO)

    evento = pago_prima_registrado(pago)

    assert evento.tipo == "PagoPrimaRegistrado"
    assert evento.payload == {
        "pago_id": str(pago.id),
        "oferta_id": str(pago.oferta_id),
        "monto": "100.00",
        "estado": "APROBADO",
    }


async def test_el_stub_es_determinista_por_token_y_por_clave():
    stub = PasarelaStub()

    aprobado = await stub.cobrar("tok_visa", Decimal("1"), "cobro-prima:x")
    repetido = await stub.cobrar("tok_visa", Decimal("1"), "cobro-prima:x")
    rechazado = await stub.cobrar(TOKEN_RECHAZO, Decimal("1"), "cobro-prima:y")

    assert aprobado.estado is EstadoPago.APROBADO
    assert aprobado.referencia_externa == repetido.referencia_externa
    assert rechazado.estado is EstadoPago.RECHAZADO
    assert rechazado.referencia_externa != aprobado.referencia_externa
