from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import DispositivoPush, Notificacion
from app.infrastructure.push_stub import PushStub
from tests.dobles import PushDoble, sembrar_notificaciones


def _datos_notificacion(usuario_id, evento_origen_id=None, canal="push", **cambios):
    datos = {
        "usuario_id": usuario_id,
        "evento_origen_id": evento_origen_id or uuid4(),
        "canal": canal,
        "tipo": "poliza_emitida",
        "titulo": "Tu póliza está lista",
        "cuerpo": "Ya puedes consultar tu póliza.",
    }
    datos.update(cambios)
    return datos


async def test_registrar_dispositivo_es_upsert_idempotente(uow, almacen):
    usuario = uuid4()

    primero = await casos_uso.registrar_dispositivo(uow, usuario, "android", "token-1")
    segundo = await casos_uso.registrar_dispositivo(uow, usuario, "android", "token-1")

    assert primero.creado
    assert not segundo.creado
    assert segundo.dispositivo.dispositivo_id == primero.dispositivo.dispositivo_id
    assert len(almacen.dispositivos) == 1


async def test_registrar_dispositivo_reactiva_uno_desactivado(uow, almacen):
    usuario = uuid4()
    creado = await casos_uso.registrar_dispositivo(uow, usuario, "ios", "token-1")
    await casos_uso.desactivar_dispositivo(uow, usuario, creado.dispositivo.dispositivo_id)
    assert not almacen.dispositivos[creado.dispositivo.dispositivo_id].activo

    reactivado = await casos_uso.registrar_dispositivo(uow, usuario, "ios", "token-1")

    assert not reactivado.creado
    assert reactivado.dispositivo.dispositivo_id == creado.dispositivo.dispositivo_id
    assert reactivado.dispositivo.activo


async def test_dispositivo_registrado_delega_atributos_del_dispositivo(uow, almacen):
    """__getattr__: DispositivoRegistrado se puede usar como si fuera
    directamente el DispositivoPush (p. ej. desde un schema de salida que
    lee .token/.plataforma sin saber que es un wrapper)."""
    usuario = uuid4()
    resultado = await casos_uso.registrar_dispositivo(uow, usuario, "android", "token-1")

    assert resultado.token == "token-1"
    assert resultado.plataforma == "android"
    assert resultado.usuario_id == usuario


async def test_registrar_dispositivo_ganador_de_la_carrera_se_recarga(uow, almacen):
    """Dos requests simultáneos intentan registrar el mismo (usuario_id,
    token): el que pierde la carrera en confirmar() debe recargar y
    devolver el que sí quedó persistido, no lanzar."""
    usuario = uuid4()
    ganador = DispositivoPush.registrar(usuario, "android", "token-1")
    almacen.chocar_dispositivo = ganador

    resultado = await casos_uso.registrar_dispositivo(uow, usuario, "android", "token-1")

    assert not resultado.creado
    assert resultado.dispositivo.dispositivo_id == ganador.dispositivo_id
    assert almacen.dispositivos[ganador.dispositivo_id] is ganador


async def test_desactivar_dispositivo_ajeno_es_no_encontrado(uow):
    creado = await casos_uso.registrar_dispositivo(uow, uuid4(), "android", "token-1")

    with pytest.raises(NoEncontrado):
        await casos_uso.desactivar_dispositivo(uow, uuid4(), creado.dispositivo.dispositivo_id)


async def test_listar_solo_las_del_usuario_con_orden_y_cursor(uow, almacen):
    usuario = uuid4()
    otro = uuid4()
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    notificaciones = [
        Notificacion.crear(**_datos_notificacion(usuario, ahora=base)),
        Notificacion.crear(**_datos_notificacion(usuario, ahora=base + timedelta(minutes=1))),
        Notificacion.crear(**_datos_notificacion(usuario, ahora=base + timedelta(minutes=2))),
        Notificacion.crear(**_datos_notificacion(otro, ahora=base + timedelta(minutes=3))),
    ]
    sembrar_notificaciones(almacen, notificaciones)

    recientes = await casos_uso.listar_notificaciones(uow, usuario, 2)
    anteriores = await casos_uso.listar_notificaciones(
        uow, usuario, 20, antes_de=base + timedelta(minutes=2)
    )

    assert [n.notificacion_id for n in recientes] == [
        notificaciones[2].notificacion_id,
        notificaciones[1].notificacion_id,
    ]
    assert [n.notificacion_id for n in anteriores] == [
        notificaciones[1].notificacion_id,
        notificaciones[0].notificacion_id,
    ]


