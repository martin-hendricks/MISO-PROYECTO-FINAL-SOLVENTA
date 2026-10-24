from decimal import Decimal

import pytest

from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import AtributoPerfil, EstadoAdaptador, FactorInterno, Oferta, OrigenAdaptador, Perfil
from app.domain.precio import ANTIGUEDAD_DOCUMENTO, NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO, ZONA_RIESGO, calcular_oferta


def _atributo(nombre: str, valor: str, degradado: bool = False) -> AtributoPerfil:
    return AtributoPerfil(
        nombre=nombre,
        valor=Decimal(valor),
        origen=OrigenAdaptador.OPEN_FINANCE,
        estado=EstadoAdaptador.DEGRADADO if degradado else EstadoAdaptador.EXITO,
        degradado=degradado,
    )


def test_otorgar_consentimiento_queda_vigente_y_con_timestamp():
    from app.domain.modelos import Consentimiento

    consentimiento = Consentimiento.otorgar("cliente-1")

    assert consentimiento.vigente
    assert consentimiento.cliente_id == "cliente-1"
    assert consentimiento.otorgado_en is not None
    assert consentimiento.revocado_en is None


def test_otorgar_consentimiento_requiere_cliente_id():
    from app.domain.modelos import Consentimiento

    with pytest.raises(ReglaDeNegocioViolada) as exc:
        Consentimiento.otorgar("   ")
    assert exc.value.codigo == "cliente_id_vacio"


def test_revocar_consentimiento_deja_de_estar_vigente():
    from app.domain.modelos import Consentimiento

    consentimiento = Consentimiento.otorgar("cliente-1")
    consentimiento.revocar()

    assert not consentimiento.vigente
    assert consentimiento.revocado_en is not None


def test_revocar_dos_veces_es_estable():
    from app.domain.modelos import Consentimiento

    consentimiento = Consentimiento.otorgar("cliente-1")
    consentimiento.revocar()
    primera_revocacion = consentimiento.revocado_en
    consentimiento.revocar()

    assert consentimiento.revocado_en == primera_revocacion


def test_perfil_se_arma_a_partir_de_atributos_propios():
    atributos = [_atributo(NIVEL_INGRESOS_ESTIMADO, "0.7"), _atributo(SCORE_COMPORTAMIENTO, "0.8")]
    perfil = Perfil.armar("cliente-1", atributos)

    assert perfil.cliente_id == "cliente-1"
    assert perfil.atributo(NIVEL_INGRESOS_ESTIMADO).valor == Decimal("0.7")
    assert perfil.atributo("inexistente") is None
    assert not perfil.degradado


def test_perfil_degradado_si_algun_atributo_lo_esta():
    atributos = [_atributo(NIVEL_INGRESOS_ESTIMADO, "1.0", degradado=True), _atributo(SCORE_COMPORTAMIENTO, "0.5")]
    perfil = Perfil.armar("cliente-1", atributos)

    assert perfil.degradado


def test_calcular_oferta_incluye_precio_y_factores_explicables():
    atributos = [
        _atributo(NIVEL_INGRESOS_ESTIMADO, "0.7"),
        _atributo(SCORE_COMPORTAMIENTO, "0.8"),
        _atributo(ZONA_RIESGO, "0.3"),
        _atributo(ANTIGUEDAD_DOCUMENTO, "0.6"),
    ]
    perfil = Perfil.armar("cliente-1", atributos)
    pesos = {
        NIVEL_INGRESOS_ESTIMADO: Decimal("-0.08"),
        SCORE_COMPORTAMIENTO: Decimal("-0.15"),
        ZONA_RIESGO: Decimal("0.20"),
        ANTIGUEDAD_DOCUMENTO: Decimal("-0.05"),
    }

    oferta = calcular_oferta("cliente-1", perfil, pesos, Decimal("50000"))

    # ajuste = 1 + (-0.08*0.7) + (-0.15*0.8) + (0.20*0.3) + (-0.05*0.6) = 0.8540
    assert oferta.precio == Decimal("42700.00")
    assert not oferta.degradado
    assert len(oferta.factores) == 4
    assert {f.factor for f in oferta.factores} == {
        NIVEL_INGRESOS_ESTIMADO,
        SCORE_COMPORTAMIENTO,
        ZONA_RIESGO,
        ANTIGUEDAD_DOCUMENTO,
    }
    factor_ingresos = next(f for f in oferta.factores if f.factor == NIVEL_INGRESOS_ESTIMADO)
    assert factor_ingresos.impacto == "reduce_prima"
    factor_zona = next(f for f in oferta.factores if f.factor == ZONA_RIESGO)
    assert factor_zona.impacto == "aumenta_prima"
    assert oferta.snapshot_atributos == perfil.atributos


def test_calcular_oferta_marca_degradado_si_el_perfil_esta_degradado():
    atributos = [_atributo(NIVEL_INGRESOS_ESTIMADO, "1.0", degradado=True)]
    perfil = Perfil.armar("cliente-1", atributos)

    oferta = calcular_oferta("cliente-1", perfil, {NIVEL_INGRESOS_ESTIMADO: Decimal("-0.08")}, Decimal("50000"))

    assert oferta.degradado


def test_oferta_armar_rechaza_precio_no_positivo():
    perfil = Perfil.armar("cliente-1", [])
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        Oferta.armar("cliente-1", Decimal("0"), [FactorInterno("x", "reduce_prima", Decimal("-0.1"))], perfil)
    assert exc.value.codigo == "precio_no_positivo"


def test_calcular_oferta_nunca_deja_precio_no_positivo():
    atributos = [_atributo(NIVEL_INGRESOS_ESTIMADO, "100")]
    perfil = Perfil.armar("cliente-1", atributos)

    oferta = calcular_oferta("cliente-1", perfil, {NIVEL_INGRESOS_ESTIMADO: Decimal("-10")}, Decimal("50000"))

    assert oferta.precio > 0
