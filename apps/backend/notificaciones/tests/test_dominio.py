from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import CanalNotificacion, DispositivoPush, EstadoNotificacion, Notificacion


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
