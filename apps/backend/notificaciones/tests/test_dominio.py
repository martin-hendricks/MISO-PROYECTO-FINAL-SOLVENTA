from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import (
    CanalNotificacion,
    Difusion,
    DispositivoPush,
    EstadoNotificacion,
    Notificacion,
    resolver_audiencia,
)


def _notificacion(**cambios):
    datos = {
        "usuario_id": uuid4(),
        "evento_origen_id": uuid4(),
        "canal": "push",
        "tipo": "poliza_emitida",
        "titulo": "Tu póliza está lista",
        "cuerpo": "Ya puedes consultar tu póliza.",
    }
    datos.update(cambios)
    return Notificacion.crear(**datos)


def test_titulo_y_cuerpo_respetan_el_tope_y_destino_exige_poliza():
    with pytest.raises(ReglaDeNegocioViolada) as titulo:
        _notificacion(titulo="x" * 81)
    assert titulo.value.codigo == "titulo_largo"
    with pytest.raises(ReglaDeNegocioViolada) as cuerpo:
        _notificacion(cuerpo="y" * 241)
    assert cuerpo.value.codigo == "cuerpo_largo"

    sin_poliza = _notificacion(destino="poliza-detalle")
    assert sin_poliza.destino == "inicio"
    assert sin_poliza.poliza is None
    con_poliza = _notificacion(destino="poliza-detalle", poliza=" POL-1 ")
    assert con_poliza.destino == "poliza-detalle"
    assert con_poliza.poliza == "POL-1"


def test_audiencia_deduplica_y_rechaza_vacia_o_demasiado_larga():
    uno, dos = uuid4(), uuid4()
    assert resolver_audiencia("todos", [uno]) == ("todos", [])
    assert resolver_audiencia("usuarios", [uno, uno, dos])[1] == [uno, dos]
    with pytest.raises(ReglaDeNegocioViolada) as vacia:
        resolver_audiencia("usuarios", [])
    assert vacia.value.codigo == "audiencia_vacia"
    with pytest.raises(ReglaDeNegocioViolada) as larga:
        resolver_audiencia("usuarios", [uuid4() for _ in range(501)])
    assert larga.value.codigo == "audiencia_larga"
    with pytest.raises(ReglaDeNegocioViolada) as invalida:
        resolver_audiencia("todos-los-clientes", None)
    assert invalida.value.codigo == "audiencia_invalida"


def test_difusion_exige_que_los_totales_sumen_los_destinatarios():
    difusion = Difusion.crear(uuid4(), "Aviso", "Cuerpo", "usuarios", 2, poliza="POL-1")
    assert difusion.poliza == "POL-1"
    difusion.registrar_totales(1, 0, 1)
    with pytest.raises(ReglaDeNegocioViolada) as error:
        difusion.registrar_totales(1, 0, 0)
    assert error.value.codigo == "totales_inconsistentes"


def test_crear_notificacion_queda_pendiente_y_normaliza():
    notificacion = _notificacion(canal="PUSH", titulo="  Hola  ", destino="  token-1  ")

    assert notificacion.estado == EstadoNotificacion.PENDIENTE
    assert notificacion.canal == CanalNotificacion.PUSH
    assert notificacion.titulo == "Hola"
    assert notificacion.destino == "token-1"
    assert notificacion.enviada_en is None
    assert notificacion.leida_en is None


@pytest.mark.parametrize(
    ("cambios", "codigo"),
    [
        ({"canal": "sms"}, "canal_invalido"),
        ({"tipo": "  "}, "tipo_vacio"),
        ({"titulo": "  "}, "titulo_vacio"),
        ({"cuerpo": "  "}, "cuerpo_vacio"),
    ],
)
def test_crear_notificacion_valida_reglas(cambios, codigo):
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        _notificacion(**cambios)
    assert exc.value.codigo == codigo


def test_marcar_enviada_registra_fecha_y_proveedor():
    notificacion = _notificacion()

    notificacion.marcar_enviada("proveedor-1")

    assert notificacion.estado == EstadoNotificacion.ENVIADA
    assert notificacion.proveedor_id == "proveedor-1"
    assert notificacion.enviada_en is not None


def test_marcar_enviada_es_idempotente():
    notificacion = _notificacion()
    notificacion.marcar_enviada("proveedor-1")
    primera_fecha = notificacion.enviada_en

    notificacion.marcar_enviada("proveedor-2")

    assert notificacion.enviada_en == primera_fecha
    assert notificacion.proveedor_id == "proveedor-1"


def test_marcar_fallida_solo_antes_de_enviar():
    notificacion = _notificacion()
    notificacion.marcar_fallida()
    assert notificacion.estado == EstadoNotificacion.FALLIDA

    notificacion.marcar_enviada("proveedor-1")
    with pytest.raises(TransicionInvalida):
        notificacion.marcar_fallida()


def test_marcar_leida_es_idempotente_y_conserva_la_fecha():
    notificacion = _notificacion()
    momento = datetime.now(UTC)

    notificacion.marcar_leida(momento)
    notificacion.marcar_leida(momento + timedelta(hours=1))

    assert notificacion.estado == EstadoNotificacion.LEIDA
    assert notificacion.leida_en == momento


def test_no_se_puede_enviar_una_notificacion_leida():
    notificacion = _notificacion()
    notificacion.marcar_leida()

    with pytest.raises(TransicionInvalida):
        notificacion.marcar_enviada("proveedor-1")


def test_registrar_dispositivo_valida_plataforma_y_token():
    usuario = uuid4()

    dispositivo = DispositivoPush.registrar(usuario, " ANDROID ", " token-1 ")

    assert dispositivo.plataforma == "android"
    assert dispositivo.token == "token-1"
    assert dispositivo.activo

    with pytest.raises(ReglaDeNegocioViolada) as exc:
        DispositivoPush.registrar(usuario, "windows", "token-1")
    assert exc.value.codigo == "plataforma_invalida"

    with pytest.raises(ReglaDeNegocioViolada) as exc:
        DispositivoPush.registrar(usuario, "ios", "  ")
    assert exc.value.codigo == "token_vacio"


def test_dispositivo_se_desactiva_y_reactiva():
    dispositivo = DispositivoPush.registrar(uuid4(), "ios", "token-1")

    dispositivo.desactivar()
    assert not dispositivo.activo

    dispositivo.activar()
    assert dispositivo.activo


def test_no_encontrado_tiene_codigo():
    assert NoEncontrado("x").codigo == "no_encontrado"
