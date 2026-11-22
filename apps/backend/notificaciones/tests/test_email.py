from uuid import uuid4

import httpx
import jwt
import pytest

from app.application.manejadores import CanalEmail, manejar_evento
from app.config import Settings
from app.domain.errores import ServicioExternoNoDisponible
from app.domain.eventos import EventoBus
from app.domain.modelos import DispositivoPush
from app.infrastructure.email_ses import EnviadorSES
from app.infrastructure.email_stub import EmailStub
from app.infrastructure.identidad_http import ResolutorIdentidadHTTP
from app.main import construir_email
from tests.dobles import EmailDoble, ResolutorDoble


def _evento(tipo="PolizaEmitida", usuario=None, **extras):
    return EventoBus.desde_mensaje(
        {
            "evento_id": str(uuid4()),
            "tipo": tipo,
            "agregado_id": str(uuid4()),
            "ocurrido_en": "2026-11-06T12:00:00+00:00",
            "origen": "ms_polizas",
            "payload": {"usuario_id": str(usuario or uuid4()), "numero": "POL-1", **extras},
        }
    )


def _por_canal(almacen, canal):
    return [n for n in almacen.notificaciones.values() if n.canal == canal]


async def test_evento_de_negocio_envia_correo_con_el_texto_de_la_notificacion(uow, almacen, push):
    usuario = uuid4()
    email = EmailDoble()
    canal = CanalEmail(email, ResolutorDoble({usuario: "ana@solventa.co"}))

    await manejar_evento(uow, push, _evento(usuario=usuario, fin_vigencia="2027-01-01"), canal)

    assert email.enviados == [
        (
            "ana@solventa.co",
            "Tu póliza fue emitida",
            "La póliza POL-1 está vigente hasta 2027-01-01.\n\n-- Equipo Solventa",
        )
    ]
    (correo,) = _por_canal(almacen, "email")
    assert correo.estado == "enviada"
    assert correo.proveedor_id == "email-doble-1"


async def test_el_correo_no_depende_de_que_el_usuario_tenga_dispositivo(uow, almacen, push):
    usuario = uuid4()
    canal = CanalEmail(EmailDoble(), ResolutorDoble({usuario: "ana@solventa.co"}))

    await manejar_evento(uow, push, _evento(usuario=usuario), canal)

    assert [n.estado for n in _por_canal(almacen, "push")] == ["fallida"]
    assert [n.estado for n in _por_canal(almacen, "email")] == ["enviada"]


async def test_es_idempotente_por_evento_y_canal_email(uow, almacen, push):
    usuario = uuid4()
    email = EmailDoble()
    canal = CanalEmail(email, ResolutorDoble({usuario: "ana@solventa.co"}))
    evento = _evento(usuario=usuario)

    await manejar_evento(uow, push, evento, canal)
    await manejar_evento(uow, push, evento, canal)

    assert len(email.enviados) == 1
    assert len(_por_canal(almacen, "email")) == 1


async def test_sin_canal_de_correo_no_crea_notificacion_email(uow, almacen, push):
    await manejar_evento(uow, push, _evento())

    assert _por_canal(almacen, "email") == []


async def test_usuario_sin_correo_deja_el_email_fallido(uow, almacen, push):
    email = EmailDoble()

    await manejar_evento(uow, push, _evento(), CanalEmail(email, ResolutorDoble()))

    assert email.enviados == []
    assert [n.estado for n in _por_canal(almacen, "email")] == ["fallida"]


@pytest.mark.parametrize(
    "canal",
    [
        CanalEmail(EmailDoble(fallar=True), ResolutorDoble()),
        CanalEmail(EmailDoble(), ResolutorDoble(fallar=True)),
    ],
)
async def test_proveedor_o_identidad_caidos_dejan_el_email_fallido(uow, almacen, push, canal):
    usuario = uuid4()
    canal.resolutor.correos[usuario] = "ana@solventa.co"

    await manejar_evento(uow, push, _evento(usuario=usuario), canal)

    assert [n.estado for n in _por_canal(almacen, "email")] == ["fallida"]


async def test_un_push_caido_no_impide_el_correo(uow, almacen):
    from app.infrastructure.push_stub import PushStub

    usuario = uuid4()
    dispositivo = DispositivoPush.registrar(usuario, "android", "t")
    almacen.dispositivos[dispositivo.dispositivo_id] = dispositivo
    email = EmailDoble()
    canal = CanalEmail(email, ResolutorDoble({usuario: "ana@solventa.co"}))

    await manejar_evento(uow, PushStub(fallar=True), _evento(usuario=usuario), canal)

    assert len(email.enviados) == 1


async def test_un_error_inesperado_del_correo_no_se_propaga(uow, almacen, push):
    class Roto:
        async def correo_de(self, usuario_id):
            raise RuntimeError("boom")

    notificacion = await manejar_evento(uow, push, _evento(), CanalEmail(EmailDoble(), Roto()))

    assert notificacion is not None


