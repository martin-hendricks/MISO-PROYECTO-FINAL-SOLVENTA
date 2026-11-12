"""Siniestro asistido en el canal web (HU-157, HU-160): el cliente reporta y sigue su caso;
el operador atiende la cola de lo que el motor no resolvió.

El núcleo (ms-siniestros) decide de forma asíncrona: el aviso responde `recibido` al
instante y el motor lo aprueba y paga (bajo monto), lo rechaza (hechos objetivos) o lo
retiene en la cola del operador. Este BFF solo compone y traduce al vocabulario del canal.
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, ValidationError

from ..clients.base import RecursoNoEncontrado
from ..clients.ms_cotizacion import ClienteMsCotizacion
from ..clients.ms_polizas import ClienteMsPolizas
from ..clients.ms_siniestros import ClienteMsSiniestros
from ..dependencies import (
    obtener_cliente_cotizacion,
    obtener_cliente_polizas,
    obtener_cliente_siniestros,
    require_roles,
)
from ..ramos import presentar
from .cliente import _cotizacion_de_poliza, contexto_canonico

router_cliente = APIRouter(prefix="/cliente", tags=["cliente-siniestros"])
router_operador = APIRouter(prefix="/operador", tags=["operador-siniestros"])

Cliente = Annotated[dict, Depends(require_roles("cliente"))]
Operador = Annotated[dict, Depends(require_roles("operador"))]
Siniestros = Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)]
Polizas = Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)]
Cotizaciones = Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)]

MONEDA = "COP"
MAX_ARCHIVOS = 5


class GeoEntrada(BaseModel):
    """Mismo shape que el contrato móvil (Contratos-BFF HU-129): {lat, lng, precisionM}."""

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    precisionM: float | None = Field(default=None, ge=0)


def _parse_geo(geo: str | None) -> dict | None:
    if not geo:
        return None  # el usuario negó la ubicación: el aviso sigue sin geoetiqueta (HU-100)
    try:
        valor = GeoEntrada.model_validate_json(geo)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="Ubicación inválida") from exc
    return {"lat": valor.lat, "lng": valor.lng, "precision_m": valor.precisionM}


def _historial(siniestro: dict) -> list[dict]:
    return [{"estado": h["estado"], "fecha": h["ocurrido_en"]} for h in siniestro["historial"]]


def _motivo_para_cliente(detalle: dict) -> str | None:
    """El cliente recibe el motivo de un rechazo (Figma HU-27), nunca las reglas internas."""
    if detalle["siniestro"].get("resultado") != "rechazado":
        return None
    rechazos = [d for d in detalle["decisiones"] if d["resultado"] == "rechazado"]
    return rechazos[-1]["motivo"] if rechazos else None


def _fila_cliente(s: dict) -> dict:
    return {
        "id": s["id"],
        "siniestroId": s.get("numero") or s["id"],
        "tipo": s.get("tipo", "asistido"),
        "ramo": presentar(s.get("ramo"))[0],  # vocabulario canónico: el núcleo guarda el código
        "poliza": s.get("poliza_numero"),
        "resumen": s.get("descripcion") or "",
        "fecha": s.get("fecha_hecho"),
        "estado": s["estado"],
        "resultado": s.get("resultado"),
        "reserva": float(s["reserva"]) if s.get("reserva") is not None else None,
        "moneda": MONEDA,
    }


# --------------------------------------------------------------------- cliente


@router_cliente.post("/siniestros", status_code=201)
async def reportar_siniestro(
    usuario: Cliente,
    siniestros: Siniestros,
    polizas: Polizas,
    cotizaciones: Cotizaciones,
    poliza: Annotated[str, Form(min_length=1, max_length=60, description="Número visible de la póliza")],
    fechaHecho: Annotated[date, Form()],
    descripcion: Annotated[str, Form(min_length=1, max_length=1000)],
    archivos: Annotated[list[UploadFile], File()],
    geo: Annotated[str | None, Form(description='JSON {"lat","lng","precisionM"}; vacío si se negó')] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=120)] = None,
) -> dict:
    """HU-116 + HU-100 + HU-110: aviso con un archivo y ubicación opcional del navegador.

    El BFF resuelve la póliza (dueño, vigencia y ramo) y la envía como foto al núcleo,
    igual que hace con el umbral paramétrico: ms-siniestros no llama a ms-polizas."""
    if len(archivos) > MAX_ARCHIVOS:
        raise HTTPException(status_code=400, detail=f"Se admiten hasta {MAX_ARCHIVOS} archivos")
    # El uid del JWT es el usuario_id de ms-identidad: el mismo dueño de la póliza y del
    # siniestro. El token se reenvía y ms-siniestros vuelve a exigir que coincida.
    contexto = contexto_canonico(usuario)

    datos_poliza = await polizas.obtener_por_numero(poliza, contexto.usuario_id)
    if str(datos_poliza.get("usuario_id")) != str(contexto.usuario_id):
        # Una póliza ajena se responde igual que una inexistente.
        raise RecursoNoEncontrado(poliza)
    cotizacion = await _cotizacion_de_poliza(cotizaciones, datos_poliza)

    datos = {
        "usuario_id": str(contexto.usuario_id),
        "canal": "web",
        "poliza": {
            "poliza_id": str(datos_poliza["id"]),
            "numero": datos_poliza["numero"],
            "ramo": cotizacion.get("producto") or "sin-clasificar",
            "estado": str(datos_poliza["estado"]).lower(),  # ms-polizas responde VIGENTE
            "inicio_vigencia": datos_poliza["inicio_vigencia"],
            "fin_vigencia": datos_poliza["fin_vigencia"],
            # TODO: sin suma_asegurada a propósito -- emitir() guarda hoy coberturas
            # placeholder con suma_asegurada = prima, lo que dejaría toda reserva bajo el
            # umbral automático. Enviar max(suma_asegurada) cuando la emisión guarde las
            # coberturas reales del catálogo.
        },
        "fecha_hecho": fechaHecho.isoformat(),
        "descripcion": descripcion,
        "geo": _parse_geo(geo),
        "tipos_adjuntos": ["foto" if (a.content_type or "").startswith("image/") else "documento" for a in archivos],
    }
    evidencia = [
        (a.filename or "evidencia", await a.read(), (a.content_type or "application/octet-stream"))
        for a in archivos
    ]
    detalle = await siniestros.registrar_aviso(datos, evidencia, idempotency_key)
    s = detalle["siniestro"]
    return {"id": s["id"], "siniestroId": s.get("numero") or s["id"], "estado": s["estado"]}


@router_cliente.get("/siniestros")
async def mis_siniestros(usuario: Cliente, siniestros: Siniestros) -> dict:
    """HU-117 / HU-160: Mis siniestros con el estado del núcleo. No aprueba ni paga."""
    filas = await siniestros.listar(limite=50, usuario_id=contexto_canonico(usuario).usuario_id)
    return {"siniestros": [_fila_cliente(s) for s in filas]}


@router_cliente.get("/siniestros/{siniestro_id}")
async def detalle_siniestro(siniestro_id: UUID, usuario: Cliente, siniestros: Siniestros) -> dict:
    """HU-111: detalle con estado actual y evidencia (solo lectura)."""
    detalle = await siniestros.detalle(siniestro_id, usuario_id=contexto_canonico(usuario).usuario_id)
    s = detalle["siniestro"]
    return _fila_cliente(s) | {
        "descripcion": s.get("descripcion"),
        "geo": s.get("geo"),
        "motivo": _motivo_para_cliente(detalle),
        "historial": _historial(s),
        "evidencia": [
            {"nombre": a["nombre"], "tipo": a["tipo"], "contentType": a["content_type"], "url": a["url"]}
            for a in detalle["adjuntos"]
        ],
        "pago": (
            {
                "comprobante": detalle["pago"]["comprobante"],
                "monto": float(detalle["pago"]["monto"]),
                "moneda": MONEDA,
                "fecha": detalle["pago"]["pagado_en"],
            }
            if detalle.get("pago")
            else None
        ),
    }


# -------------------------------------------------------------------- operador

# Chips de la cola (Figma bo-cola-avisos): Pendientes, Aprobados, Rechazados, Todos.
_FILTROS = {
    "pendientes": {"requiere_revision": True},
    "aprobados": {"resultado": "aprobado"},
    "rechazados": {"resultado": "rechazado"},
    "todos": {},
}
LIMITE_COLA = 100


def _estado_cola(s: dict) -> str:
    """Una sola etiqueta para el badge: en_revision | aprobado | rechazado | enrutado |
    pagado | recibido. El texto lo pone el front; aquí no se comunica solo por color."""
    if s.get("requiere_revision"):
        return "en_revision"
    if s["estado"] in ("pagado", "enrutado"):
        return s["estado"]
    return s.get("resultado") or s["estado"]


def _fila_operador(s: dict) -> dict:
    return {
        "id": s["id"],
        "siniestroId": s.get("numero") or s["id"],
        # ms-identidad no expone nombre ni búsqueda por id: el canal muestra el id.
        "clienteId": s.get("usuario_id"),
        "poliza": s.get("poliza_numero") or "",
        "ramo": presentar(s.get("ramo"))[0],
        "recibidoEn": s["creado_en"],
        "estado": s["estado"],
        "estadoCola": _estado_cola(s),
        "resultado": s.get("resultado"),
        "requiereRevision": bool(s.get("requiere_revision")),
    }


@router_operador.get("/avisos")
async def cola(
    _: Operador,
    siniestros: Siniestros,
    filtro: Annotated[str, Query(pattern="^(pendientes|aprobados|rechazados|todos)$")] = "pendientes",
) -> dict:
    """HU-26: cola del operador ordenada por antigüedad del aviso, con conteo por chip."""
    conteos = {}
    filas: list[dict] = []
    for nombre, extra in _FILTROS.items():
        resultado = await siniestros.listar(limite=LIMITE_COLA, tipo="asistido", **extra)
        conteos[nombre] = len(resultado)
        if nombre == filtro:
            filas = resultado
    filas.sort(key=lambda s: s["creado_en"])  # el más antiguo primero
    return {"filtro": filtro, "conteos": conteos, "avisos": [_fila_operador(s) for s in filas]}


def _detalle_operador(detalle: dict) -> dict:
    s = detalle["siniestro"]
    return _fila_operador(s) | {
        "fechaHecho": s.get("fecha_hecho"),
        "descripcion": s.get("descripcion"),
        "geo": s.get("geo"),
        "montoEstimado": float(s["reserva"]) if s.get("reserva") is not None else None,
        "umbralAutomatico": float(s["umbral_automatico"]) if s.get("umbral_automatico") is not None else None,
        "bajoMonto": (
            s.get("reserva") is not None
            and s.get("umbral_automatico") is not None
            and float(s["reserva"]) <= float(s["umbral_automatico"])
        ),
        "moneda": MONEDA,
        "clavePago": detalle.get("clave_pago"),
        "motivoRevision": s.get("motivo_revision"),
        # Solo lectura: el operador ve la evidencia pero no puede editarla (HU-26).
        "evidencia": [
            {"nombre": a["nombre"], "tipo": a["tipo"], "contentType": a["content_type"], "url": a["url"]}
            for a in detalle["adjuntos"]
        ],
        "decisiones": detalle["decisiones"],
        "historial": _historial(s),
        "pago": detalle.get("pago"),
        "intentosPago": detalle.get("intentos_pago", []),
    }


@router_operador.get("/avisos/{siniestro_id}")
async def caso(siniestro_id: UUID, _: Operador, siniestros: Siniestros) -> dict:
    """HU-26: evidencia, póliza y estado en una pantalla."""
    return _detalle_operador(await siniestros.detalle(siniestro_id))


class Decision(BaseModel):
    siniestroId: str
    decision: str
    motivo: str | None = None


_DECISION_A_RESULTADO = {"aprobar": "aprobado", "rechazar": "rechazado"}


@router_operador.post("/avisos/decision")
async def decidir(body: Decision, operador: Operador, siniestros: Siniestros) -> dict:
    """HU-27: aprobar o rechazar con auditoría (quién = usuario de la sesión, cuándo, por
    qué). Aprobar no paga: el pago de bajo monto es una acción aparte (HU-29)."""
    if body.decision not in _DECISION_A_RESULTADO:
        raise HTTPException(status_code=400, detail="Decision no permitida")
    if body.decision == "rechazar" and not (body.motivo or "").strip():
        raise HTTPException(status_code=400, detail="Motivo requerido")
    try:
        siniestro_id = UUID(body.siniestroId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="siniestroId invalido") from exc

    detalle = await siniestros.decidir(
        siniestro_id, _DECISION_A_RESULTADO[body.decision], body.motivo, operador["sub"]
    )
    return _detalle_operador(detalle)


class Perito(BaseModel):
    motivo: str | None = None


@router_operador.post("/avisos/{siniestro_id}/perito")
async def enrutar_a_perito(siniestro_id: UUID, body: Perito, operador: Operador, siniestros: Siniestros) -> dict:
    """HU-28: el caso que no es de bajo monto se enruta a un perito."""
    return _detalle_operador(await siniestros.enrutar_a_perito(siniestro_id, body.motivo, operador["sub"]))


@router_operador.post("/avisos/{siniestro_id}/pago")
async def pagar(siniestro_id: UUID, operador: Operador, siniestros: Siniestros) -> dict:
    """HU-29: desembolso de bajo monto. Un reintento devuelve el mismo comprobante."""
    resultado = await siniestros.pagar(siniestro_id, operador["sub"])
    return {
        "pago": resultado["pago"],
        "reintento": resultado["reintento"],
        "caso": _detalle_operador(resultado["detalle"]),
    }

