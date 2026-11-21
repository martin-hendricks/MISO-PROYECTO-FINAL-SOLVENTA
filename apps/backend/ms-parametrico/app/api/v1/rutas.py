from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.adaptadores import ADAPTADORES
from app.domain.evento import EventoInvalido
from app.metricas import EVENTOS
from app.ports.publicador import PublicadorEventos, PublicadorNoDisponible, PublicadorSaturado
from app.seguridad import ProveedorAutenticado

router = APIRouter(prefix="/v1/telemetria", tags=["telemetria"])


def obtener_publicador(request: Request) -> PublicadorEventos:
    return request.app.state.publicador


Publicador = Annotated[PublicadorEventos, Depends(obtener_publicador)]


class EventoAceptado(BaseModel):
    evento_id: str
    aceptado: bool = True


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str


def _reintentar(request: Request, codigo_http: int, codigo: str, mensaje: str) -> JSONResponse:
    segundos = request.app.state.config.reintentar_despues_segundos
    return JSONResponse(
        status_code=codigo_http,
        content={"codigo": codigo, "mensaje": mensaje},
        headers={"Retry-After": str(segundos)},
    )


@router.post(
    "/{proveedor}/eventos",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EventoAceptado,
    responses={
        404: {"model": ErrorSalida},
        422: {"model": ErrorSalida},
        429: {"model": ErrorSalida, "description": "Contrapresión: reintentar tras Retry-After"},
        503: {"model": ErrorSalida, "description": "Tópico no disponible: reintentar tras Retry-After"},
    },
)
async def recibir_evento(
    proveedor: str,
    request: Request,
    publicador: Publicador,
    _cliente: ProveedorAutenticado,
    carga: Annotated[dict[str, Any], Body()],
):
    """:ApiTelemetria. Traduce la carga del proveedor al evento canónico y la publica en
    TopicoTelemetria. 202 = el tópico confirmó la escritura; la evaluación y el pago
    ocurren después, en el consumidor (ms-siniestros). Reenviar el mismo evento es
    seguro: el consumidor deduplica por evento_id."""
    adaptador = ADAPTADORES.get(proveedor)
    if adaptador is None:
        raise HTTPException(status_code=404, detail=f"Proveedor '{proveedor}' no registrado")
    try:
        evento = adaptador.traducir(carga)
    except EventoInvalido as exc:
        EVENTOS.labels(proveedor, "rechazado").inc()
        return JSONResponse(status_code=422, content={"codigo": exc.codigo, "mensaje": exc.mensaje})

    try:
        await publicador.publicar(evento)
    except PublicadorSaturado:
        EVENTOS.labels(proveedor, "contrapresion").inc()
        return _reintentar(request, 429, "contrapresion", "Capacidad de ingesta saturada; reintentar")
    except PublicadorNoDisponible:
        EVENTOS.labels(proveedor, "no_disponible").inc()
        return _reintentar(request, 503, "topico_no_disponible", "El evento no se pudo persistir; reintentar")

    EVENTOS.labels(proveedor, "aceptado").inc()
    return EventoAceptado(evento_id=evento.evento_id)
