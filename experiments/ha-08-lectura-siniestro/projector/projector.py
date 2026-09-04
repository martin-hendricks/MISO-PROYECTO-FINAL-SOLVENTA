import asyncio, os, orjson
import asyncpg
from aiokafka import AIOKafkaConsumer
from redis.asyncio import Redis
from prometheus_client import Histogram, Counter, start_http_server

LAG = Histogram(
    "ha08_projection_lag_seconds",
    "Lag entre ocurrencia del evento y proyección",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
)
PROJECTED = Counter("ha08_events_projected_total", "Eventos proyectados")
SKIPPED = Counter("ha08_events_skipped_total", "Eventos descartados por versión")

UPSERT = """
INSERT INTO siniestros_r.siniestro_estado
       (siniestro_id, cliente_id, version, ocurrido_en, proyectado_en, payload)
VALUES ($1, $2, $3, $4, now(), $5)
ON CONFLICT (siniestro_id) DO UPDATE
SET cliente_id    = EXCLUDED.cliente_id,
    version       = EXCLUDED.version,
    ocurrido_en   = EXCLUDED.ocurrido_en,
    proyectado_en = now(),
    payload       = EXCLUDED.payload
WHERE siniestros_r.siniestro_estado.version < EXCLUDED.version
RETURNING siniestro_id
"""

def _lag_seconds(ocurrido_en_iso: str) -> float:
    from datetime import datetime, timezone
    ocurrido_en = datetime.fromisoformat(ocurrido_en_iso.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - ocurrido_en).total_seconds()

async def main() -> None:
    start_http_server(8001)
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=2, max_size=5)
    redis = Redis.from_url(os.environ["REDIS_URL"])
    consumer = AIOKafkaConsumer(
        os.environ["TOPIC"],
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP"],
        group_id=os.environ["CONSUMER_GROUP"],
        enable_auto_commit=True,
        auto_offset_reset="latest",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            ev = orjson.loads(msg.value)
            async with pool.acquire() as conn:
                applied = await conn.fetchval(
                    UPSERT,
                    ev["siniestro_id"], ev["payload"]["cliente_id"],
                    ev["version"], ev["ocurrido_en"],
                    orjson.dumps(ev["payload"]).decode(),
                )
            if applied is None:
                SKIPPED.inc()
                continue
            # Invalidación proactiva: el caché no debe servir estado vencido
            await redis.delete(f"siniestro:estado:{ev['siniestro_id']}")
            PROJECTED.inc()
            LAG.observe(_lag_seconds(ev["ocurrido_en"]))
    finally:
        await consumer.stop()
        await pool.close()
        await redis.aclose()

if __name__ == "__main__":
    asyncio.run(main())