async def test_la_bandeja_de_la_app_no_lista_correos(uow, almacen, push):
    from app.application.casos_uso import listar_notificaciones

    usuario = uuid4()
    canal = CanalEmail(EmailDoble(), ResolutorDoble({usuario: "ana@solventa.co"}))
    await manejar_evento(uow, push, _evento(usuario=usuario), canal)

    assert {n.canal for n in await listar_notificaciones(uow, usuario, 10)} == {"push"}


# --- adaptadores -----------------------------------------------------------


async def test_email_stub_devuelve_id_y_puede_fallar():
    assert (await EmailStub().enviar("a@b.co", "x", "y")).startswith("stub-email-")
    with pytest.raises(ServicioExternoNoDisponible):
        await EmailStub(fallar=True).enviar("a@b.co", "x", "y")


async def test_ses_arma_la_peticion_y_devuelve_el_message_id():
    class Cliente:
        def send_email(self, **kwargs):
            self.kwargs = kwargs
            return {"MessageId": "ses-1"}

    cliente = Cliente()
    ses = EnviadorSES("us-east-1", "no-reply@solventa.co", "conf")
    ses._cliente = cliente

    assert await ses.enviar("ana@solventa.co", "Asunto", "Cuerpo") == "ses-1"
    assert cliente.kwargs["FromEmailAddress"] == "no-reply@solventa.co"
    assert cliente.kwargs["Destination"] == {"ToAddresses": ["ana@solventa.co"]}
    assert cliente.kwargs["Content"]["Simple"]["Subject"]["Data"] == "Asunto"
    assert cliente.kwargs["ConfigurationSetName"] == "conf"
    assert "Html" not in cliente.kwargs["Content"]["Simple"]["Body"]


async def test_ses_incluye_el_html_cuando_se_provee():
    class Cliente:
        def send_email(self, **kwargs):
            self.kwargs = kwargs
            return {"MessageId": "ses-1"}

    cliente = Cliente()
    ses = EnviadorSES("us-east-1", "no-reply@solventa.co")
    ses._cliente = cliente

    await ses.enviar("ana@solventa.co", "Asunto", "Cuerpo", "<p>Cuerpo</p>")

    assert cliente.kwargs["Content"]["Simple"]["Body"]["Html"]["Data"] == "<p>Cuerpo</p>"


async def test_ses_traduce_los_errores_del_proveedor():
    from botocore.exceptions import ClientError

    class Cliente:
        def send_email(self, **kwargs):
            raise ClientError({"Error": {"Code": "MessageRejected", "Message": "x"}}, "SendEmail")

    ses = EnviadorSES("us-east-1", "no-reply@solventa.co")
    ses._cliente = Cliente()

    with pytest.raises(ServicioExternoNoDisponible):
        await ses.enviar("ana@solventa.co", "a", "b")


def _identidad(handler):
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://identidad")
    return ResolutorIdentidadHTTP("http://identidad", "secreto", http)


async def test_identidad_pide_el_contacto_con_token_de_servicio():
    usuario = uuid4()
    visto = {}

    def handler(request):
        visto["ruta"] = request.url.path
        visto["token"] = request.headers["authorization"].removeprefix("Bearer ")
        return httpx.Response(200, json={"email": " ana@solventa.co "})

    assert await _identidad(handler).correo_de(usuario) == "ana@solventa.co"
    assert visto["ruta"] == f"/v1/usuarios/{usuario}/contacto"
    claims = jwt.decode(visto["token"], "secreto", algorithms=["HS256"])
    assert (claims["sub"], claims["rol"], claims["typ"]) == ("notificaciones", "servicio", "access")


async def test_identidad_404_es_sin_correo_y_otros_errores_son_indisponibilidad():
    assert await _identidad(lambda r: httpx.Response(404)).correo_de(uuid4()) is None
    with pytest.raises(ServicioExternoNoDisponible):
        await _identidad(lambda r: httpx.Response(500)).correo_de(uuid4())

    def caido(request):
        raise httpx.ConnectError("sin red")

    with pytest.raises(ServicioExternoNoDisponible):
        await _identidad(caido).correo_de(uuid4())


# --- wiring ----------------------------------------------------------------


def test_correo_apagado_por_defecto():
    assert construir_email(Settings(_env_file=None)) is None


def test_ses_exige_remitente_identidad_y_secreto():
    with pytest.raises(RuntimeError, match="EMAIL_REMITENTE"):
        construir_email(Settings(_env_file=None, email_proveedor="ses"))
    canal = construir_email(
        Settings(
            _env_file=None,
            email_proveedor="ses",
            email_remitente="no-reply@solventa.co",
            ms_identidad_url="http://identidad",
            solventa_token_secret="s",
        )
    )
    assert isinstance(canal.enviador, EnviadorSES)


def test_stub_no_se_permite_con_msk_y_proveedor_desconocido_falla():
    with pytest.raises(RuntimeError, match="MSK"):
        construir_email(Settings(_env_file=None, email_proveedor="stub", msk_bootstrap_brokers="b:9098"))
    with pytest.raises(RuntimeError, match="no soportado"):
        construir_email(Settings(_env_file=None, email_proveedor="sendgrid"))
    assert isinstance(construir_email(Settings(_env_file=None, email_proveedor="stub")).enviador, EmailStub)
