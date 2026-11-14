from fastapi import Request

from app.ports.consentimiento import ConsultaConsentimiento
from app.ports.kyc import VerificadorKYC
from app.ports.perfilamiento import ConsultaPerfilamiento
from app.ports.persistencia import FabricaUnidadDeTrabajo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_verificador_kyc(request: Request) -> VerificadorKYC:
    return request.app.state.verificador_kyc


def obtener_cliente_consentimiento(request: Request) -> ConsultaConsentimiento:
    return request.app.state.cliente_consentimiento


def obtener_cliente_perfilamiento(request: Request) -> ConsultaPerfilamiento:
    return request.app.state.cliente_perfilamiento