async def test_consultar_notificacion_ajena_es_no_encontrado(uow, almacen):
    ajena = Notificacion.crear(**_datos_notificacion(uuid4()))
    sembrar_notificaciones(almacen, [ajena])

    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_notificacion(uow, uuid4(), ajena.notificacion_id)


async def test_marcar_leida_propia_es_idempotente_y_ajena_no_existe(uow, almacen):
    usuario = uuid4()
    propia = Notificacion.crear(**_datos_notificacion(usuario))
    sembrar_notificaciones(almacen, [propia])

    primera = await casos_uso.marcar_leida(uow, usuario, propia.notificacion_id)
    segunda = await casos_uso.marcar_leida(uow, usuario, propia.notificacion_id)

    assert primera.estado == "leida"
    assert segunda.leida_en == primera.leida_en
    assert almacen.notificaciones[propia.notificacion_id].estado == "leida"

    with pytest.raises(NoEncontrado):
        await casos_uso.marcar_leida(uow, uuid4(), propia.notificacion_id)


async def test_crear_notificacion_es_idempotente_por_evento_y_canal(uow, almacen):
    usuario = uuid4()
    evento = uuid4()

    primera = await casos_uso.crear_notificacion(
        uow, usuario, evento, "push", "tipo", "Título", "Cuerpo"
    )
    reintento = await casos_uso.crear_notificacion(
        uow, usuario, evento, "push", "tipo", "Otro título", "Otro cuerpo"
    )
    otro_canal = await casos_uso.crear_notificacion(
        uow, usuario, evento, "email", "tipo", "Título", "Cuerpo", "correo@ejemplo.com"
    )

    assert reintento.notificacion_id == primera.notificacion_id
    assert reintento.titulo == "Título"
    assert otro_canal.notificacion_id != primera.notificacion_id
    assert len(almacen.notificaciones) == 2


async def test_crear_notificacion_sin_evento_no_deduplica(uow, almacen):
    usuario = uuid4()

    primera = await casos_uso.crear_notificacion(
        uow, usuario, None, "email", "tipo", "Título", "Cuerpo", "a@b.co"
    )
    segunda = await casos_uso.crear_notificacion(
        uow, usuario, None, "email", "tipo", "Título", "Cuerpo", "a@b.co"
    )

    assert primera.notificacion_id != segunda.notificacion_id
    assert len(almacen.notificaciones) == 2


async def test_despachar_envia_a_dispositivos_activos_y_marca_enviada(uow, almacen):
    usuario = uuid4()
    activo_1 = DispositivoPush.registrar(usuario, "android", "token-1")
    activo_2 = DispositivoPush.registrar(usuario, "ios", "token-2")
    inactivo = DispositivoPush.registrar(usuario, "android", "token-3")
    inactivo.desactivar()
    for dispositivo in (activo_1, activo_2, inactivo):
        almacen.dispositivos[dispositivo.dispositivo_id] = dispositivo
    notificacion = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )
    push = PushDoble()

    enviadas = await casos_uso.despachar_pendientes(uow, push)

    assert enviadas == 1
    assert push.llamadas == [
        ([activo_1.dispositivo_id, activo_2.dispositivo_id], notificacion.notificacion_id)
    ]
    persistida = almacen.notificaciones[notificacion.notificacion_id]
    assert persistida.estado == "enviada"
    assert persistida.enviada_en is not None
    assert persistida.proveedor_id.startswith("doble-")


async def test_despachar_con_fallo_marca_fallida(uow, almacen):
    usuario = uuid4()
    almacen.dispositivos[uuid4()] = DispositivoPush.registrar(usuario, "android", "token-1")
    notificacion = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )

    enviadas = await casos_uso.despachar_pendientes(uow, PushDoble(fallar=True))

    assert enviadas == 0
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "fallida"


