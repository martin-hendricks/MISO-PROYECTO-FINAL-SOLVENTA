from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..clients.base import RechazoDelNucleo, RecursoNoEncontrado, ServicioNoDisponible
from ..clients.ms_cotizacion import ClienteMsCotizacion
from ..clients.ms_pagos import ClienteMsPagos
from ..clients.ms_perfilamiento import ClienteMsPerfilamiento
from ..clients.ms_polizas import ClienteMsPolizas
from ..clients.ms_suscripcion import ClienteMsSuscripcion
from ..dependencies import (
    obtener_cliente_cotizacion,
    obtener_cliente_pagos,
    obtener_cliente_perfilamiento,
    obtener_cliente_polizas,
    obtener_cliente_suscripcion,
    require_roles,
)
from .cliente import (
    FIRMA_NO_EXITOSA,
    RAMO_A_PRODUCTO,
    RAMO_VIDA_CREDITICIA,
    SIN_CONSENTIMIENTO,
    ContextoUsuario,
    Credito,
    _catalogo_salida,
    _cotizacion_salida,
    _idempotency_key,
    _producto_de,
    _uuid_desde,
    ofertar_vida_crediticia,
)

router = APIRouter(
    prefix="/asesor",
    tags=["asesor"],
    dependencies=[Depends(require_roles("asesor"))],
)


def _cliente(
    cliente_id: str,
    nombre: str,
    documento: str,
    canal: str,
    estado: str,
    consentimiento: str,
) -> dict:
    return {
        "clienteId": cliente_id,
        "nombre": nombre,
        "documento": documento,
        "correo": f"{nombre.split()[0].lower()}@correo.com",
        "habeasData": consentimiento != "revocado",
        "estado": estado,
        "canal": canal,
        "consentimiento": consentimiento,
    }


CLIENTES = [
    _cliente("CLI-18", "Andrés Gómez", "1020334556", "web", "activo", "habeas_data"),
    _cliente("CLI-19", "Laura Peña", "52448901", "android", "activo", "habeas_data"),
    _cliente("CLI-20", "Ricardo Salas", "80112334", "web", "activo", "hipotecario_pendiente"),
    _cliente("CLI-21", "Marcela Ruiz", "41778220", "android", "activo", "habeas_data"),
    _cliente("CLI-22", "Julián Torres", "79330114", "web", "inactivo", "revocado"),
]


class VentaAsistida(BaseModel):
    clienteId: str = Field(min_length=1)
    ramo: str
    datosRiesgo: dict


class OfertaHipotecariaAsistida(BaseModel):
    clienteId: str = Field(min_length=1)
    credito: Credito
    consentimientoPerfil: bool


class ClienteNuevo(BaseModel):
    nombre: str
    documento: str
    correo: str
    habeasData: bool
    estado: str = "activo"


class Desactivar(BaseModel):
    clienteId: str
    estado: str


def _asesor_id(sesion: dict) -> UUID:
    """HU-163: id estable del asesor de la sesión (uuid5 del `sub`, mismo
    estilo que ContextoUsuario). Nunca se toma del body: así un asesor solo
    puede crear y listar cotizaciones a su propio nombre."""
    return _uuid_desde("asesor", sesion["sub"])


@router.post("/cotizaciones")
async def venta(
    body: VentaAsistida,
    sesion: Annotated[dict, Depends(require_roles("asesor"))],
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
) -> dict:
    """Cotización asistida: el asesor cotiza en nombre del cliente que
    atiende. Reusa ms-cotizacion igual que el canal cliente (routers/
    cliente.py), derivando el contexto a partir de body.clienteId (no del
    correo del asesor que está en la sesión) -- la cotización queda asociada
    de forma estable al cliente atendido, no a quien la generó. No hay
    ms-identidad real que resuelva clienteId a una identidad verificada;
    ContextoUsuario deriva UUIDs deterministas a partir del string tal cual
    llega (mismo patrón ya documentado en cliente.py)."""
    contexto = ContextoUsuario(body.clienteId)
    producto = _producto_de(body.ramo)

    datos = await cliente_cotizacion.cotizar(
        idempotency_key=_idempotency_key(),
        usuario_id=contexto.usuario_id,
        socio_id=contexto.socio_id,
        consentimiento_id=contexto.consentimiento_id,
        producto=producto,
        canal="asesor",
        datos_riesgo=body.datosRiesgo,
        asesor_id=_asesor_id(sesion),
        cliente_ref=body.clienteId,
    )
    return _cotizacion_salida(datos, body.ramo)


