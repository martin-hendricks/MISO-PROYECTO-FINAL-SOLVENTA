import asyncio
import uuid
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..clients.base import RechazoDelNucleo, RecursoNoEncontrado, ServicioNoDisponible
from ..clients.ms_cotizacion import ClienteMsCotizacion
from ..clients.ms_pagos import ClienteMsPagos
from ..clients.ms_perfilamiento import ClienteMsPerfilamiento
from ..clients.ms_identidad import ClienteMsIdentidad
from ..clients.ms_polizas import ClienteMsPolizas
from ..clients.ms_siniestros import ClienteMsSiniestros
from ..ramos import PRODUCTOS, presentar, producto_de
from ..dependencies import (
    obtener_cliente_cotizacion,
    obtener_cliente_identidad,
    obtener_cliente_pagos,
    obtener_cliente_perfilamiento,
    obtener_cliente_polizas,
    obtener_cliente_siniestros,
    require_roles,
)

router = APIRouter(
    prefix="/cliente",
    tags=["cliente"],
    dependencies=[Depends(require_roles("cliente"))],
)

# Payload del JWT del cliente: `sub` es su correo y de él salen sus ids.
Sesion = Annotated[dict, Depends(require_roles("cliente"))]

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
REFUSAL = {"estado": "rechazada", "motivo": "Valor del equipo fuera de rango"}
PAYMENT = {
    "siniestroId": "SIN-220",
    "poliza": "POL-11002-CO",
    "umbral": "retraso mayor a 120 min",
    "monto": 250000,
    "moneda": "COP",
    "estado": "pagado",
}

RAMO_A_PRODUCTO = {nombre: codigo for codigo, (nombre, _) in PRODUCTOS.items()}

RAMO_VIDA_CREDITICIA = "Vida crediticia"
PRODUCTO_VIDA_CREDITICIA = RAMO_A_PRODUCTO[RAMO_VIDA_CREDITICIA]

# Namespace fijo y arbitrario, solo para derivar UUIDs deterministas v5 a
# partir de datos ya disponibles (correo de sesión). No tiene significado de
# negocio, solo evita colisiones triviales con otros usos de uuid5.
# Código con el que ms-polizas rechaza una emisión cuya firma no fue exitosa (HU-17).
FIRMA_NO_EXITOSA = "firma_no_exitosa"

_NAMESPACE_SOLVENTA = uuid.UUID("5f4d3a2b-0000-4000-8000-000000000000")


def _producto_de(ramo: str) -> str:
    codigo = producto_de(ramo)
    if codigo is None:
        raise HTTPException(status_code=404, detail="ramo_no_disponible")
    return codigo


def _uuid_desde(*partes: str) -> UUID:
    return uuid.uuid5(_NAMESPACE_SOLVENTA, "|".join(partes))


def _exigir_dueno(recurso: dict, uid: UUID) -> None:
    dueno = recurso.get("usuario_id")
    if dueno is not None and str(dueno) != str(uid):
        raise HTTPException(status_code=404, detail="No existe")


def contexto_canonico(usuario: dict) -> "ContextoUsuario":
    """El uid del JWT es el usuario_id de ms-identidad. Los ids de apoyo
    salen de ese uid, nunca del correo."""
    uid = str(usuario.get("uid") or "")
    if not uid:
        raise HTTPException(status_code=401, detail="Token invalido")
    return ContextoUsuario(uid, canonico=True)


class ContextoUsuario:
    """Deriva identificadores que hoy no existen en el canal web.

    El JWT de bff-web solo trae `sub` (correo) y `rol` (ver
    app/dependencies.py); no hay ms-identidad real todavía que resuelva un
    usuario_id/socio_id/consentimiento_id/perfil_id de verdad a partir de la
    sesión. Mientras ese servicio no exista, se derivan UUIDs deterministas
    (uuid5) a partir del correo de la sesión: esto permite que el mismo
    usuario reutilice siempre el mismo usuario_id frente a ms-cotizacion
    (útil para idempotencia/consistencia en pruebas), pero NO es una
    resolución de identidad real ni debe tratarse como tal en producción.
    """

    def __init__(self, correo: str, *, canonico: bool = False) -> None:
        if canonico:
            self.usuario_id = UUID(correo)
            semilla = str(self.usuario_id)
        else:
            self.usuario_id = _uuid_desde("usuario", correo)
            semilla = correo
        self.socio_id = _uuid_desde("socio", semilla)
        self.consentimiento_id = _uuid_desde("consentimiento", semilla)
        self.perfil_id = _uuid_desde("perfil", semilla)


