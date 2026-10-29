import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..clients.nucleo import DETALLE_INCOMPLETA
from ..dependencies import require_customer

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
RAMO_SIN_CLASIFICAR = "Sin clasificar"
_NAMESPACE = uuid.UUID("5f4d3a2b-0000-4000-8000-000000000000")
RAMO_A_PRODUCTO = {
    "Protección de dispositivo": "proteccion-dispositivo",
    "Vida crediticia": "vida-crediticia",
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


def es_v1(request: Request) -> bool:
    return request.url.path.startswith("/v1/")


def _offer(cotizacion_id: str) -> dict:
    body = dict(OFFER)
    body["cotizacionId"] = cotizacion_id
    return body


def _producto_de(ramo: str) -> str:
    return RAMO_A_PRODUCTO.get(ramo, ramo.strip().lower().replace(" ", "-"))


def _uuid_desde(*partes: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, "|".join(partes)))


def _contexto(correo: str) -> dict:
    return {
        "usuario_id": _uuid_desde("usuario", correo),
        "socio_id": _uuid_desde("socio", correo),
        "consentimiento_id": _uuid_desde("consentimiento", correo),
        "perfil_id": _uuid_desde("perfil", correo),
    }


def _exigir(cuerpo: dict, *claves: str) -> dict:
    if not isinstance(cuerpo, dict) or any(clave not in cuerpo for clave in claves):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    return cuerpo


def _oferta_movil(datos: dict, ramo: str) -> dict:
    datos = _exigir(datos, "cotizacion_id", "estado", "prima", "moneda", "vence_en")
    return {
        "cotizacionId": datos["cotizacion_id"],
        "ramo": ramo,
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
    cuerpo = {
        "numero": poliza["numero"],
        "ramo": cotizacion.get("producto") or RAMO_SIN_CLASIFICAR,
        "resumen": ", ".join(nombres) or "Sin coberturas",
        "estado": poliza["estado"],
        "venceEn": poliza["fin_vigencia"],
    }
    if detalle:
        cuerpo["queHacer"] = QUE_HACER
    return cuerpo


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
    contexto = _contexto(usuario["sub"])
    datos = request.app.state.nucleo.cotizar(
        idempotency_key=str(uuid.uuid4()),
        usuario_id=contexto["usuario_id"],
        socio_id=contexto["socio_id"],
        consentimiento_id=contexto["consentimiento_id"],
        producto=_producto_de(body.ramo),
        canal=CANAL,
        datos_riesgo=body.datosRiesgo,
    )
    return _oferta_movil(datos, body.ramo)


@router.get("/cotizaciones/{cotizacion_id}")
def reconsultar(cotizacion_id: str, request: Request) -> dict:
    if not es_v1(request):
        return _offer(cotizacion_id)
    datos = request.app.state.nucleo.reconsultar(cotizacion_id)
    datos = _exigir(datos, "producto")
    return _oferta_movil(datos, datos["producto"])


@router.post("/polizas")
def aceptar(body: Aceptar, request: Request, usuario: dict = Depends(require_customer)) -> dict:
    if not es_v1(request):
        if body.cotizacionId == "COT-RECHAZADA":
            return {"estado": "rechazada", "motivo": "Valor del equipo fuera de rango"}
        return dict(POLICY)
    nucleo = request.app.state.nucleo
    contexto = _contexto(usuario["sub"])
    aceptacion = _exigir(
        nucleo.aceptar_oferta(
            cotizacion_id=body.cotizacionId,
            idempotency_key=str(uuid.uuid4()),
            perfil_id=contexto["perfil_id"],
            score=SCORE,
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
    return {
        "numero": poliza["numero"],
        "ramo": cotizacion["producto"],
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
    nucleo = request.app.state.nucleo
    polizas = nucleo.listar_polizas(usuario_id=_contexto(usuario["sub"])["usuario_id"], limite=20)
    if not isinstance(polizas, list):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    return {
        "polizas": [
            _poliza_movil(poliza, _cotizacion_de_poliza(nucleo, poliza), detalle=False)
            for poliza in polizas
        ]
    }


@router.get("/polizas/{numero}")
def detalle(numero: str, request: Request) -> dict:
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
    poliza = nucleo.obtener_por_numero(numero)
    return _poliza_movil(poliza, _cotizacion_de_poliza(nucleo, poliza), detalle=True)


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
    cliente_id = _contexto(usuario["sub"])["usuario_id"]
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


@router.get("/inicio")
def inicio() -> dict:
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
