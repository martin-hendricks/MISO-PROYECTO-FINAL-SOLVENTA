from uuid import uuid4

from app.application.manejadores import CanalEmail, manejar_evento
from app.application.plantillas_email import renderizar
from tests.dobles import EmailDoble, ResolutorDoble


def _evento(tipo="PolizaEmitida", usuario=None, **extras):
    from app.domain.eventos import EventoBus

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


def test_cada_tipo_soportado_tiene_un_acento_de_color_propio():
    tipos = [
        "poliza_emitida",
        "poliza_renovada",
        "poliza_modificada",
        "poliza_cancelada",
        "consentimiento_pendiente",
    ]
    html_por_tipo = {tipo: renderizar(tipo, "Título", "Cuerpo") for tipo in tipos}

    colores = {html.split("border-top:4px solid ")[1].split(";")[0] for html in html_por_tipo.values()}
    assert len(colores) == len(tipos), "cada tipo debe distinguirse por color"


def test_tipo_desconocido_usa_un_color_por_defecto_en_vez_de_fallar():
    html = renderizar("tipo_futuro_no_mapeado", "Título", "Cuerpo")

    assert "Título" in html


def test_titulo_y_cuerpo_se_escapan_contra_html_injection():
    html = renderizar("poliza_emitida", "<script>alert(1)</script>", "a & b")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "a &amp; b" in html


def test_saltos_de_linea_en_el_cuerpo_se_convierten_a_br():
    html = renderizar("poliza_cancelada", "Título", "línea uno\nlínea dos")

    assert "línea uno<br>línea dos" in html


async def test_despachar_email_envia_tambien_el_html_renderizado(uow, almacen, push):
    usuario = uuid4()
    email = EmailDoble()
    canal = CanalEmail(email, ResolutorDoble({usuario: "ana@solventa.co"}))

    await manejar_evento(uow, push, _evento(usuario=usuario, fin_vigencia="2027-01-01"), canal)

    assert len(email.enviados_html) == 1
    html = email.enviados_html[0]
    assert html is not None
    assert "Tu póliza fue emitida" in html
    assert "POL-1" in html
