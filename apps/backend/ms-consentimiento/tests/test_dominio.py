import pytest

from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import Consentimiento


def test_otorgar_crea_consentimiento_vigente():
    consentimiento = Consentimiento.otorgar("cliente-1")

    assert consentimiento.cliente_id == "cliente-1"
    assert consentimiento.vigente
    assert consentimiento.revocado_en is None


def test_otorgar_normaliza_espacios():
    consentimiento = Consentimiento.otorgar("  cliente-1  ")

    assert consentimiento.cliente_id == "cliente-1"


@pytest.mark.parametrize("cliente_id", ["", "   "])
def test_otorgar_exige_cliente_id(cliente_id):
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        Consentimiento.otorgar(cliente_id)
    assert exc.value.codigo == "cliente_id_vacio"


def test_revocar_marca_revocado_en_y_deja_de_estar_vigente():
    consentimiento = Consentimiento.otorgar("cliente-1")

    consentimiento.revocar()

    assert not consentimiento.vigente
    assert consentimiento.revocado_en is not None


def test_revocar_dos_veces_es_estable_y_no_cambia_la_marca():
    consentimiento = Consentimiento.otorgar("cliente-1")
    consentimiento.revocar()
    primera_marca = consentimiento.revocado_en

    consentimiento.revocar()

    assert consentimiento.revocado_en == primera_marca
