import asyncio
import json
from collections import namedtuple
from decimal import Decimal

import pytest

from app.config import Settings
from app.domain.modelos import EstadoSiniestro
from app.infrastructure.consumidor_telemetria import (
    ConsumidorTelemetria,
    MensajeDescartable,
    opciones_conexion,
    procesar_mensaje,
)

Mensaje = namedtuple("Mensaje", "value offset partition")
PARTICION = "TopicoTelemetria-0"


def mensaje(evento_id="vuelos:R-1", valor="190", monto="180000.00", version=1, **cobertura) -> bytes:
    return json.dumps(
        {
            "version": version,
            "evento_id": evento_id,
            "proveedor": "vuelos",
            "tipo": "retraso_vuelo",
            "valor": valor,
            "ocurrido_en": "2026-11-20T14:00:00+00:00",
            "recibido_en": "2026-11-20T14:00:01+00:00",
            "ramo": "clima-vuelos",
            "descripcion": "Retraso del vuelo AV234",
            "cobertura": {"umbral": "120", "monto": monto, "vigente": True, "poliza_numero": "POL-77310", **cobertura},
        }
    ).encode()


class AdaptadorQueCuenta:
    def __init__(self, fallos=0):
        self.llamadas = []
        self._fallos = fallos

    async def desembolsar(self, evento_id, monto):
        self.llamadas.append(evento_id)
        if self._fallos:
            self._fallos -= 1
            raise ConnectionError("pasarela caída")


def _siniestro(almacen, evento_id):
    return next(s for s in almacen.siniestros.values() if s.evento_id == evento_id)


# --- procesar_mensaje: contrato y clasificación de errores ---------------------------


async def test_mensaje_valido_evalua_y_paga_con_origen_topico(uow, almacen):
    adaptador = AdaptadorQueCuenta()

    resultado = await procesar_mensaje(uow, adaptador, mensaje())

    assert resultado.procesado is True
    assert resultado.siniestro.estado is EstadoSiniestro.PAGADO
    assert resultado.pago.monto == Decimal("180000.00")
    siniestro = _siniestro(almacen, "vuelos:R-1")
    assert siniestro.historial[0].origen == "topico-telemetria"
    assert siniestro.poliza.numero == "POL-77310"
    assert siniestro.poliza.ramo == "clima-vuelos"
    assert adaptador.llamadas == ["vuelos:R-1"]


async def test_reentrega_del_mismo_mensaje_no_paga_dos_veces(uow, almacen):
    adaptador = AdaptadorQueCuenta()

    await procesar_mensaje(uow, adaptador, mensaje())
    segundo = await procesar_mensaje(uow, adaptador, mensaje())

    assert segundo.procesado is False
    assert adaptador.llamadas == ["vuelos:R-1"]
    assert len(almacen.pagos) == 1


async def test_umbral_no_alcanzado_queda_decidido_sin_pago(uow):
    resultado = await procesar_mensaje(uow, AdaptadorQueCuenta(), mensaje(valor="30"))

    assert resultado.siniestro.estado is EstadoSiniestro.DECIDIDO
    assert resultado.pago is None


@pytest.mark.parametrize(
    "valor",
    [b"no-es-json", b'{"version": 1}', mensaje(version=2), mensaje(evento_id="")],
    ids=["json-corrupto", "campos-faltantes", "version-desconocida", "sin-id"],
)
async def test_mensajes_inservibles_son_descartables(uow, almacen, valor):
    with pytest.raises(MensajeDescartable):
        await procesar_mensaje(uow, AdaptadorQueCuenta(), valor)
    assert almacen.siniestros == {}


async def test_regla_de_negocio_violada_es_descartable_y_no_deja_nada(uow, almacen):
    with pytest.raises(MensajeDescartable):
        await procesar_mensaje(uow, AdaptadorQueCuenta(), mensaje(monto="0"))
    assert almacen.siniestros == {}
    assert almacen.eventos_parametricos == {}


# --- bucle: offset después de procesar, descarte y reintento -------------------------


