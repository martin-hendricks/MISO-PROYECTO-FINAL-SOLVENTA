import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from ..clients.nucleo import DETALLE_INCOMPLETA, token_saliente
from ..dependencies import require_customer
from ..ramos import SIN_CLASIFICAR, presentar, producto_de

router = APIRouter(
    prefix="/cliente",
    tags=["cliente"],
    dependencies=[Depends(require_customer)],
)

OFFER = {
    "cotizacionId": "COT-1042",
    "ramo": "Protección de dispositivo",
    "estado": "oferta_vigente",
    "prima": 89000,
    "moneda": "COP",
    "venceEn": "2026-10-01",
}
POLICY = {
    "numero": "POL-88219-CO",
    "ramo": "Protección de dispositivo",
    "estado": "vigente",
    "venceEn": "2027-03-12",
}
PAYMENT = {
    "siniestroId": "SIN-220",
    "poliza": "POL-11002-CO",
    "umbral": "retraso mayor a 120 min",
    "monto": 250000,
    "moneda": "COP",
    "estado": "pagado",
}
QUE_HACER = "Toma la foto del daño y anota fecha y lugar."
CANAL = "movil"
SCORE = "0.5000"
TOKEN_MEDIO_PAGO = "stub-medio-pago"
RAMO_SIN_CLASIFICAR = SIN_CLASIFICAR
_NAMESPACE = uuid.UUID("5f4d3a2b-0000-4000-8000-000000000000")


class Cotizacion(BaseModel):
    ramo: str
    datosRiesgo: dict
    rol: str | None = None


class Aceptar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cotizacionId: str


class ConfirmacionVacia(BaseModel):
    """Acceptance carries no card data. Any extra field is rejected."""

    model_config = ConfigDict(extra="forbid")


class PreferenciaRenovacion(BaseModel):
    renovacionAutomatica: bool


class Geo(BaseModel):
    lat: float
    lng: float
    precisionM: float


class Adjunto(BaseModel):
    tipo: str
    nombre: str


class Aviso(BaseModel):
    poliza: str
    fechaHecho: str
    geo: Geo | None
    adjuntos: list[Adjunto]
    rol: str | None = None


class Credito(BaseModel):
    valor: int
    plazoMeses: int


class Hipoteca(BaseModel):
    credito: Credito
    consentimientoPerfil: bool


class PushToken(BaseModel):
    token: str
    plataforma: str


class Asistencia(BaseModel):
    prestadorId: str
    geo: Geo
    poliza: str


def es_v1(request: Request) -> bool:
    return "/v1/" in request.url.path


def _offer(cotizacion_id: str) -> dict:
    body = dict(OFFER)
    body["cotizacionId"] = cotizacion_id
    return body


def _producto_de(ramo: str) -> str:
    codigo = producto_de(ramo)
    if codigo is None:
        raise HTTPException(status_code=404, detail="ramo_no_disponible")
    return codigo


def _uuid_desde(*partes: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, "|".join(partes)))


def _contexto(usuario: dict) -> dict:
    uid = str(usuario.get("uid") or "")
    if not uid:
        raise HTTPException(status_code=401, detail="Token invalido")
    return {
        "usuario_id": uid,
        "socio_id": _uuid_desde("socio", uid),
        "consentimiento_id": _uuid_desde("consentimiento", uid),
        "perfil_id": _uuid_desde("perfil", uid),
    }


def _ajeno(recurso: dict, uid: str) -> bool:
    dueno = recurso.get("usuario_id")
    return dueno is not None and str(dueno) != str(uid)


def _exigir(cuerpo: dict, *claves: str) -> dict:
    if not isinstance(cuerpo, dict) or any(clave not in cuerpo for clave in claves):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    return cuerpo


def _oferta_movil(datos: dict, ramo: str, descripcion: str = "") -> dict:
    datos = _exigir(datos, "cotizacion_id", "estado", "prima", "moneda", "vence_en")
    return {
        "cotizacionId": datos["cotizacion_id"],
        "ramo": ramo,
        "descripcion": descripcion,
        "estado": datos["estado"],
        "prima": datos["prima"],
        "moneda": datos["moneda"],
        "venceEn": datos["vence_en"],
    }