def _idempotency_key() -> str:
    return str(uuid.uuid4())


class Cotizacion(BaseModel):
    ramo: str
    datosRiesgo: dict
    clienteId: str | None = None


class Aceptar(BaseModel):
    cotizacionId: str


class Credito(BaseModel):
    valor: int = Field(gt=0)
    plazoMeses: int = Field(gt=0)


class Hipoteca(BaseModel):
    credito: Credito
    consentimientoPerfil: bool


def _offer(cotizacion_id: str) -> dict:
    body = dict(OFFER)
    body["cotizacionId"] = cotizacion_id
    return body


def _cotizacion_salida(datos: dict, ramo: str, descripcion: str = "") -> dict:
    """Traduce la salida real de ms-cotizacion al shape que el canal web ya
    espera, para no romper el contrato existente del frontend.

    primaNeta/expedicion (SOLV-103): ms-cotizacion ya devuelve el desglose
    completo (prima_neta, gastos_expedicion) desde HU-4/HU-6 -- antes este
    traductor solo exponía el total "prima" y descartaba el desglose."""
    return {
        "cotizacionId": datos["cotizacion_id"],
        "ramo": ramo,
        "descripcion": descripcion,
        "estado": datos["estado"],
        "prima": datos["prima"],
        "primaNeta": datos["prima_neta"],
        "expedicion": datos["gastos_expedicion"],
        "moneda": datos["moneda"],
        "venceEn": datos["vence_en"],
    }


def _dato_riesgo_salida(dato: dict) -> dict:
    """Traduce DatoRiesgoSalida (snake_case, ms-cotizacion) a camelCase
    (convención del contrato de bff-web)."""
    salida = {"nombre": dato["nombre"], "tipo": dato["tipo"]}
    if dato["tipo"] == "rango":
        salida["minimo"] = dato["minimo"]
        salida["maximo"] = dato["maximo"]
    else:
        salida["valores"] = dato["valores"]
    return salida


def _catalogo_salida(producto: dict, ramo: str) -> dict:
    """Traduce ProductoSalida (ms-cotizacion, HU-1/HU-2) al shape propuesto
    para SOLV-245: el frontend bloquea "Continuar" con estos rangos antes de
    cotizar, en vez de esperar al 422 de dato fuera de rango."""
    codigo = _producto_de(ramo)
    _, descripcion = presentar(codigo)
    return {
        "ramo": ramo,
        "descripcion": producto.get("descripcion") or descripcion,
        "disponible": producto.get("disponible", True),
        "nombre": producto["nombre"],
        "moneda": producto["moneda"],
        "coberturas": [
            {
                "codigo": c["codigo"],
                "nombre": c["nombre"],
                "limite": c["limite"],
                "unidadLimite": c["unidad_limite"],
            }
            for c in producto["coberturas"]
        ],
        "datosRiesgo": [_dato_riesgo_salida(d) for d in producto["datos_riesgo"]],
    }


@router.get("/catalogo/{ramo}")
async def catalogo(
    ramo: str,
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
) -> dict:
    """SOLV-245: rangos válidos de los datos de riesgo de un ramo, para que
    el frontend bloquee "Continuar" antes de cotizar (RecursoNoEncontrado ya
    propaga 404 si el ramo no mapea a ningún producto real)."""
    producto = await cliente_cotizacion.obtener_producto(_producto_de(ramo))
    return _catalogo_salida(producto, ramo)