async def test_despachar_con_push_stub_configurado_para_fallar(uow, almacen):
    usuario = uuid4()
    almacen.dispositivos[uuid4()] = DispositivoPush.registrar(usuario, "android", "token-1")
    notificacion = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )

    enviadas = await casos_uso.despachar_pendientes(uow, PushStub(fallar=True))

    assert enviadas == 0
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "fallida"


async def test_despachar_sin_dispositivos_marca_fallida(uow, almacen):
    notificacion = await casos_uso.crear_notificacion(
        uow, uuid4(), uuid4(), "push", "tipo", "Título", "Cuerpo"
    )

    enviadas = await casos_uso.despachar_pendientes(uow, PushDoble())

    assert enviadas == 0
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "fallida"


async def test_despachar_no_reenvia_una_ya_enviada(uow, almacen):
    usuario = uuid4()
    almacen.dispositivos[uuid4()] = DispositivoPush.registrar(usuario, "android", "token-1")
    notificacion = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )
    push = PushDoble()

    assert await casos_uso.despachar_pendientes(uow, push) == 1
    assert await casos_uso.despachar_pendientes(uow, push) == 0

    assert len(push.llamadas) == 1
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "enviada"


async def test_token_invalido_desactiva_el_dispositivo_sin_reintento(uow, almacen):
    usuario = uuid4()
    dispositivo = DispositivoPush.registrar(usuario, "android", "token-malo")
    almacen.dispositivos[dispositivo.dispositivo_id] = dispositivo
    notificacion = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )
    push = PushDoble()
    push.tokens_invalidos = {"token-malo"}

    assert await casos_uso.despachar_notificacion(uow, push, notificacion.notificacion_id) is False
    assert almacen.dispositivos[dispositivo.dispositivo_id].activo is False
    assert len(push.llamadas) == 1
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "fallida"


async def test_despachar_sin_proveedores_marca_fallida(uow, almacen):
    """enviar_a_usuario() puede devolver una lista vacía sin lanzar (p. ej.
    todos los proveedores de push rechazaron el token) -- distinto del
    caso 'sin dispositivos', que ni siquiera llega a llamar al push."""

    class _PushSinProveedores:
        async def enviar_a_usuario(self, dispositivos, notificacion):
            return []

    usuario = uuid4()
    almacen.dispositivos[uuid4()] = DispositivoPush.registrar(usuario, "android", "token-1")
    notificacion = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )

    enviadas = await casos_uso.despachar_pendientes(uow, _PushSinProveedores())

    assert enviadas == 0
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "fallida"


async def test_crear_notificacion_ganadora_de_la_carrera_se_recarga(uow, almacen):
    """Dos eventos simultáneos para el mismo (evento_origen_id, canal): el
    que pierde la carrera en confirmar() debe recargar y devolver la
    notificación que sí quedó persistida, no lanzar."""
    usuario = uuid4()
    evento = uuid4()
    ganadora = Notificacion.crear(
        usuario_id=usuario,
        evento_origen_id=evento,
        canal="push",
        tipo="tipo",
        titulo="Título ganador",
        cuerpo="Cuerpo ganador",
    )
    almacen.chocar_notificacion = ganadora

    resultado = await casos_uso.crear_notificacion(
        uow, usuario, evento, "push", "tipo", "Título", "Cuerpo"
    )

    assert resultado.notificacion_id == ganadora.notificacion_id
    assert resultado.titulo == "Título ganador"
    assert almacen.notificaciones[ganadora.notificacion_id] is ganadora


async def test_despachar_notificacion_no_pendiente_devuelve_false(uow, almacen):
    usuario = uuid4()
    notificacion = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )
    almacen.notificaciones[notificacion.notificacion_id].marcar_enviada("proveedor-x")

    enviada = await casos_uso.despachar_notificacion(uow, PushDoble(), notificacion.notificacion_id)

    assert enviada is False


async def test_despachar_notificacion_inexistente_devuelve_false(uow):
    enviada = await casos_uso.despachar_notificacion(uow, PushDoble(), uuid4())

    assert enviada is False


