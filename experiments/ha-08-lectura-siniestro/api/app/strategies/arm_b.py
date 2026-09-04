import orjson
from ..db import pool

SQL = "SELECT payload FROM siniestros_r.siniestro_estado WHERE siniestro_id = $1"

async def get_estado(siniestro_id: int) -> dict | None:
    async with pool.acquire() as conn:
        raw = await conn.fetchval(SQL, siniestro_id)
    return orjson.loads(raw) if raw else None