@router.post("/cotizaciones")
async def cotizar(
    body: Cotizacion,
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
) -> dict:
    if body.clienteId:
        raise HTTPException(status_code=400, detail="La venta asistida no es de este canal")

    contexto = contexto_canonico(usuario)
    producto = _producto_de(body.ramo)

    datos = await cliente_cotizacion.cotizar(
        idempotency_key=_idempotency_key(),
        usuario_id=contexto.usuario_id,
        socio_id=contexto.socio_id,
        consentimiento_id=contexto.consentimiento_id,
        producto=producto,
        canal="web",
        datos_riesgo=body.datosRiesgo,
    )
    _, descripcion = presentar(producto)
    return _cotizacion_salida(datos, body.ramo, descripcion)


@router.get("/cotizaciones/{cotizacion_id}")
async def reconsultar(
    cotizacion_id: str,
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
) -> dict:
    datos = await cliente_cotizacion.reconsultar(cotizacion_id, contexto_canonico(usuario).usuario_id)
    ramo, descripcion = presentar(datos.get("producto"))
    return _cotizacion_salida(datos, ramo, descripcion)


@router.post("/polizas")
async def emitir(
    body: Aceptar,
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    cliente_pagos: Annotated[ClienteMsPagos, Depends(obtener_cliente_pagos)],
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
) -> dict:
    """Aceptar la oferta y emitir la póliza. Flujo real:

    1. ms-cotizacion POST /v1/cotizaciones/{id}/aceptacion -- ya orquesta la
       decisión de suscripción internamente (el BFF no llama a
       ms-suscripcion por separado). Devuelve oferta_id + decision/motivo.
    2. Si la decisión fue RECHAZADA, el flujo se detiene aquí: un rechazo de
       suscripción es un resultado de negocio válido, no una falla técnica
       del sistema, así que se devuelve 200 con
       {resultado: "RECHAZADA", motivo} en vez de propagar un error HTTP.
       No se cobra ni se intenta emitir sobre una suscripción rechazada.
    3. Si fue ACEPTADA: ms-pagos POST /v1/pagos/primas cobra la prima.
    4. ms-polizas POST /v1/polizas emite la póliza con el pago confirmado.
    5. Se reconsulta la cotización (ms-cotizacion GET /v1/cotizaciones/{id})
       para resolver el producto real de la póliza emitida -- ms-polizas no
       guarda ramo/producto, solo coberturas sueltas.

    Si cualquier paso de I/O falla por un motivo técnico (servicio caído,
    recurso no encontrado, rechazo de validación del núcleo), la excepción
    tipificada (ServicioNoDisponible/RecursoNoEncontrado/RechazoDelNucleo) se
    propaga sin capturar y los exception handlers de main.py la traducen a
    503/404/409/422. Si el paso de pago falla, la emisión nunca se ejecuta.
    """
    # TODO: mismo placeholder de identidad que en cotizar() -- no hay
    # ms-identidad real para resolver el correo de la sesión a un contexto.
    contexto = contexto_canonico(usuario)

    # TODO: `score` es un stub fijo documentado: no hay ms-perfilamiento
    # conectado aún que calcule un score real de riesgo/crédito para el
    # perfil del cliente. Cuando ms-perfilamiento esté disponible, este valor
    # debe venir de una llamada real a ese servicio en vez de una constante.
    score_stub = Decimal("0.5000")

    aceptacion = await cliente_cotizacion.aceptar_oferta(
        cotizacion_id=body.cotizacionId,
        idempotency_key=_idempotency_key(),
        perfil_id=contexto.perfil_id,
        score=score_stub,
        usuario_id=contexto.usuario_id,
    )

    if aceptacion["decision"].upper() != "ACEPTADA":
        # ms-suscripcion solo entrega un código; el web espera {codigo, mensaje}.
        motivo = aceptacion["motivo"]
        return {"resultado": "RECHAZADA", "motivo": {"codigo": motivo, "mensaje": motivo}}

    oferta_id = UUID(aceptacion["oferta_id"])
    solicitud_id = UUID(aceptacion["cotizacion_id"])

    # TODO: `token_medio_pago` es un placeholder -- el canal web todavía no
    # captura/tokeniza un medio de pago real (no hay integración con una
    # pasarela ni un campo en el body de esta ruta). Debe reemplazarse cuando
    # el frontend capture el medio de pago real del cliente.
    pago = await cliente_pagos.cobrar_prima(
        solicitud_id=solicitud_id,
        oferta_id=oferta_id,
        usuario_id=contexto.usuario_id,
        monto=Decimal(str(aceptacion["prima"])),
        token_medio_pago="stub-medio-pago",
    )

    cobertura_minima = [
        {
            "nombre": aceptacion.get("estado", "cobertura-base"),
            "suma_asegurada": str(aceptacion["prima"]),
            "deducible": "0",
        }
    ]
    try:
        poliza = await cliente_polizas.emitir(
            solicitud_id=solicitud_id,
            oferta_id=oferta_id,
            usuario_id=contexto.usuario_id,
            token_pago_confirmado=UUID(str(pago["id"])),
            coberturas=cobertura_minima,
        )
    except RechazoDelNucleo as rechazo:
        # HU-17: una firma no exitosa es un resultado de negocio, igual que un
        # rechazo de suscripción; cualquier otro rechazo sigue propagándose.
        if rechazo.codigo != FIRMA_NO_EXITOSA:
            raise
        return {"resultado": "RECHAZADA", "motivo": {"codigo": rechazo.codigo, "mensaje": rechazo.mensaje}}

    cotizacion = await cliente_cotizacion.reconsultar(str(solicitud_id))
    ramo, descripcion = presentar(cotizacion.get("producto"))

    return {
        "resultado": "EMITIDA",
        "poliza": {
            "numero": poliza["numero"],
            "ramo": ramo,
            "descripcion": descripcion,
            "producto": ramo,
            "estado": poliza["estado"],
            "venceEn": poliza.get("fin_vigencia", ""),
            "inicioVigencia": poliza.get("inicio_vigencia", ""),
            "finVigencia": poliza.get("fin_vigencia", ""),
            "moneda": aceptacion.get("moneda", ""),
            "primaTotal": float(aceptacion["prima"]),
        },
    }