def _poliza_movil(poliza: dict, cotizacion: dict, *, detalle: bool) -> dict:
    poliza = _exigir(poliza, "numero", "estado", "fin_vigencia", "coberturas")
    if not isinstance(poliza["coberturas"], list):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    nombres = []
    for cobertura in poliza["coberturas"]:
        if not isinstance(cobertura, dict) or "nombre" not in cobertura:
            raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
        nombres.append(cobertura["nombre"])
    ramo, descripcion = presentar(cotizacion.get("producto"))
    cuerpo = {
        "numero": poliza["numero"],
        "ramo": ramo,
        "descripcion": descripcion,
        "resumen": ", ".join(nombres) or "Sin coberturas",
        "estado": poliza["estado"],
        "venceEn": poliza["fin_vigencia"],
    }
    if detalle:
        cuerpo["queHacer"] = QUE_HACER
    return cuerpo


def _polizas_proyectadas(nucleo, usuario: dict) -> list:
    polizas = nucleo.listar_polizas(usuario_id=_contexto(usuario)["usuario_id"], limite=20)
    if not isinstance(polizas, list):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    return [
        _poliza_movil(poliza, _cotizacion_de_poliza(nucleo, poliza), detalle=False)
        for poliza in polizas
    ]


def _cotizacion_de_poliza(nucleo, poliza: dict) -> dict:
    oferta_id = poliza.get("oferta_id") if isinstance(poliza, dict) else None
    if not oferta_id:
        return {}
    try:
        return nucleo.reconsultar_por_oferta(str(oferta_id))
    except HTTPException as exc:
        if exc.status_code in (404, 503):
            return {}
        raise


def _hipoteca_degradada() -> dict:
    return {
        "ramo": "Vida crediticia",
        "estado": "oferta_vigente",
        "prima": 50000,
        "moneda": "COP",
        "factores": ["plazo", "valor del crédito"],
        "degradada": True,
    }


def _hipoteca_movil(oferta: dict) -> dict:
    oferta = _exigir(oferta, "precio", "moneda", "factores", "degradado")
    if not isinstance(oferta["factores"], list):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    factores = []
    for factor in oferta["factores"]:
        if not isinstance(factor, dict) or "factor" not in factor:
            raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
        factores.append(factor["factor"])
    return {
        "ramo": "Vida crediticia",
        "estado": "oferta_vigente",
        "prima": float(oferta["precio"]),
        "moneda": oferta["moneda"],
        "factores": factores,
        "degradada": oferta["degradado"],
    }


