from uuid import uuid4

import pytest

from app.domain.errores import ProductoNoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import EstadoSolicitud, SolicitudCotizacion

from .dobles import CatalogoEnMemoria

DATOS_VALIDOS = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}


def _crear(catalogo, **overrides):
    datos_riesgo = overrides.pop("datos_riesgo", DATOS_VALIDOS)
    producto = overrides.pop("producto", "soat-motocicleta")
    return SolicitudCotizacion.crear(
        idempotency_key="clave-0001",
        usuario_id=uuid4(),
        socio_id=uuid4(),
        consentimiento_id=uuid4(),
        producto=producto,
        canal="app-socio",
        datos_riesgo=datos_riesgo,
        catalogo=catalogo,
    )


def test_crear_solicitud_valida():
    solicitud = _crear(CatalogoEnMemoria())

    assert solicitud.estado.value == "recibida"
    assert solicitud.producto == "soat-motocicleta"
    assert solicitud.datos_riesgo == DATOS_VALIDOS


def test_producto_inexistente_lanza_producto_no_encontrado():
    with pytest.raises(ProductoNoEncontrado) as exc:
        _crear(CatalogoEnMemoria(), producto="producto-inexistente")

    assert exc.value.codigo == "producto_no_encontrado"


def test_dato_riesgo_fuera_de_rango_nombra_campo_y_rango():
    datos = {**DATOS_VALIDOS, "cilindraje_cc": 5000}

    with pytest.raises(ReglaDeNegocioViolada) as exc:
        _crear(CatalogoEnMemoria(), datos_riesgo=datos)

    assert exc.value.codigo == "dato_riesgo_fuera_de_rango"
    assert "cilindraje_cc" in exc.value.mensaje


def test_dato_riesgo_faltante():
    datos = {k: v for k, v in DATOS_VALIDOS.items() if k != "modelo_anio"}

    with pytest.raises(ReglaDeNegocioViolada) as exc:
        _crear(CatalogoEnMemoria(), datos_riesgo=datos)

    assert exc.value.codigo == "dato_riesgo_faltante"
    assert "modelo_anio" in exc.value.mensaje


def test_marcar_cotizada_en_estado_invalido_lanza_transicion_invalida():
    solicitud = _crear(CatalogoEnMemoria())
    solicitud.marcar_cotizada()

    with pytest.raises(TransicionInvalida):
        solicitud.marcar_cotizada()

    assert solicitud.estado is EstadoSolicitud.COTIZADA
