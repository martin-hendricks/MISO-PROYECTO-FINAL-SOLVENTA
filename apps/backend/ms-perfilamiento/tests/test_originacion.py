from decimal import Decimal

import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import Originacion, OrigenOriginacion

CLIENTE = "cliente-1"


async def test_registrar_originacion_queda_pendiente_con_sus_valores(uow):
    creada = await casos_uso.registrar_originacion(uow, CLIENTE, Decimal("180000000"), 240, OrigenOriginacion.CLIENTE)

    pendiente = await casos_uso.consultar_originacion_pendiente(uow, CLIENTE)

    assert pendiente.id == creada.id
    assert (pendiente.valor, pendiente.plazo_meses, pendiente.origen) == (
        Decimal("180000000"),
        240,
        OrigenOriginacion.CLIENTE,
    )
    assert pendiente.pendiente is True


async def test_una_nueva_originacion_reemplaza_la_pendiente(uow, almacen):
    primera = await casos_uso.registrar_originacion(uow, CLIENTE, Decimal("100000000"), 120, OrigenOriginacion.CLIENTE)
    segunda = await casos_uso.registrar_originacion(uow, CLIENTE, Decimal("200000000"), 360, OrigenOriginacion.SOCIO)

    pendiente = await casos_uso.consultar_originacion_pendiente(uow, CLIENTE)

    assert pendiente.id == segunda.id
    assert pendiente.origen == OrigenOriginacion.SOCIO
    assert almacen.originaciones[primera.id].pendiente is False


async def test_sin_originacion_pendiente_es_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_originacion_pendiente(uow, CLIENTE)


async def test_cerrar_deja_al_cliente_sin_originacion_pendiente(uow):
    await casos_uso.registrar_originacion(uow, CLIENTE, Decimal("180000000"), 240, OrigenOriginacion.CLIENTE)

    await casos_uso.cerrar_originacion(uow, CLIENTE)

    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_originacion_pendiente(uow, CLIENTE)


async def test_cerrar_sin_originacion_no_falla(uow):
    await casos_uso.cerrar_originacion(uow, CLIENTE)


async def test_las_originaciones_de_otro_cliente_no_se_mezclan(uow):
    await casos_uso.registrar_originacion(uow, "otro", Decimal("180000000"), 240, OrigenOriginacion.CLIENTE)

    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_originacion_pendiente(uow, CLIENTE)


@pytest.mark.parametrize(
    ("cliente_id", "valor", "plazo", "codigo"),
    [
        (" ", Decimal("1"), 12, "cliente_id_vacio"),
        (CLIENTE, Decimal("0"), 12, "valor_credito_invalido"),
        (CLIENTE, Decimal("1"), 0, "plazo_credito_invalido"),
        (CLIENTE, Decimal("1"), 481, "plazo_credito_invalido"),
    ],
)
def test_originacion_rechaza_datos_invalidos(cliente_id, valor, plazo, codigo):
    with pytest.raises(ReglaDeNegocioViolada) as error:
        Originacion.abrir(cliente_id, valor, plazo, OrigenOriginacion.CLIENTE)

    assert error.value.codigo == codigo


def test_cerrar_dos_veces_conserva_la_primera_fecha():
    originacion = Originacion.abrir(CLIENTE, Decimal("1"), 12, OrigenOriginacion.CLIENTE)
    originacion.cerrar()
    primera = originacion.cerrada_en

    originacion.cerrar()

    assert originacion.cerrada_en == primera


def test_api_registra_consulta_y_cierra_la_originacion(client):
    creada = client.post(
        "/v1/originaciones",
        json={"cliente_id": CLIENTE, "valor": "180000000", "plazo_meses": 240, "origen": "socio"},
    )

    assert creada.status_code == 201
    assert creada.json()["origen"] == "socio"
    assert creada.json()["pendiente"] is True

    pendiente = client.get(f"/v1/originaciones/clientes/{CLIENTE}/pendiente")
    assert pendiente.status_code == 200
    assert pendiente.json()["id"] == creada.json()["id"]
    assert pendiente.json()["plazo_meses"] == 240

    assert client.delete(f"/v1/originaciones/clientes/{CLIENTE}/pendiente").status_code == 204
    assert client.get(f"/v1/originaciones/clientes/{CLIENTE}/pendiente").status_code == 404


def test_api_origen_por_defecto_es_cliente(client):
    creada = client.post("/v1/originaciones", json={"cliente_id": CLIENTE, "valor": "5000000", "plazo_meses": 60})

    assert creada.status_code == 201
    assert creada.json()["origen"] == "cliente"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"cliente_id": CLIENTE, "valor": "0", "plazo_meses": 60},
        {"cliente_id": CLIENTE, "valor": "5000000", "plazo_meses": 0},
        {"cliente_id": CLIENTE, "valor": "5000000", "plazo_meses": 60, "origen": "banco"},
        {"cliente_id": "", "valor": "5000000", "plazo_meses": 60},
    ],
)
def test_api_rechaza_originaciones_invalidas(client, cuerpo):
    assert client.post("/v1/originaciones", json=cuerpo).status_code == 422
