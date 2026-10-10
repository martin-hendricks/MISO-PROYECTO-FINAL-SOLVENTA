from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application import casos_uso_cotizaciones as casos_uso
from app.config import Settings
from app.domain.errores import NoEncontrado, ProductoNoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import SolicitudCotizacion
from app.domain.riesgo import OrigenFactorRiesgo
from app.infrastructure.adaptador_perfil_stub import AdaptadorPerfilRiesgoStub
from app.ports.persistencia import ClaveIdempotenciaDuplicada

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


async def _cotizar(uow, catalogo, adaptador, idempotency_key="clave-oferta-0001", **overrides):
    return await casos_uso.cotizar(
        uow,
        catalogo,
        adaptador,
        Settings(),
        idempotency_key,
        overrides.get("usuario_id", uuid4()),
        overrides.get("socio_id", uuid4()),
        overrides.get("consentimiento_id", uuid4()),
        overrides.get("producto", "soat-motocicleta"),
        overrides.get("canal", "app-socio"),
        overrides.get("datos_riesgo", DATOS_VALIDOS),
    )


async def test_cotizar_devuelve_oferta_en_el_mismo_flujo(uow, catalogo):
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=1, factor_fijo=Decimal("1.0"))

    resultado = await _cotizar(uow, catalogo, adaptador)

    assert resultado.creada
    assert resultado.oferta.solicitud_id == resultado.solicitud.id
    assert resultado.oferta.prima > 0
    assert resultado.oferta.moneda
    assert resultado.oferta.vence_en is not None


async def test_cotizar_publica_dos_eventos_en_outbox(uow, almacen, catalogo):
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=1, factor_fijo=Decimal("1.0"))

    await _cotizar(uow, catalogo, adaptador)

    assert [e.tipo for e in almacen.eventos] == ["SolicitudCotizacionRecibida", "OfertaEmitida"]


async def test_cotizar_con_factor_de_respaldo_completa_oferta(uow, catalogo):
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=0, fallar=True)

    resultado = await _cotizar(uow, catalogo, adaptador)

    assert resultado.creada
    assert resultado.oferta.factor_riesgo_origen == OrigenFactorRiesgo.RESPALDO


async def test_reconsultar_no_invoca_motor_de_rating_ni_adaptador(uow, catalogo, monkeypatch):
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=1, factor_fijo=Decimal("1.0"))
    registrada = await _cotizar(uow, catalogo, adaptador)

    def _falla_si_se_invoca(*args, **kwargs):
        raise AssertionError("reconsultar_oferta no debe invocar el motor de rating ni el adaptador")

    monkeypatch.setattr(casos_uso, "calcular_prima_solicitud", _falla_si_se_invoca)
    monkeypatch.setattr(casos_uso, "combinar_factor_riesgo", _falla_si_se_invoca)

    resultado = await casos_uso.reconsultar_oferta(uow, registrada.solicitud.id)

    assert resultado.consulta.oferta.id == registrada.oferta.id


async def test_reconsulta_repetida_es_estable(uow, catalogo):
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=1, factor_fijo=Decimal("1.0"))
    registrada = await _cotizar(uow, catalogo, adaptador)

    primera = await casos_uso.reconsultar_oferta(uow, registrada.solicitud.id)
    segunda = await casos_uso.reconsultar_oferta(uow, registrada.solicitud.id)

    assert primera == segunda


async def test_reconsultar_id_inexistente_lanza_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.reconsultar_oferta(uow, uuid4())


async def test_reconsultar_oferta_vencida_devuelve_vencida_true_con_precio_original(uow, catalogo, almacen):
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=1, factor_fijo=Decimal("1.0"))
    registrada = await _cotizar(uow, catalogo, adaptador)
    almacen.ofertas[registrada.oferta.id].vence_en = datetime.now(UTC) - timedelta(seconds=1)

    resultado = await casos_uso.reconsultar_oferta(uow, registrada.solicitud.id)

    assert resultado.consulta.vencida
    assert resultado.consulta.oferta.prima == registrada.oferta.prima


async def test_carrera_sin_ganador_visible_lanza_runtime_error(catalogo):
    class _RepoSolicitudesSinGanador:
        async def obtener_por_clave(self, _clave):
            return None

        async def agregar(self, _solicitud):
            pass

    class _Outbox:
        async def agregar(self, _evento):
            pass

    class _UowSinGanador:
        def __init__(self):
            self.solicitudes = _RepoSolicitudesSinGanador()
            self.outbox = _Outbox()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            pass

        async def confirmar(self):
            raise ClaveIdempotenciaDuplicada

    with pytest.raises(RuntimeError, match="Clave duplicada sin registro visible"):
        await _recibir(lambda: _UowSinGanador(), catalogo)


async def test_cotizar_con_carrera_de_idempotencia_devuelve_la_oferta_del_ganador(uow, almacen, catalogo):
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=1, factor_fijo=Decimal("1.0"))
    # chocar_en_proximo_commit simula que otra petición concurrente con la MISMA clave ya
    # ganó la carrera dentro de confirmar(): el check inicial de cotizar() (obtener_por_clave
    # antes del cálculo) no la ve todavía porque solo se escribe en el almacén justo cuando
    # confirmar() resuelve el choque, igual que en una carrera real entre dos peticiones.
    # El doble en memoria no persiste la oferta del ganador fantasma (a diferencia de
    # Postgres real, donde ambas filas se escriben en la misma transacción ganadora), así
    # que esta prueba ejercita el camino de relectura (líneas 159-162) sin poder afirmar
    # sobre el contenido de resultado.oferta.
    ganador_fantasma = SolicitudCotizacion.crear(
        "clave-carrera-0001", uuid4(), uuid4(), uuid4(), "soat-motocicleta", "app-socio", DATOS_VALIDOS, catalogo
    )
    almacen.chocar_en_proximo_commit = ganador_fantasma

    resultado = await _cotizar(uow, catalogo, adaptador, idempotency_key="clave-carrera-0001")

    assert not resultado.creada
    assert resultado.solicitud.id == ganador_fantasma.id
