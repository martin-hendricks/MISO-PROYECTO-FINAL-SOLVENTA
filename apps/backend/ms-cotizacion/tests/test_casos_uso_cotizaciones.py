from uuid import uuid4

import pytest

from app.application import casos_uso_cotizaciones as casos_uso
from app.domain.errores import ProductoNoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import SolicitudCotizacion

DATOS_VALIDOS = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}


async def _recibir(uow, catalogo, idempotency_key="clave-0001", **overrides):
    return await casos_uso.recibir_solicitud(
        uow,
        catalogo,
        idempotency_key,
        overrides.get("usuario_id", uuid4()),
        overrides.get("socio_id", uuid4()),
        overrides.get("consentimiento_id", uuid4()),
        overrides.get("producto", "soat-motocicleta"),
        overrides.get("canal", "app-socio"),
        overrides.get("datos_riesgo", DATOS_VALIDOS),
    )


async def test_recibir_solicitud_publica_evento_en_outbox(uow, almacen, catalogo):
    resultado = await _recibir(uow, catalogo)

    assert resultado.creada
    assert [e.tipo for e in almacen.eventos] == ["SolicitudCotizacionRecibida"]


async def test_reintento_con_la_misma_clave_no_duplica(uow, almacen, catalogo):
    primero = await _recibir(uow, catalogo)
    segundo = await _recibir(uow, catalogo)

    assert not segundo.creada
    assert segundo.solicitud.id == primero.solicitud.id
    assert len(almacen.solicitudes) == 1
    assert len(almacen.eventos) == 1


async def test_carrera_de_idempotencia_devuelve_el_ganador(uow, almacen, catalogo):
    ganador = SolicitudCotizacion.crear(
        "clave-0001", uuid4(), uuid4(), uuid4(), "soat-motocicleta", "app-socio", DATOS_VALIDOS, catalogo
    )
    almacen.chocar_en_proximo_commit = ganador

    resultado = await _recibir(uow, catalogo)

    assert not resultado.creada
    assert resultado.solicitud.id == ganador.id
    assert almacen.eventos == []


async def test_producto_inexistente_no_genera_cotizacion_id(uow, almacen, catalogo):
    with pytest.raises(ProductoNoEncontrado):
        await _recibir(uow, catalogo, idempotency_key="clave-0002", producto="producto-inexistente")

    assert almacen.solicitudes == {}


async def test_calcular_prima_solicitud_sin_regla_configurada_lanza_regla_de_negocio(uow):
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        await casos_uso.calcular_prima_solicitud(uow, "producto-sin-regla", {})

    assert exc.value.codigo == "regla_rating_no_configurada"


async def test_calcular_prima_solicitud_devuelve_regla_y_resultado(uow):
    regla, resultado = await casos_uso.calcular_prima_solicitud(
        uow, "soat-motocicleta", {"cilindraje_cc": 150}
    )

    assert regla.producto == "soat-motocicleta"
    assert resultado.prima_total == resultado.prima_neta + resultado.gastos_expedicion