@router.post("/oferta-hipotecaria")
async def oferta_hipotecaria(
    body: OfertaHipotecariaAsistida,
    sesion: Annotated[dict, Depends(require_roles("asesor"))],
    cliente_perfilamiento: Annotated[ClienteMsPerfilamiento, Depends(obtener_cliente_perfilamiento)],
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
) -> dict:
    """Oferta de vida hipotecario en el portal asesor (HU-58): la misma
    orquestación y el mismo shape que ve el cliente (HU-105), pero a nombre
    del cliente atendido, igual que venta(). `consentimientoPerfil` lo
    declara el cliente en la venta asistida; sin él no se perfila. La
    cotización queda con el asesor, así sigue a emisión por HU-163."""
    if not body.consentimientoPerfil:
        return {"ramo": RAMO_VIDA_CREDITICIA, "estado": SIN_CONSENTIMIENTO}

    return await ofertar_vida_crediticia(
        ContextoUsuario(body.clienteId),
        body.credito,
        "asesor",
        cliente_perfilamiento,
        cliente_cotizacion,
        asesor_id=_asesor_id(sesion),
        cliente_ref=body.clienteId,
    )


POLIZAS_NO_DISPONIBLE = "polizas_no_disponible"

_PRODUCTO_A_RAMO = {producto: ramo for ramo, producto in RAMO_A_PRODUCTO.items()}


def _pendiente_salida(item: dict) -> dict:
    return {
        "cotizacionId": item["cotizacion_id"],
        "ofertaId": item["oferta_id"],
        "ramo": _PRODUCTO_A_RAMO.get(item["producto"], item["producto"]),
        "estado": item["estado"],
        "prima": item["prima"],
        "moneda": item["moneda"],
        "creadaEn": item["creada_en"],
        "venceEn": item["vence_en"],
        "vencida": item["vencida"],
        "clienteRef": item.get("cliente_ref"),
    }