RAMO_SIN_CLASIFICAR = "Sin clasificar"


async def _cotizacion_de_poliza(cliente_cotizacion: ClienteMsCotizacion, poliza: dict) -> dict:
    """Reconsulta ms-cotizacion por oferta_id (ver
    ClienteMsCotizacion.reconsultar_por_oferta) para resolver producto, prima
    y moneda, que ms-polizas no guarda. Si la cotización original ya no
    existe o el servicio no responde, se degrada a {} en vez de tumbar toda la
    respuesta de billetera/detalle: son datos de presentación, no deben
    bloquear ver la póliza."""
    try:
        return await cliente_cotizacion.reconsultar_por_oferta(UUID(str(poliza["oferta_id"])))
    except (RecursoNoEncontrado, ServicioNoDisponible, RechazoDelNucleo):
        return {}


def _poliza_billetera(poliza: dict, cotizacion: dict) -> dict:
    ramo, descripcion = presentar(cotizacion.get("producto"))
    return {
        "numero": poliza["numero"],
        "ramo": ramo,
        "descripcion": descripcion,
        "producto": ramo,
        "resumen": ", ".join(c["nombre"] for c in poliza["coberturas"]) or "Sin coberturas",
        "estado": poliza["estado"].upper(),
        "venceEn": poliza["fin_vigencia"],
        "inicioVigencia": poliza["inicio_vigencia"],
        "finVigencia": poliza["fin_vigencia"],
        "moneda": cotizacion.get("moneda", ""),
        "primaTotal": float(cotizacion.get("prima", 0)),
    }


@router.get("/polizas")
async def billetera(
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
) -> dict:
    # TODO: mismo placeholder de identidad que en cotizar()/emitir() -- no
    # hay ms-identidad real para resolver el correo de la sesión a un
    # usuario_id. El usuario_id derivado es estable dentro de este proceso.
    contexto = contexto_canonico(usuario)

    polizas = await cliente_polizas.listar_por_usuario(contexto.usuario_id, limite=20)
    cotizaciones = await asyncio.gather(*(_cotizacion_de_poliza(cliente_cotizacion, p) for p in polizas))
    return {"polizas": [_poliza_billetera(p, c) for p, c in zip(polizas, cotizaciones, strict=True)]}


