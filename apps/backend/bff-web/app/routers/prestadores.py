"""Catálogo de prestadores. El núcleo calcula la distancia; aquí solo se adapta el canal."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from ..clients.ms_siniestros import ClienteMsSiniestros
from ..dependencies import obtener_cliente_siniestros, require_roles

router_cliente = APIRouter(prefix="/cliente", tags=["cliente-prestadores"])
router_operador = APIRouter(prefix="/operador", tags=["operador-prestadores"])

RADIO_DEFECTO = 10.0
RADIO_MAXIMO = 50.0


def _radio(valor: float | None) -> float:
    if valor is None:
        return RADIO_DEFECTO
    return min(valor, RADIO_MAXIMO)


def _fila_cliente(fila: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "tipo": fila["tipo"],
        "ramos": fila["ramos"],
        "direccion": fila["direccion"],
        "ciudad": fila["ciudad"],
        "barrio": fila["barrio"],
        "lat": fila["lat"],
        "lng": fila["lng"],
        "telefono": fila["telefono"],
        "horario": fila["horario"],
        "distanciaKm": fila.get("distancia_km"),
    }


def _fila_operador(fila: dict[str, Any]) -> dict[str, Any]:
    return _fila_cliente(fila) | {"estado": fila["estado"], "actualizadoEn": fila.get("actualizado_en")}


def _centro(cuerpo: dict[str, Any]) -> dict[str, Any] | None:
    centro = cuerpo.get("centro")
    if centro is None:
        return None
    return {"lat": centro["lat"], "lng": centro["lng"], "origen": centro["origen"]}


@router_cliente.get("/prestadores")
async def prestadores_cliente(
    siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
    _: Annotated[dict, Depends(require_roles("cliente"))],
    lat: Annotated[float | None, Query()] = None,
    lng: Annotated[float | None, Query()] = None,
    ramo: Annotated[str | None, Query()] = None,
    ciudad: Annotated[str | None, Query()] = None,
    radioKm: Annotated[float | None, Query()] = None,
) -> dict:
    cuerpo = await siniestros.prestadores(
        lat=lat, lng=lng, ramo=ramo, ciudad=ciudad, radio_km=_radio(radioKm), limite=50
    )
    return {
        "centro": _centro(cuerpo),
        "radioKm": cuerpo.get("radio_km"),
        "prestadores": [_fila_cliente(fila) for fila in cuerpo["prestadores"]],
    }


@router_cliente.get("/siniestros/{siniestro_id}/prestadores")
async def prestadores_del_siniestro(
    siniestro_id: str,
    siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
    _: Annotated[dict, Depends(require_roles("cliente"))],
    radioKm: Annotated[float | None, Query()] = None,
) -> dict:
    cuerpo = await siniestros.prestadores_siniestro(siniestro_id, _radio(radioKm))
    aviso = cuerpo["siniestro"]
    return {
        "siniestro": {"id": aviso["id"], "numero": aviso.get("numero"), "ramo": cuerpo.get("ramo_fijo")},
        "ramoFijo": cuerpo.get("ramo_fijo"),
        "sinGeoetiqueta": cuerpo["sin_geoetiqueta"],
        "centro": _centro(cuerpo),
        "radioKm": cuerpo.get("radio_km"),
        "prestadores": [_fila_cliente(fila) for fila in cuerpo["prestadores"]],
    }


@router_operador.get("/prestadores")
async def prestadores_operador(
    siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
    _: Annotated[dict, Depends(require_roles("operador", "asesor"))],
    ramo: Annotated[str | None, Query()] = None,
    ciudad: Annotated[str | None, Query()] = None,
    estado: Annotated[str | None, Query()] = None,
) -> dict:
    cuerpo = await siniestros.prestadores(ramo=ramo, ciudad=ciudad, estado=estado, limite=100)
    return {
        "conteos": cuerpo.get("conteos"),
        "centro": _centro(cuerpo),
        "prestadores": [_fila_operador(fila) for fila in cuerpo["prestadores"]],
    }


@router_operador.get("/prestadores/{prestador_id}")
async def prestador_operador(
    prestador_id: str,
    siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
    _: Annotated[dict, Depends(require_roles("operador", "asesor"))],
) -> dict:
    return _fila_operador(await siniestros.prestador(prestador_id))


@router_operador.post("/prestadores", status_code=201)
async def crear_prestador(
    cuerpo: dict,
    siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
    _: Annotated[dict, Depends(require_roles("operador"))],
) -> dict:
    return _fila_operador(await siniestros.crear_prestador(cuerpo))


@router_operador.patch("/prestadores/{prestador_id}")
async def editar_prestador(
    prestador_id: str,
    cuerpo: dict,
    siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
    _: Annotated[dict, Depends(require_roles("operador"))],
) -> dict:
    return _fila_operador(await siniestros.editar_prestador(prestador_id, cuerpo))


@router_operador.post("/prestadores/{prestador_id}/estado")
async def estado_prestador(
    prestador_id: str,
    cuerpo: dict,
    siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
    _: Annotated[dict, Depends(require_roles("operador"))],
) -> dict:
    return _fila_operador(await siniestros.cambiar_estado_prestador(prestador_id, cuerpo["estado"]))