@router.get("/cotizaciones")
async def pendientes(
    sesion: Annotated[dict, Depends(require_roles("asesor"))],
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
    incluirVencidas: bool = False,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamano: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """Cotizaciones pendientes de emisión del asesor de la sesión (HU-163).

    ms-cotizacion ya filtra por asesor, estado y vencimiento. Una `aceptada`
    puede tener la póliza emitida (ms-cotizacion no lo sabe), así que se
    cruza con ms-polizas en una sola llamada. Si ms-polizas falla no se
    puede saber cuáles siguen pendientes: se descartan todas las aceptadas
    y se avisa, en vez de ofrecer continuar una emisión ya hecha.
    """
    listado = await cliente_cotizacion.listar_por_asesor(
        _asesor_id(sesion), incluirVencidas, pagina, tamano
    )
    items = listado["items"]
    avisos: list[str] = []

    aceptadas = [UUID(i["oferta_id"]) for i in items if i["estado"] == "aceptada"]
    if aceptadas:
        try:
            emitidas = await cliente_polizas.ofertas_con_poliza(aceptadas)
            items = [i for i in items if i["estado"] != "aceptada" or i["oferta_id"] not in emitidas]
        except (ServicioNoDisponible, RechazoDelNucleo, RecursoNoEncontrado):
            items = [i for i in items if i["estado"] != "aceptada"]
            avisos.append(POLIZAS_NO_DISPONIBLE)

    return {
        "items": [_pendiente_salida(i) for i in items],
        "pagina": listado["pagina"],
        "tamano": listado["tamano"],
        "hayMas": listado["hay_mas"],
        "avisos": avisos,
    }


@router.get("/catalogo/{ramo}")
async def catalogo(
    ramo: str,
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
) -> dict:
    """SOLV-245: mismo catálogo que GET /cliente/catalogo/{ramo}, expuesto
    también para el asesor (ver routers/cliente.py:catalogo)."""
    producto = await cliente_cotizacion.obtener_producto(_producto_de(ramo))
    return _catalogo_salida(producto, ramo)


class ConsultarEmision(BaseModel):
    cotizacionId: str = Field(min_length=1)
    clienteId: str | None = None


# ms-suscripcion decide con una regla de datos, sin intervención humana (HU-13).
DECIDIDO_POR = "Motor automático"

# ms-polizas emite toda póliza con un año de vigencia (_un_anio_despues).
VIGENCIA_POLIZA_MESES = 12


def _pasos(aceptada: bool) -> list[dict]:
    """Stepper del web: COTIZAR y OFERTA ya ocurrieron; EMISION queda como
    paso actual si la suscripción aceptó, o en error si rechazó."""
    return [
        {"paso": "COTIZAR", "estado": "COMPLETADO"},
        {"paso": "OFERTA", "estado": "COMPLETADO"},
        {"paso": "EMISION", "estado": "ACTUAL" if aceptada else "ERROR"},
        {"paso": "POLIZA", "estado": "PENDIENTE"},
    ]


def _cliente_salida(cliente_id: str | None) -> dict:
    """Datos del cliente atendido. Sin ms-identidad se resuelve contra la
    cartera de ejemplo; si no está, el id hace de nombre para no dejar vacío
    el encabezado de la pantalla."""
    cliente_id = cliente_id or ""
    conocido = next((c for c in CLIENTES if c["clienteId"] == cliente_id), None)
    return {"clienteId": cliente_id, "nombre": conocido["nombre"] if conocido else cliente_id}


def _decision_salida(suscripcion: dict) -> dict:
    """Traduce SuscripcionSalida de ms-suscripcion al shape de "decision"
    de la propuesta de análisis del equipo de frontend (HU-149).

    "regla" es la copia de la regla que ms-suscripcion guardó al decidir;
    una decisión anterior a esa columna la trae vacía y queda None en vez de
    inventada. "decididoPor" es el motor automático, porque la decisión
    es una evaluación contra una regla de datos sin un humano que decida.
    "detalle" reusa el mismo texto que "motivo" porque ms-suscripcion no
    distingue las dos cosas.
    """
    return {
        "resultado": suscripcion["decision"],
        "regla": suscripcion.get("regla") or None,
        "detalle": suscripcion["motivo"],
        "decididoPor": DECIDIDO_POR,
        "decididoEn": suscripcion["evaluada_en"],
    }


def _oferta_resumen(cotizacion: dict) -> dict:
    """Traduce CotizacionSalida al shape de "oferta" de la propuesta.

    "vigenciaMeses" es la vigencia de la póliza que emitirá ms-polizas, no
    vence_en de ms-cotizacion (la expiración de la oferta).
    """
    return {
        "moneda": cotizacion["moneda"],
        "primaTotal": cotizacion["prima"],
        "primaNeta": cotizacion["prima_neta"],
        "expedicion": cotizacion["gastos_expedicion"],
        "vigenciaMeses": VIGENCIA_POLIZA_MESES,
    }


async def _nombre_producto(cliente_cotizacion: ClienteMsCotizacion, producto: str) -> str:
    """Nombre comercial del producto según el catálogo; si el catálogo no lo
    tiene, se muestra el código tal como lo guarda ms-cotizacion."""
    try:
        return (await cliente_cotizacion.obtener_producto(producto))["nombre"]
    except RecursoNoEncontrado:
        return producto


@router.post("/emisiones")
async def consultar_emision(
    body: ConsultarEmision,
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    cliente_suscripcion: Annotated[ClienteMsSuscripcion, Depends(obtener_cliente_suscripcion)],
) -> dict:
    """Consulta la decisión de suscripción SIN emitir (HU-149, SOLV-112).

    A diferencia de POST /cliente/polizas (que acepta la oferta en
    ms-cotizacion -- eso cambia el estado de la solicitud a "aceptada"),
    aquí se evalúa la suscripción directo contra ms-suscripcion. Es
    idempotente por solicitud_id: reintentar esta consulta nunca duplica
    ni cambia nada, siempre devuelve la misma decisión ya persistida la
    primera vez que se evaluó para esa cotización.

    TODO: "score" es el mismo stub fijo que usa cliente.py -- no hay
    ms-perfilamiento conectado a este flujo para calcular un score real.
    TODO: no hay sesión de cliente real para resolver "cliente" (nombre,
    documento, etc. de la propuesta) -- requiere ms-identidad.
    """
    cotizacion = await cliente_cotizacion.reconsultar(body.cotizacionId)

    score_stub = Decimal("0.5000")
    perfil_id = ContextoUsuario(body.cotizacionId).perfil_id
    suscripcion = await cliente_suscripcion.evaluar(
        solicitud_id=UUID(body.cotizacionId),
        perfil_id=perfil_id,
        score=score_stub,
    )

    decision = _decision_salida(suscripcion)
    return {
        "solicitudId": body.cotizacionId,
        "cliente": _cliente_salida(body.clienteId),
        "producto": await _nombre_producto(cliente_cotizacion, cotizacion["producto"]),
        "referencia": body.cotizacionId,
        "pasos": _pasos(decision["resultado"] == "ACEPTADA"),
        "decision": decision,
        "oferta": _oferta_resumen(cotizacion),
    }


@router.post("/emisiones/{solicitud_id}/poliza")
async def firmar_y_emitir(
    solicitud_id: str,
    cliente_cotizacion: Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)],
    cliente_pagos: Annotated[ClienteMsPagos, Depends(obtener_cliente_pagos)],
    cliente_polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
) -> dict:
    """Firma y emite una solicitud ya evaluada por POST /asesor/emisiones
    (HU-149, HU-17 stub de firma electrónica).

    Mismo flujo que POST /cliente/polizas (ver cliente.emitir): acepta la
    oferta en ms-cotizacion (idempotente -- si ya se evaluó en
    consultar_emision, reutiliza esa misma decisión en vez de recalcularla,
    porque ms-suscripcion.evaluar es idempotente por solicitud_id), cobra la
    prima y emite la póliza. Un rechazo de suscripción responde 200 con
    {resultado: RECHAZADA, motivo} igual que en el canal cliente -- no es
    una falla técnica.

    ms-polizas firma (stub de HU-17) dentro de la emisión. Una firma no
    exitosa también responde 200 con {resultado: RECHAZADA, motivo, pasos} y
    el paso Emisión en ERROR; si la firma es exitosa, su fecha y hash salen
    de la constancia persistida, no de la póliza.
    """
    score_stub = Decimal("0.5000")
    perfil_id = ContextoUsuario(solicitud_id).perfil_id

    aceptacion = await cliente_cotizacion.aceptar_oferta(
        cotizacion_id=solicitud_id,
        idempotency_key=_idempotency_key(),
        perfil_id=perfil_id,
        score=score_stub,
    )

    if aceptacion["decision"].upper() != "ACEPTADA":
        return {"resultado": "RECHAZADA", "motivo": aceptacion["motivo"]}

    oferta_id = UUID(aceptacion["oferta_id"])
    solicitud_uuid = UUID(aceptacion["cotizacion_id"])
    contexto = ContextoUsuario(solicitud_id)

    # TODO: `token_medio_pago` es un placeholder -- mismo faltante que en
    # cliente.emitir() (sin pasarela real integrada todavía).
    pago = await cliente_pagos.cobrar_prima(
        solicitud_id=solicitud_uuid,
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
            solicitud_id=solicitud_uuid,
            oferta_id=oferta_id,
            usuario_id=contexto.usuario_id,
            token_pago_confirmado=UUID(str(pago["id"])),
            coberturas=cobertura_minima,
        )
    except RechazoDelNucleo as rechazo:
        if rechazo.codigo != FIRMA_NO_EXITOSA:
            raise
        return {
            "resultado": "RECHAZADA",
            "motivo": rechazo.mensaje,
            "pasos": [
                {"paso": "COTIZAR", "estado": "COMPLETADO"},
                {"paso": "OFERTA", "estado": "COMPLETADO"},
                {"paso": "EMISION", "estado": "ERROR"},
                {"paso": "POLIZA", "estado": "PENDIENTE"},
            ],
        }

    constancia = await cliente_polizas.consultar_firma(oferta_id)
    cotizacion = await cliente_cotizacion.reconsultar(solicitud_id)
    ramo = cotizacion.get("producto", "")

    inicio = poliza.get("inicio_vigencia", "")
    return {
        "resultado": "EMITIDA",
        "pasos": [
            {"paso": "COTIZAR", "estado": "COMPLETADO"},
            {"paso": "OFERTA", "estado": "COMPLETADO"},
            {"paso": "EMISION", "estado": "COMPLETADO"},
            {"paso": "POLIZA", "estado": "COMPLETADO"},
        ],
        "firma": {"firmadaEn": constancia["firmada_en"], "hash": constancia.get("firma_hash") or ""},
        "poliza": {
            "numero": poliza["numero"],
            "ramo": ramo,
            "estado": poliza["estado"],
            "venceEn": poliza.get("fin_vigencia", ""),
            "expedidaEn": inicio,
            "inicioVigencia": inicio,
            "finVigencia": poliza.get("fin_vigencia", ""),
        },
    }