# "queHacer" es contenido estático de ayuda al usuario (guía de qué hacer
# frente a un siniestro): no depende de ningún microservicio, por eso queda
# fijo aquí en vez de requerir una integración con ms-siniestros/ms-parametrico.
QUE_HACER_POR_DEFECTO = (
    "Si necesitas usar tu póliza, documenta lo ocurrido (foto, fecha y lugar) "
    "y comunícate con soporte para iniciar el proceso de reclamación."
)


@router.get("/polizas/{numero}")
async def detalle(
    numero: str,
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
) -> dict:
    poliza = await cliente_polizas.obtener_por_numero(numero, contexto_canonico(usuario).usuario_id)
    _exigir_dueno(poliza, contexto_canonico(usuario).usuario_id)
    salida = _poliza_billetera(poliza, await _cotizacion_de_poliza(cliente_cotizacion, poliza))
    salida["coberturas"] = [
        {
            "nombre": c["nombre"],
            "sumaAsegurada": float(c["suma_asegurada"]),
            "deducible": float(c["deducible"]),
        }
        for c in poliza["coberturas"]
    ]
    salida["queHacer"] = QUE_HACER_POR_DEFECTO
    return salida


# TODO: no hay microservicio de pagos automáticos/recurrentes conectado
# (ms-pagos en el PR abierto solo cubre el cobro puntual de la prima al
# emitir, no el ciclo de pagos automáticos de siniestros) -- falta definir
# ese contrato en el núcleo antes de integrar esta ruta.
@router.get("/pagos-automaticos")
def pagos() -> dict:
    return dict(PAYMENT)


SIN_CONSENTIMIENTO = "sin_consentimiento"


async def ofertar_vida_crediticia(
    contexto: ContextoUsuario,
    credito: Credito,
    canal: str,
    cliente_perfilamiento: ClienteMsPerfilamiento,
    cliente_cotizacion: ClienteMsCotizacion,
    asesor_id: UUID | None = None,
    cliente_ref: str | None = None,
) -> dict:
    """Oferta de vida hipotecario (HU-162) para el cliente y el asesor.

    1. Otorga el consentimiento de perfilamiento (HU-53) y pide a
       ms-perfilamiento el perfil y sus factores explicables (HU-54/55).
    2. Cotiza `vida-crediticia` en ms-cotizacion con el valor y el plazo del
       crédito. ms-cotizacion toma el factor de ese mismo perfil
       (IPerfilRiesgo), así que la prima mostrada es la que se cobra al
       emitir con el `cotizacionId` (HU-114).

    Si ms-perfilamiento no responde, la originación no se cancela (HU-56):
    se cotiza igual, ms-cotizacion aplica su valor de respaldo y la oferta
    sale marcada como degradada, sin factores.
    """
    cliente_id = str(contexto.usuario_id)
    factores: list[dict] = []
    perfil_degradado = True
    try:
        await cliente_perfilamiento.otorgar_consentimiento(cliente_id)
        perfil = await cliente_perfilamiento.solicitar_oferta_hipotecario(
            idempotency_key=_idempotency_key(),
            cliente_id=cliente_id,
        )
        factores = [{"factor": f["factor"], "impacto": f["impacto"]} for f in perfil["factores"]]
        perfil_degradado = perfil["degradado"]
    except ServicioNoDisponible:
        pass

    datos = await cliente_cotizacion.cotizar(
        idempotency_key=_idempotency_key(),
        usuario_id=contexto.usuario_id,
        socio_id=contexto.socio_id,
        consentimiento_id=contexto.consentimiento_id,
        producto=PRODUCTO_VIDA_CREDITICIA,
        canal=canal,
        datos_riesgo={"valorCredito": credito.valor, "plazoMeses": credito.plazoMeses},
        asesor_id=asesor_id,
        cliente_ref=cliente_ref,
    )
    return {
        **_cotizacion_salida(datos, RAMO_VIDA_CREDITICIA),
        "factores": factores,
        "degradada": perfil_degradado or datos.get("factor_riesgo_origen") == "respaldo",
        "credito": {"valor": credito.valor, "plazoMeses": credito.plazoMeses},
    }


