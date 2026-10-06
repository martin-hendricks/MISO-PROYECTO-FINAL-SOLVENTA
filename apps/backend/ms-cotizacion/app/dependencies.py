from datetime import timedelta

from fastapi import Request

from app.application.casos_uso import Colaboradores
from app.config import Settings
from app.infrastructure.catalogo_memoria import CatalogoEnMemoria
from app.infrastructure.memoria import RelojSistema, RepositorioCotizacionesEnMemoria
from app.infrastructure.stubs import FactorRiesgoNeutroStub, PrimaFijaStub


def componer(config: Settings) -> Colaboradores:
    """Raíz de composición: qué implementación cumple cada puerto en esta iteración."""
    return Colaboradores(
        catalogo=CatalogoEnMemoria(),
        calculadora_prima=PrimaFijaStub(),
        factor_riesgo=FactorRiesgoNeutroStub(),
        cotizaciones=RepositorioCotizacionesEnMemoria(),
        reloj=RelojSistema(),
        vigencia_oferta=timedelta(minutes=config.vigencia_oferta_minutos),
    )


def obtener_colaboradores(request: Request) -> Colaboradores:
    return request.app.state.colaboradores