# TODO: no hay microservicio que agregue KPIs/cartera de un asesor -- requiere
# un endpoint de reporting en el núcleo que no existe todavía.
@router.get("/cartera")
def cartera() -> dict:
    return {
        "kpis": {"cotizaciones": 12, "polizas": 40},
        "cola": [
            {
                "id": "COT-1042",
                "tipo": "cotizacion",
                "ramo": "Protección de dispositivo",
                "estado": "en_revision",
            },
            {
                "id": "POL-88219-CO",
                "tipo": "poliza",
                "ramo": "Protección de dispositivo",
                "estado": "vigente",
            },
        ],
    }


# TODO: el CRM de clientes depende de ms-identidad (no existe código, solo
# README en cualquier rama) -- no hay microservicio real al que integrar.
@router.get("/clientes")
def listar() -> dict:
    return {"clientes": [dict(cliente) for cliente in CLIENTES]}


# TODO: mismo faltante que listar() -- alta de clientes depende de ms-identidad.
@router.post("/clientes")
def crear(body: ClienteNuevo) -> dict:
    created = body.model_dump()
    created["clienteId"] = "CLI-23"
    return created


# TODO: mismo faltante que listar() -- cambio de estado depende de ms-identidad.
@router.post("/clientes/estado")
def desactivar(body: Desactivar) -> dict:
    return {"clienteId": body.clienteId, "estado": "inactivo"}
