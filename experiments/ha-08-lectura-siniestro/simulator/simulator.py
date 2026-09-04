import asyncio, os, random, uuid
from datetime import datetime, timezone

import asyncpg
import orjson
from aiokafka import AIOKafkaProducer

EVENTS_PER_SECOND = float(os.environ.get("EVENTS_PER_SECOND", "5"))
HOT_SET_SIZE = int(os.environ.get("HOT_SET_SIZE", "10000"))

ESTADOS = ["RECIBIDO", "EN_VALIDACION", "EN_PERITAJE", "EN_LIQUIDACION", "APROBADO", "RECHAZADO"]

FETCH_SNAPSHOT_SQL = """
SELECT
    s.numero, s.cliente_id, s.causa,
    s.monto_estimado, s.monto_aprobado,
    s.fecha_ocurrencia, s.fecha_aviso,
    jsonb_build_object(
        'numero', p.numero,
        'producto', p.producto,
        'suma_asegurada', p.suma_asegurada
    ) AS poliza,
    COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
            'tipo', h.tipo, 'descripcion', h.descripcion,
            'actor', h.actor, 'ocurrido_en', h.ocurrido_en
        ) ORDER BY h.ocurrido_en)
        FROM siniestros_w.hito h WHERE h.siniestro_id = s.id
    ), '[]'::jsonb) AS hitos,
    COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
            'tipo', d.tipo, 'estado', d.estado, 'cargado_en', d.cargado_en
        ) ORDER BY d.cargado_en)
        FROM siniestros_w.documento d WHERE d.siniestro_id = s.id
    ), '[]'::jsonb) AS documentos,
    (
        SELECT jsonb_build_object(
            'perito', pe.perito, 'estado', pe.estado,
            'resultado', pe.resultado, 'agendado_para', pe.agendado_para
        )
        FROM siniestros_w.peritaje pe
        WHERE pe.siniestro_id = s.id
        ORDER BY pe.id DESC LIMIT 1
    ) AS peritaje
FROM siniestros_w.siniestro s
JOIN siniestros_w.poliza p ON p.id = s.poliza_id
WHERE s.id = $1
"""

UPDATE_SQL = """
UPDATE siniestros_w.siniestro
SET estado = $2, actualizado_en = now(), version = version + 1
WHERE id = $1
RETURNING version, actualizado_en
"""

INSERT_HITO_SQL = """
INSERT INTO siniestros_w.hito (siniestro_id, tipo, descripcion, actor, ocurrido_en)
VALUES ($1, 'CAMBIO_ESTADO', $2, 'SISTEMA', now())
"""


async def emitir_evento(pool: asyncpg.Pool, producer: AIOKafkaProducer, siniestro_id: int) -> None:
    nuevo_estado = random.choice(ESTADOS)

    async with pool.acquire() as conn:
        async with conn.transaction():
            # 2. UPDATE del estado del siniestro
            row = await conn.fetchrow(UPDATE_SQL, siniestro_id, nuevo_estado)
            if row is None:
                return
            # 3. INSERT de hito
            await conn.execute(
                INSERT_HITO_SQL, siniestro_id, f"Estado cambiado a {nuevo_estado}"
            )
            # 4. construir el payload completo (mismo shape que arm_a)
            snapshot = await conn.fetchrow(FETCH_SNAPSHOT_SQL, siniestro_id)

    if snapshot is None:
        return

    data = dict(snapshot)
    for k in ("poliza", "hitos", "documentos", "peritaje"):
        if isinstance(data[k], str):
            data[k] = orjson.loads(data[k])
    data["estado"] = nuevo_estado

    ocurrido_en = row["actualizado_en"].astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "SiniestroEstadoCambiado",
        "siniestro_id": siniestro_id,
        "version": row["version"],
        "ocurrido_en": ocurrido_en,
        "payload": {
            "numero": data["numero"],
            "cliente_id": data["cliente_id"],
            "estado": nuevo_estado,
            "causa": data["causa"],
            "monto_estimado": float(data["monto_estimado"]) if data["monto_estimado"] is not None else None,
            "monto_aprobado": float(data["monto_aprobado"]) if data["monto_aprobado"] is not None else None,
            "fecha_ocurrencia": data["fecha_ocurrencia"].isoformat(),
            "fecha_aviso": data["fecha_aviso"].isoformat(),
            "poliza": data["poliza"],
            "hitos": data["hitos"],
            "documentos": data["documentos"],
            "peritaje": data["peritaje"],
        },
    }

    # 5. publicar en Redpanda con key=str(siniestro_id) y ocurrido_en=now()
    await producer.send_and_wait(
        os.environ["TOPIC"],
        key=str(siniestro_id).encode(),
        value=orjson.dumps(event),
    )


async def main() -> None:
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=2, max_size=5)
    producer = AIOKafkaProducer(bootstrap_servers=os.environ["KAFKA_BOOTSTRAP"])
    await producer.start()

    interval = 1.0 / EVENTS_PER_SECOND
    try:
        while True:
            # 1. elegir un siniestro del hot set (los que un cliente consultaría)
            siniestro_id = random.randint(1, HOT_SET_SIZE)
            await emitir_evento(pool, producer, siniestro_id)
            await asyncio.sleep(interval)
    finally:
        await producer.stop()
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