async def test_despachar_filtra_por_usuario_cuando_se_indica(uow, almacen):
    usuario = uuid4()
    otro = uuid4()
    for duenio, token in ((usuario, "token-1"), (otro, "token-2")):
        almacen.dispositivos[uuid4()] = DispositivoPush.registrar(duenio, "android", token)
    propia = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )
    ajena = await casos_uso.crear_notificacion(
        uow, otro, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )

    assert await casos_uso.despachar_pendientes(uow, PushDoble(), usuario_id=usuario) == 1
    assert almacen.notificaciones[propia.notificacion_id].estado == "enviada"
    assert almacen.notificaciones[ajena.notificacion_id].estado == "pendiente"


async def test_despachar_ignora_canal_email(uow, almacen):
    usuario = uuid4()
    almacen.dispositivos[uuid4()] = DispositivoPush.registrar(usuario, "android", "token-1")
    email = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "email", "tipo", "Título", "Cuerpo", "a@b.co"
    )

    assert await casos_uso.despachar_pendientes(uow, PushDoble()) == 0
    assert almacen.notificaciones[email.notificacion_id].estado == "pendiente"


async def test_difundir_cuenta_enviadas_fallidas_y_sin_dispositivo(uow, almacen):
    con_token, sin_token, otro_con_token = uuid4(), uuid4(), uuid4()
    await casos_uso.registrar_dispositivo(uow, con_token, "android", "token-1")
    await casos_uso.registrar_dispositivo(uow, otro_con_token, "android", "token-2")
    push = PushDoble()

    resultado = await casos_uso.difundir(
        uow,
        push,
        uuid4(),
        "Aviso",
        "Cuerpo del aviso",
        "usuarios",
        [con_token, sin_token],
        "POL-1",
    )

    assert resultado.enviadas == 1
    assert resultado.fallidas == 0
    assert resultado.sin_dispositivo == 1
    assert len(push.llamadas) == 1
    creada = next(iter(almacen.notificaciones.values()))
    assert creada.tipo == "mensaje_operador"
    assert creada.difusion_id == resultado.difusion_id
    assert creada.poliza == "POL-1"
    assert creada.usuario_id == con_token
    assert almacen.difusiones[resultado.difusion_id].enviadas == 1

    a_todos = await casos_uso.difundir(
        uow, PushDoble(), uuid4(), "Aviso", "Cuerpo del aviso", "todos", None, None
    )
    assert a_todos.enviadas == 2
    assert a_todos.sin_dispositivo == 0


async def test_difundir_cuenta_proveedor_caido_como_fallida(uow, almacen):
    usuario = uuid4()
    await casos_uso.registrar_dispositivo(uow, usuario, "android", "token-1")
    resultado = await casos_uso.difundir(
        uow, PushDoble(fallar=True), uuid4(), "Aviso", "Cuerpo", "usuarios", [usuario], None
    )
    assert resultado.fallidas == 1
    assert resultado.enviadas == 0
    assert almacen.notificaciones[next(iter(almacen.notificaciones))].estado == "fallida"


async def test_difundir_rechaza_titulo_vacio_antes_de_escribir(uow, almacen):
    with pytest.raises(ReglaDeNegocioViolada):
        await casos_uso.difundir(uow, PushDoble(), uuid4(), "  ", "Cuerpo", "todos", None, None)
    assert almacen.difusiones == {}


async def test_un_dispositivo_invalido_no_anula_el_envio_del_otro(uow, almacen):
    usuario = uuid4()
    await casos_uso.registrar_dispositivo(uow, usuario, "android", "malo")
    await casos_uso.registrar_dispositivo(uow, usuario, "android", "bueno")
    push = PushDoble()
    push.tokens_invalidos = {"malo"}
    notificacion = await casos_uso.crear_notificacion(
        uow, usuario, uuid4(), "push", "tipo", "Título", "Cuerpo"
    )

    assert await casos_uso.despachar_notificacion(uow, push, notificacion.notificacion_id)
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "enviada"
    activos = [d for d in almacen.dispositivos.values() if d.activo]
    assert [d.token for d in activos] == ["bueno"]