@router.post("/cotizaciones")
def cotizar(body: Cotizacion, request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        return _offer(OFFER["cotizacionId"])
    contexto = _contexto(usuario)
    producto = _producto_de(body.ramo)
    datos_riesgo = dict(body.datosRiesgo)
    try:
        perfil = request.app.state.nucleo.obtener_usuario(contexto["usuario_id"]) or {}
    except Exception:
        perfil = {}
    if isinstance(perfil, dict) and perfil.get("ingresos_mensuales") is not None:
        datos_riesgo["ingresos_mensuales"] = perfil["ingresos_mensuales"]
        datos_riesgo["gastos_mensuales"] = perfil["gastos_mensuales"]
    datos = request.app.state.nucleo.cotizar(
        idempotency_key=str(uuid.uuid4()),
        usuario_id=contexto["usuario_id"],
        socio_id=contexto["socio_id"],
        consentimiento_id=contexto["consentimiento_id"],
        producto=producto,
        canal=CANAL,
        datos_riesgo=datos_riesgo,
    )
    _, descripcion = presentar(producto)
    return _oferta_movil(datos, body.ramo, descripcion)


@router.patch("/polizas/{numero}/preferencias")
def guardar_renovacion(
    numero: str, body: PreferenciaRenovacion, request: Request, usuario: dict = Depends(require_customer)
) -> dict:
    if not es_v1(request):
        raise HTTPException(status_code=404, detail="No existe")
    contexto = _contexto(usuario)
    poliza = _exigir(request.app.state.nucleo.obtener_por_numero(numero, contexto["usuario_id"]), "id", "numero")
    if _ajeno(poliza, contexto["usuario_id"]):
        raise HTTPException(status_code=404, detail="No existe")
    actualizada = request.app.state.nucleo.guardar_preferencia(
        str(poliza["id"]), body.renovacionAutomatica, contexto["usuario_id"]
    )
    return {"numero": actualizada.get("numero", numero), "renovacionAutomatica": body.renovacionAutomatica}


@router.get("/cotizaciones/{cotizacion_id}")
def reconsultar(
    cotizacion_id: str, request: Request, usuario: dict = Depends(require_customer)
) -> dict:
    if not es_v1(request):
        return _offer(cotizacion_id)
    uid = _contexto(usuario)["usuario_id"]
    datos = request.app.state.nucleo.reconsultar(cotizacion_id, usuario_id=uid)
    datos = _exigir(datos, "producto")
    if _ajeno(datos, uid):
        raise HTTPException(status_code=404, detail="No existe")
    ramo, descripcion = presentar(datos["producto"])
    return _oferta_movil(datos, ramo, descripcion)


@router.post("/cotizaciones/{cotizacion_id}/aceptacion")
def aceptar_cotizacion(
    cotizacion_id: str,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
    _confirmacion: ConfirmacionVacia | None = None,
    usuario: dict = Depends(require_customer),
) -> dict:
    if not es_v1(request):
        raise HTTPException(status_code=404, detail="No existe")
    nucleo = request.app.state.nucleo
    contexto = _contexto(usuario)
    aceptacion = _exigir(
        nucleo.aceptar_oferta(
            cotizacion_id=cotizacion_id,
            idempotency_key=idempotency_key,
            perfil_id=contexto["perfil_id"],
            score=SCORE,
            usuario_id=contexto["usuario_id"],
        ),
        "decision",
    )
    if str(aceptacion["decision"]).upper() != "ACEPTADA":
        if "motivo" not in aceptacion:
            raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
        return {"estado": "rechazada", "motivo": aceptacion["motivo"]}
    aceptacion = _exigir(aceptacion, "oferta_id", "cotizacion_id", "prima", "estado", "moneda")
    pago = _exigir(
        nucleo.cobrar_prima(
            solicitud_id=str(aceptacion["cotizacion_id"]),
            oferta_id=str(aceptacion["oferta_id"]),
            usuario_id=contexto["usuario_id"],
            monto=str(Decimal(str(aceptacion["prima"]))),
            token_medio_pago=TOKEN_MEDIO_PAGO,
        ),
        "id",
    )
    poliza = _exigir(
        nucleo.emitir(
            solicitud_id=str(aceptacion["cotizacion_id"]),
            oferta_id=str(aceptacion["oferta_id"]),
            usuario_id=contexto["usuario_id"],
            token_pago_confirmado=str(pago["id"]),
            coberturas=[
                {
                    "nombre": aceptacion.get("estado", "cobertura-base"),
                    "suma_asegurada": str(aceptacion["prima"]),
                    "deducible": "0",
                }
            ],
        ),
        "numero",
        "estado",
        "fin_vigencia",
    )
    cotizacion = _exigir(nucleo.reconsultar(str(aceptacion["cotizacion_id"])), "producto")
    return {
        "cotizacionId": aceptacion["cotizacion_id"],
        "estado": aceptacion["estado"],
        "prima": aceptacion["prima"],
        "moneda": aceptacion["moneda"],
        "poliza": {
            "numero": poliza["numero"],
            "ramo": presentar(cotizacion["producto"])[0],
            "descripcion": presentar(cotizacion["producto"])[1],
            "estado": poliza["estado"],
            "venceEn": poliza["fin_vigencia"],
        },
    }


@router.post("/polizas")
def aceptar(body: Aceptar, request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        if body.cotizacionId == "COT-RECHAZADA":
            return {"estado": "rechazada", "motivo": "Valor del equipo fuera de rango"}
        return dict(POLICY)
    nucleo = request.app.state.nucleo
    contexto = _contexto(usuario)
    aceptacion = _exigir(
        nucleo.aceptar_oferta(
            cotizacion_id=body.cotizacionId,
            idempotency_key=str(uuid.uuid4()),
            perfil_id=contexto["perfil_id"],
            score=SCORE,
            usuario_id=contexto["usuario_id"],
        ),
        "decision",
    )
    if str(aceptacion["decision"]).upper() != "ACEPTADA":
        if "motivo" not in aceptacion:
            raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
        return {"estado": "rechazada", "motivo": aceptacion["motivo"]}
    aceptacion = _exigir(aceptacion, "oferta_id", "cotizacion_id", "prima")
    pago = _exigir(
        nucleo.cobrar_prima(
            solicitud_id=str(aceptacion["cotizacion_id"]),
            oferta_id=str(aceptacion["oferta_id"]),
            usuario_id=contexto["usuario_id"],
            monto=str(Decimal(str(aceptacion["prima"]))),
            token_medio_pago=TOKEN_MEDIO_PAGO,
        ),
        "id",
    )
    poliza = _exigir(
        nucleo.emitir(
            solicitud_id=str(aceptacion["cotizacion_id"]),
            oferta_id=str(aceptacion["oferta_id"]),
            usuario_id=contexto["usuario_id"],
            token_pago_confirmado=str(pago["id"]),
            coberturas=[
                {
                    "nombre": aceptacion.get("estado", "cobertura-base"),
                    "suma_asegurada": str(aceptacion["prima"]),
                    "deducible": "0",
                }
            ],
        ),
        "numero",
        "estado",
        "fin_vigencia",
    )
    cotizacion = _exigir(nucleo.reconsultar(str(aceptacion["cotizacion_id"])), "producto")
    ramo, descripcion = presentar(cotizacion["producto"])
    return {
        "numero": poliza["numero"],
        "ramo": ramo,
        "descripcion": descripcion,
        "estado": poliza["estado"],
        "venceEn": poliza["fin_vigencia"],
    }


@router.get("/polizas")
def billetera(request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        return {
            "polizas": [
                {
                    "numero": "POL-88219-CO",
                    "ramo": "Protección de dispositivo",
                    "resumen": "Robo, Pantalla, Hurto",
                    "estado": "vigente",
                    "venceEn": "2027-03-12",
                }
            ]
        }
    return {"polizas": _polizas_proyectadas(request.app.state.nucleo, usuario)}


@router.get("/polizas/{numero}")
def detalle(numero: str, request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        return {
            "numero": numero,
            "ramo": "Protección de dispositivo",
            "resumen": "Robo y Pantalla",
            "estado": "vigente",
            "venceEn": "2027-03-12",
            "queHacer": QUE_HACER,
        }
    nucleo = request.app.state.nucleo
    uid = _contexto(usuario)["usuario_id"]
    poliza = nucleo.obtener_por_numero(numero, usuario_id=uid)
    if _ajeno(poliza, uid):
        raise HTTPException(status_code=404, detail="No existe")
    return _poliza_movil(poliza, _cotizacion_de_poliza(nucleo, poliza), detalle=True)


_ESTADO_TEXTO = {
    "recibido": "Recibido",
    "en_evaluacion": "En evaluación",
    "decidido": "Decidido",
    "enrutado": "Enrutado",
    "pagado": "Pagado",
}


def _siniestro_movil(fila: dict) -> dict:
    fila = _exigir(fila, "id", "estado")
    numero = fila.get("numero") or fila.get("siniestroId") or fila["id"]
    return {
        "id": str(fila["id"]),
        "siniestroId": str(numero),
        "tipo": fila.get("tipo") or "asistido",
        "ramo": fila.get("ramo") or fila.get("poliza") or "",
        "resumen": fila.get("descripcion") or fila.get("evento_id") or fila.get("resumen") or "",
        "fecha": fila.get("fecha_hecho") or fila.get("fecha"),
        "estado": fila["estado"],
        "estadoTexto": fila.get("estadoTexto") or _ESTADO_TEXTO.get(fila["estado"], fila["estado"]),
        "reserva": fila.get("reserva"),
        "moneda": fila.get("moneda") or "COP",
    }


def _detalle_movil(detalle: dict) -> dict:
    siniestro = detalle.get("siniestro") if isinstance(detalle.get("siniestro"), dict) else detalle
    fila = _siniestro_movil(siniestro)
    pago = detalle.get("pago")
    return fila | {
        "poliza": siniestro.get("poliza_numero") or siniestro.get("poliza"),
        "descripcion": siniestro.get("descripcion"),
        "lugar": siniestro.get("lugar"),
        "geo": siniestro.get("geo"),
        "motivo": siniestro.get("motivo") or detalle.get("motivo"),
        "evidencia": [
            {
                "nombre": a.get("nombre"),
                "tipo": a.get("tipo"),
                "contentType": a.get("content_type") or a.get("contentType"),
                "url": a.get("url"),
            }
            for a in detalle.get("adjuntos") or detalle.get("evidencia") or []
        ],
        "historial": [
            {"estado": h.get("estado"), "fecha": h.get("ocurrido_en") or h.get("fecha")}
            for h in siniestro.get("historial") or detalle.get("historial") or []
        ],
        "pago": pago,
        "umbral": siniestro.get("umbral_automatico") or detalle.get("umbral"),
    }


_TIPOS = {
    "image/png": "foto",
    "image/jpeg": "foto",
    "application/pdf": "soporte",
    "video/mp4": "video",
}


def _geo_aviso(crudo) -> dict | None:
    """El móvil envía {lat, lng, precisionM}. ms-siniestros espera precision_m."""
    if not crudo:
        return None
    try:
        valor = json.loads(str(crudo))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Ubicación inválida") from exc
    if not isinstance(valor, dict) or "lat" not in valor or "lng" not in valor:
        raise HTTPException(status_code=422, detail="Ubicación inválida")
    geo = {"lat": valor["lat"], "lng": valor["lng"]}
    precision = valor.get("precision_m", valor.get("precisionM"))
    if precision is not None:
        geo["precision_m"] = precision
    return geo


@router.post("/siniestros")
async def avisar(request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        return {"siniestroId": "SIN-441", "estado": "recibido"}
    idempotency_key = request.headers.get("idempotency-key")
    if not idempotency_key or not 8 <= len(idempotency_key) <= 128:
        raise HTTPException(status_code=422, detail="Idempotency-Key requerida")
    form = await request.form()
    numero = str(form.get("poliza") or "")
    fecha = str(form.get("fechaHecho") or "")
    descripcion = str(form.get("descripcion") or "").strip()
    lugar = str(form.get("lugar") or "").strip()
    if not numero or not fecha or not descripcion:
        raise HTTPException(status_code=422, detail="Faltan poliza, fecha o descripción")
    if len(descripcion) > 1000:
        raise HTTPException(status_code=422, detail="La descripción admite hasta 1000 caracteres")
    if len(lugar) > 200:
        raise HTTPException(status_code=422, detail="El lugar admite hasta 200 caracteres")
    archivos = form.getlist("archivos")
    if not archivos or len(archivos) > 5:
        raise HTTPException(status_code=422, detail="El aviso requiere de 1 a 5 archivos")
    evidencia = []
    tipos = []
    for archivo in archivos:
        tipo = (archivo.content_type or "").split(";")[0].strip().lower()
        if tipo not in _TIPOS:
            raise HTTPException(status_code=422, detail="Tipo de archivo no admitido")
        contenido = await archivo.read()
        if len(contenido) > 10 * 1024 * 1024:
            raise HTTPException(status_code=422, detail="Cada archivo admite hasta 10 MB")
        evidencia.append((archivo.filename or "evidencia", contenido, tipo))
        tipos.append(_TIPOS[tipo])
    uid = _contexto(usuario)["usuario_id"]
    nucleo = request.app.state.nucleo
    poliza = nucleo.obtener_por_numero(numero, usuario_id=uid)
    if _ajeno(poliza, uid):
        raise HTTPException(status_code=404, detail="No existe")
    poliza_id = str(poliza.get("poliza_id") or poliza.get("id") or "")
    if not poliza_id:
        raise HTTPException(status_code=404, detail="No existe")
    cotizacion = _cotizacion_de_poliza(nucleo, poliza)
    geo = _geo_aviso(form.get("geo"))
    datos = {
        "usuario_id": uid,
        "canal": "movil",
        "poliza": {
            "poliza_id": poliza_id,
            "numero": poliza.get("numero") or numero,
            "ramo": cotizacion.get("producto") or poliza.get("ramo") or "sin-clasificar",
            "estado": str(poliza.get("estado") or "vigente").lower(),
            "inicio_vigencia": poliza.get("inicio_vigencia") or "2020-01-01",
            "fin_vigencia": poliza.get("fin_vigencia") or "2099-01-01",
        },
        "fecha_hecho": fecha,
        "descripcion": descripcion,
        "geo": geo,
        "tipos_adjuntos": tipos,
    }
    if lugar:
        datos["lugar"] = lugar
    creado = nucleo.registrar_aviso(
        usuario_id=uid, datos=datos, archivos=evidencia, idempotency_key=idempotency_key
    )
    siniestro = creado.get("siniestro") if isinstance(creado, dict) else None
    if not isinstance(siniestro, dict):
        siniestro = creado if isinstance(creado, dict) else {}
    siniestro = _exigir(siniestro, "id", "estado")
    return {
        "siniestroId": str(siniestro.get("numero") or siniestro["id"]),
        "estado": siniestro["estado"],
    }


@router.get("/siniestros")
def siniestros(request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        return {
            "siniestros": [
                {
                    "siniestroId": "SIN-441",
                    "ramo": "Protección de dispositivo",
                    "resumen": "Pantalla rota",
                    "estado": "en_evaluacion",
                }
            ]
        }
    filas = request.app.state.nucleo.listar_siniestros(usuario_id=_contexto(usuario)["usuario_id"])
    if not isinstance(filas, list):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    return {"siniestros": [_siniestro_movil(fila) for fila in filas]}


@router.get("/siniestros/{siniestro_id}")
def detalle_siniestro(siniestro_id: str, request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        raise HTTPException(status_code=404, detail="No existe")
    uid = _contexto(usuario)["usuario_id"]
    detalle = request.app.state.nucleo.detalle_siniestro(siniestro_id, uid)
    if not isinstance(detalle, dict):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    return _detalle_movil(detalle)


@router.get("/pagos-automaticos")
def pagos() -> dict:
    return dict(PAYMENT)


@router.post("/oferta-hipotecaria")
def hipoteca(body: Hipoteca, request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        ready = body.consentimientoPerfil
        return {
            "ramo": "Vida crediticia",
            "estado": "oferta_vigente",
            "prima": 64000 if ready else 50000,
            "moneda": "COP",
            "factores": ["plazo", "valor del crédito"],
            "degradada": not ready,
        }
    if not body.consentimientoPerfil:
        return _hipoteca_degradada()
    nucleo = request.app.state.nucleo
    cliente_id = _contexto(usuario)["usuario_id"]
    nucleo.otorgar_consentimiento(cliente_id)
    return _hipoteca_movil(
        nucleo.solicitar_oferta_hipotecario(
            idempotency_key=str(uuid.uuid4()),
            cliente_id=cliente_id,
        )
    )


@router.get("/avisos")
def avisos() -> dict:
    return {
        "avisos": [
            {"tipo": "vencimiento", "poliza": "POL-88219-CO", "venceEn": "2027-03-12"},
            {"tipo": "renovacion", "poliza": "POL-88219-CO", "estado": "vigente"},
        ]
    }


def _tarjeta_inicio(cotizacion_id: str, ramo: str) -> dict:
    return {"cotizacionId": cotizacion_id, "ramo": ramo, "estado": "oferta_vigente"}


def _inicio_muestra() -> dict:
    oferta = _tarjeta_inicio("COT-1042", "Protección de dispositivo")
    return {
        "ofertaVigente": oferta,
        "cotizacionesPendientes": [oferta],
        "poliza": {
            "numero": "POL-88219-CO",
            "ramo": "Protección de dispositivo",
            "estado": "vigente",
        },
        "siniestroEnCurso": {"siniestroId": "SIN-441", "estado": "en_evaluacion"},
        "hipotecario": None,
    }


def _cotizaciones_pendientes(nucleo, usuario: dict) -> list:
    pagina = nucleo.listar_cotizaciones_usuario(
        usuario_id=_contexto(usuario)["usuario_id"],
        tamano=20,
    )
    if not isinstance(pagina, dict) or not isinstance(pagina.get("items"), list):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    tarjetas = []
    for item in pagina["items"]:
        item = _exigir(item, "cotizacion_id", "producto")
        producto = item["producto"]
        ramo, _ = presentar(producto)
        tarjetas.append(_tarjeta_inicio(item["cotizacion_id"], ramo))
    return tarjetas


@router.get("/inicio")
def inicio(request: Request, usuario: dict = Depends(require_customer)) -> dict:
    cuerpo = _inicio_muestra()
    if not es_v1(request):
        return cuerpo
    nucleo = request.app.state.nucleo
    token = token_saliente.get()

    def _leer(funcion):
        token_saliente.set(token)
        try:
            return funcion()
        except HTTPException:
            return None

    with ThreadPoolExecutor(max_workers=3) as pool:
        pendientes_fut = pool.submit(_leer, lambda: _cotizaciones_pendientes(nucleo, usuario))
        polizas_fut = pool.submit(_leer, lambda: _polizas_proyectadas(nucleo, usuario))
        siniestros_fut = pool.submit(
            _leer, lambda: nucleo.listar_siniestros(usuario_id=_contexto(usuario)["usuario_id"])
        )
        pendientes = pendientes_fut.result() or []
        filas = polizas_fut.result() or []
        siniestros = siniestros_fut.result() or []
    cuerpo["cotizacionesPendientes"] = pendientes
    cuerpo["ofertaVigente"] = pendientes[0] if pendientes else None
    if not filas:
        cuerpo["poliza"] = None
    else:
        primera = filas[0]
        cuerpo["poliza"] = {
            "numero": primera["numero"],
            "ramo": primera["ramo"],
            "estado": primera["estado"],
        }
    if isinstance(siniestros, list) and siniestros:
        primero = _exigir(siniestros[0], "id", "estado")
        cuerpo["siniestroEnCurso"] = {"siniestroId": str(primero["id"]), "estado": primero["estado"]}
    else:
        cuerpo["siniestroEnCurso"] = None
    return cuerpo


class PerfilEntrada(BaseModel):
    nombre: str
    apellidos: str


def _perfil_movil(usuario: dict) -> dict:
    usuario = _exigir(usuario, "usuario_id", "email")
    return {
        "usuarioId": str(usuario["usuario_id"]),
        "correo": usuario["email"],
        "nombre": usuario.get("nombre") or "",
        "apellidos": usuario.get("apellidos") or "",
        "documento": usuario.get("numero_documento") or "",
    }


@router.get("/perfil")
def leer_perfil(request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        raise HTTPException(status_code=404, detail="No existe")
    return _perfil_movil(
        request.app.state.nucleo.obtener_usuario(_contexto(usuario)["usuario_id"])
    )


@router.patch("/perfil")
def guardar_perfil(
    body: PerfilEntrada, request: Request, usuario: dict = Depends(require_customer)
) -> dict:
    if not es_v1(request):
        raise HTTPException(status_code=404, detail="No existe")
    return _perfil_movil(
        request.app.state.nucleo.actualizar_perfil(
            _contexto(usuario)["usuario_id"], nombre=body.nombre, apellidos=body.apellidos
        )
    )


@router.post("/avisos/token")
def registrar_token(body: PushToken) -> dict:
    return {"estado": "aceptada", "plataforma": body.plataforma}


@router.get("/avisos/push")
def push() -> dict:
    return {
        "tipo": "vencimiento",
        "titulo": "Tu póliza vence",
        "cuerpo": "En 7 días",
        "destino": "aviso-vencimiento",
        "poliza": "POL-88219-CO",
    }


@router.get("/prestadores")
def prestadores() -> dict:
    return {
        "prestadores": [
            {"id": "PR-1", "nombre": "Taller Norte", "distanciaKm": 1.2, "zona": "Chapinero"},
            {"id": "PR-2", "nombre": "Taller Sur", "distanciaKm": 3.4, "zona": "Kennedy"},
        ]
    }


@router.post("/asistencias")
def asistencia(body: Asistencia) -> dict:
    if not body.prestadorId:
        raise HTTPException(status_code=400, detail="Prestador requerido")
    return {"asistenciaId": "AS-18", "estado": "registrada"}