class ConsumidorFalso:
    """Entrega un lote y luego se queda esperando, como un tópico sin mensajes nuevos."""

    def __init__(self, mensajes):
        self._lotes = [{PARTICION: mensajes}]
        self.commits = []
        self.vacio = asyncio.Event()

    async def start(self):
        pass

    async def stop(self):
        pass

    async def getmany(self, timeout_ms, max_records):
        if self._lotes:
            return self._lotes.pop(0)
        self.vacio.set()
        await asyncio.sleep(3600)
        return {}

    async def commit(self, offsets):
        self.commits.append(offsets)


def _config() -> Settings:
    return Settings(
        _env_file=None,
        consumidor_backoff_inicial_segundos=0.01,
        consumidor_backoff_maximo_segundos=0.02,
    )


async def _consumir(uow, adaptador, mensajes):
    falso = ConsumidorFalso(mensajes)
    consumidor = ConsumidorTelemetria(_config(), uow, adaptador, consumer=falso)
    await consumidor.iniciar()
    await asyncio.wait_for(falso.vacio.wait(), timeout=5)
    await consumidor.detener()
    return falso


async def test_bucle_confirma_cada_offset_despues_de_procesar(uow, almacen):
    adaptador = AdaptadorQueCuenta()

    falso = await _consumir(
        uow, adaptador, [Mensaje(mensaje("vuelos:A"), 10, 0), Mensaje(mensaje("vuelos:B"), 11, 0)]
    )

    assert falso.commits == [{PARTICION: 11}, {PARTICION: 12}]
    assert adaptador.llamadas == ["vuelos:A", "vuelos:B"]


async def test_bucle_salta_un_mensaje_corrupto_sin_bloquear_la_particion(uow, almacen):
    adaptador = AdaptadorQueCuenta()

    falso = await _consumir(uow, adaptador, [Mensaje(b"basura", 5, 0), Mensaje(mensaje("vuelos:C"), 6, 0)])

    assert falso.commits == [{PARTICION: 6}, {PARTICION: 7}]
    assert adaptador.llamadas == ["vuelos:C"]


async def test_bucle_reintenta_una_falla_transitoria_sin_perder_el_evento(uow, almacen):
    adaptador = AdaptadorQueCuenta(fallos=2)  # la pasarela falla dos veces y luego responde

    falso = await _consumir(uow, adaptador, [Mensaje(mensaje("vuelos:D"), 0, 0)])

    assert falso.commits == [{PARTICION: 1}]  # un solo commit, después de lograrlo
    assert adaptador.llamadas == ["vuelos:D"] * 3
    assert _siniestro(almacen, "vuelos:D").estado is EstadoSiniestro.PAGADO
    assert len(almacen.pagos) == 1


class ConsumidorSinBroker(ConsumidorFalso):
    """El broker rechaza las dos primeras conexiones y luego responde."""

    def __init__(self, mensajes):
        super().__init__(mensajes)
        self.intentos = 0

    async def start(self):
        self.intentos += 1
        if self.intentos <= 2:
            raise ConnectionError("broker no disponible")


async def test_sin_broker_el_arranque_no_bloquea_y_reintenta_hasta_conectar(uow, almacen):
    adaptador = AdaptadorQueCuenta()
    falso = ConsumidorSinBroker([Mensaje(mensaje("vuelos:E"), 0, 0)])
    consumidor = ConsumidorTelemetria(_config(), uow, adaptador, consumer=falso)

    await asyncio.wait_for(consumidor.iniciar(), timeout=0.5)  # retorna de inmediato
    await asyncio.wait_for(falso.vacio.wait(), timeout=5)
    await consumidor.detener()

    assert falso.intentos == 3
    assert falso.commits == [{PARTICION: 1}]
    assert adaptador.llamadas == ["vuelos:E"]


def test_plaintext_para_local_e_iam_para_msk():
    assert opciones_conexion(Settings(_env_file=None, msk_auth_mechanism="PLAINTEXT")) == {
        "security_protocol": "PLAINTEXT"
    }
    assert opciones_conexion(Settings(_env_file=None))["sasl_mechanism"] == "OAUTHBEARER"
