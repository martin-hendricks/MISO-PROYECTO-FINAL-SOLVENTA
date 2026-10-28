from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..clients.bff_web import DETALLE_INCOMPLETA, autorizacion, es_v1, proyectar
from ..dependencies import require_customer

router = APIRouter(
    prefix="/cliente",
    tags=["cliente"],
    dependencies=[Depends(require_customer())],
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


class Cotizacion(BaseModel):
    ramo: str
    datosRiesgo: dict
    rol: str | None = None


class Aceptar(BaseModel):
    cotizacionId: str


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


CLAVES_OFERTA = ("cotizacionId", "ramo", "estado", "prima", "moneda", "venceEn")
CLAVES_POLIZA = ("numero", "ramo", "estado", "venceEn")
CLAVES_BILLETERA = ("numero", "ramo", "resumen", "estado", "venceEn")
CLAVES_DETALLE = (*CLAVES_BILLETERA, "queHacer")
CLAVES_PAGO = ("siniestroId", "poliza", "umbral", "monto", "moneda", "estado")
CLAVES_HIPOTECA = ("ramo", "estado", "prima", "moneda", "factores", "degradada")
CLAVES_INICIO = ("ofertaVigente", "poliza", "siniestroEnCurso", "hipotecario")


def _offer(cotizacion_id: str) -> dict:
    body = dict(OFFER)
    body["cotizacionId"] = cotizacion_id
    return body


def _traducir_aceptar(cuerpo: dict) -> dict:
    resultado = cuerpo.get("resultado") if isinstance(cuerpo, dict) else None
    if resultado == "EMITIDA":
        return proyectar(cuerpo.get("poliza"), CLAVES_POLIZA)
    if resultado == "RECHAZADA" and isinstance(cuerpo, dict) and "motivo" in cuerpo:
        return {"estado": "rechazada", "motivo": cuerpo["motivo"]}
    raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)


def _traducir_billetera(cuerpo: dict) -> dict:
    polizas = cuerpo.get("polizas") if isinstance(cuerpo, dict) else None
    if not isinstance(polizas, list):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    return {"polizas": [proyectar(item, CLAVES_BILLETERA) for item in polizas]}


def _web(request: Request, metodo: str, ruta: str, cuerpo: dict | None = None) -> dict:
    return request.app.state.bff_web.enviar(
        metodo,
        ruta,
        json=cuerpo,
        autorizacion=autorizacion(request),
    )


@router.post("/cotizaciones")
def cotizar(body: Cotizacion, request: Request) -> dict:
    if es_v1(request):
        return proyectar(
            _web(
                request,
                "POST",
                "/v1/cliente/cotizaciones",
                {"ramo": body.ramo, "datosRiesgo": body.datosRiesgo},
            ),
            CLAVES_OFERTA,
        )
    return _offer(OFFER["cotizacionId"])


@router.get("/cotizaciones/{cotizacion_id}")
def reconsultar(cotizacion_id: str, request: Request) -> dict:
    if es_v1(request):
        return proyectar(
            _web(request, "GET", f"/v1/cliente/cotizaciones/{cotizacion_id}"),
            CLAVES_OFERTA,
        )
    return _offer(cotizacion_id)


@router.post("/polizas")
def aceptar(body: Aceptar, request: Request) -> dict:
    if es_v1(request):
        return _traducir_aceptar(
            _web(request, "POST", "/v1/cliente/polizas", {"cotizacionId": body.cotizacionId})
        )
    if body.cotizacionId == "COT-RECHAZADA":
        return {"estado": "rechazada", "motivo": "Valor del equipo fuera de rango"}
    return dict(POLICY)


@router.get("/polizas")
def billetera(request: Request) -> dict:
    if es_v1(request):
        return _traducir_billetera(_web(request, "GET", "/v1/cliente/polizas"))
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


@router.get("/polizas/{numero}")
def detalle(numero: str, request: Request) -> dict:
    if es_v1(request):
        return proyectar(_web(request, "GET", f"/v1/cliente/polizas/{numero}"), CLAVES_DETALLE)
    return {
        "numero": numero,
        "ramo": "Protección de dispositivo",
        "resumen": "Robo y Pantalla",
        "estado": "vigente",
        "venceEn": "2027-03-12",
        "queHacer": "Toma la foto del daño y anota fecha y lugar.",
    }


@router.post("/siniestros")
def avisar(body: Aviso) -> dict:
    return {"siniestroId": "SIN-441", "estado": "recibido"}


@router.get("/siniestros")
def siniestros() -> dict:
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


@router.get("/pagos-automaticos")
def pagos(request: Request) -> dict:
    if es_v1(request):
        return proyectar(_web(request, "GET", "/v1/cliente/pagos-automaticos"), CLAVES_PAGO)
    return dict(PAYMENT)


@router.post("/oferta-hipotecaria")
def hipoteca(body: Hipoteca, request: Request) -> dict:
    if es_v1(request):
        return proyectar(
            _web(request, "POST", "/v1/cliente/oferta-hipotecaria", body.model_dump()),
            CLAVES_HIPOTECA,
        )
    ready = body.consentimientoPerfil
    return {
        "ramo": "Vida crediticia",
        "estado": "oferta_vigente",
        "prima": 64000 if ready else 50000,
        "moneda": "COP",
        "factores": ["plazo", "valor del crédito"],
        "degradada": not ready,
    }


@router.get("/avisos")
def avisos() -> dict:
    return {
        "avisos": [
            {"tipo": "vencimiento", "poliza": "POL-88219-CO", "venceEn": "2027-03-12"},
            {"tipo": "renovacion", "poliza": "POL-88219-CO", "estado": "vigente"},
        ]
    }


@router.get("/inicio")
def inicio(request: Request) -> dict:
    if es_v1(request):
        return proyectar(_web(request, "GET", "/v1/cliente/inicio"), CLAVES_INICIO)
    return {
        "ofertaVigente": {
            "cotizacionId": "COT-1042",
            "ramo": "Protección de dispositivo",
            "estado": "oferta_vigente",
        },
        "poliza": {
            "numero": "POL-88219-CO",
            "ramo": "Protección de dispositivo",
            "estado": "vigente",
        },
        "siniestroEnCurso": {"siniestroId": "SIN-441", "estado": "en_evaluacion"},
        "hipotecario": None,
    }


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