@router.post("/oferta-hipotecaria")
async def hipoteca(
    body: Hipoteca,
    cliente_perfilamiento: Annotated[ClienteMsPerfilamiento, Depends(obtener_cliente_perfilamiento)],
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
) -> dict:
    """Oferta de vida hipotecario del cliente (HU-105).

    `consentimientoPerfil=False` no llama a ningún servicio (HU-53: nunca se
    asume consentimiento) y no inventa una prima: el canal vuelve a Inicio.
    """
    if not body.consentimientoPerfil:
        return {"ramo": RAMO_VIDA_CREDITICIA, "estado": SIN_CONSENTIMIENTO}

    return await ofertar_vida_crediticia(
        contexto_canonico(usuario), body.credito, "web", cliente_perfilamiento, cliente_cotizacion
    )


def _vacio(exc: Exception) -> bool:
    return isinstance(exc, (RecursoNoEncontrado, ServicioNoDisponible, RechazoDelNucleo))


@router.get("/inicio")
async def inicio(
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
    cliente_siniestros: Annotated[ClienteMsSiniestros, Depends(obtener_cliente_siniestros)],
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
) -> dict:
    contexto = contexto_canonico(usuario)
    pendientes: list[dict] = []
    try:
        pagina = await cliente_cotizacion.listar_por_usuario(contexto.usuario_id)
        for item in pagina.get("items") or []:
            ramo, _ = presentar(item.get("producto"))
            pendientes.append(
                {"cotizacionId": item.get("cotizacion_id"), "ramo": ramo, "estado": "oferta_vigente"}
            )
    except Exception as exc:
        if not _vacio(exc):
            raise
    poliza = None
    try:
        filas = await cliente_polizas.listar_por_usuario(contexto.usuario_id, limite=1)
        if filas:
            ramo, _ = presentar((await _cotizacion_de_poliza(cliente_cotizacion, filas[0])).get("producto"))
            poliza = {"numero": filas[0]["numero"], "ramo": ramo, "estado": str(filas[0]["estado"]).lower()}
    except Exception as exc:
        if not _vacio(exc):
            raise
    siniestro = None
    try:
        abiertos = await cliente_siniestros.listar(usuario_id=contexto.usuario_id)
        if abiertos:
            primero = abiertos[0]
            siniestro = {"siniestroId": str(primero["id"]), "estado": primero["estado"]}
    except Exception as exc:
        if not _vacio(exc):
            raise
    return {
        "ofertaVigente": pendientes[0] if pendientes else None,
        "cotizacionesPendientes": pendientes,
        "poliza": poliza,
        "siniestroEnCurso": siniestro,
        "hipotecario": {"estado": "disponible"},
    }


class PerfilEntrada(BaseModel):
    nombre: str
    apellidos: str


def _perfil_salida(usuario: dict) -> dict:
    return {
        "usuarioId": str(usuario["usuario_id"]),
        "correo": usuario["email"],
        "nombre": usuario.get("nombre") or "",
        "apellidos": usuario.get("apellidos") or "",
        "documento": usuario.get("numero_documento") or "",
    }


@router.get("/perfil")
async def leer_perfil(
    cliente_identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
) -> dict:
    return _perfil_salida(await cliente_identidad.obtener(str(contexto_canonico(usuario).usuario_id)))


@router.patch("/perfil")
async def guardar_perfil(
    body: PerfilEntrada,
    cliente_identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    usuario: Annotated[dict, Depends(require_roles("cliente"))],
) -> dict:
    actualizado = await cliente_identidad.actualizar_perfil(
        str(contexto_canonico(usuario).usuario_id), nombre=body.nombre, apellidos=body.apellidos
    )
    return _perfil_salida(actualizado)
