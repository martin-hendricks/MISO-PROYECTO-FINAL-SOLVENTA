from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.domain.modelos import EstadoSolicitud, SolicitudCotizacion
from app.domain.oferta import Oferta
from app.domain.rating import ReglaRating, ResultadoPrima
from app.domain.riesgo import FactorRiesgo, OrigenFactorRiesgo

SOLICITUD = SolicitudCotizacion(
    id=uuid4(),
    idempotency_key="clave-0001",
    usuario_id=uuid4(),
    socio_id=uuid4(),
    consentimiento_id=uuid4(),
    producto="soat-motocicleta",
    canal="app-socio",
    datos_riesgo={"cilindraje_cc": 150},
    estado=EstadoSolicitud.RECIBIDA,
    creada_en=datetime.now(UTC),
)
REGLA = ReglaRating(id=uuid4(), producto="soat-motocicleta", version="0001", formula={})
RESULTADO = ResultadoPrima(prima_neta=Decimal("120000.00"), gastos_expedicion=Decimal("8500.00"), moneda="COP")
FACTOR = FactorRiesgo(valor=Decimal("1.0"), origen=OrigenFactorRiesgo.REAL)


def test_oferta_emitir_calcula_prima_como_neta_mas_gastos():
    oferta = Oferta.emitir(SOLICITUD, REGLA, RESULTADO, FACTOR, ["muerte"], timedelta(minutes=60))

    assert oferta.prima == RESULTADO.prima_neta + RESULTADO.gastos_expedicion


def test_oferta_vigente_antes_de_vencer():
    oferta = Oferta.emitir(SOLICITUD, REGLA, RESULTADO, FACTOR, ["muerte"], timedelta(minutes=60))

    assert oferta.vigente(ahora=oferta.vence_en - timedelta(seconds=1))


def test_oferta_no_vigente_despues_de_vencer():
    oferta = Oferta.emitir(SOLICITUD, REGLA, RESULTADO, FACTOR, ["muerte"], timedelta(minutes=60))

    assert not oferta.vigente(ahora=oferta.vence_en + timedelta(seconds=1))
