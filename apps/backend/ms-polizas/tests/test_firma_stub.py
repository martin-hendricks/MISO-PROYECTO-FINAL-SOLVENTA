from uuid import uuid4

import pytest

from app.config import Settings
from app.infrastructure.firma import FirmaStub


async def test_stub_ok_firma_con_hash_determinista_por_oferta():
    stub = FirmaStub("ok")
    oferta_id = uuid4()

    primera = await stub.firmar(oferta_id)
    segunda = await stub.firmar(oferta_id)

    assert primera.exitosa and primera.motivo is None
    assert len(primera.firma_hash) == 64
    assert primera.firma_hash == segunda.firma_hash
    assert primera.firma_hash != (await stub.firmar(uuid4())).firma_hash


async def test_stub_no_rechaza_con_motivo_y_sin_hash():
    resultado = await FirmaStub("no").firmar(uuid4())

    assert not resultado.exitosa
    assert resultado.motivo
    assert resultado.firma_hash is None


def test_el_stub_responde_ok_por_defecto():
    assert Settings().firma_stub_resultado == "ok"


def test_resultado_del_stub_invalido_falla_al_crearse():
    with pytest.raises(ValueError):
        FirmaStub("tal_vez")
