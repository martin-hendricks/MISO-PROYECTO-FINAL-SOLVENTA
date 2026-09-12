import asyncpg
from .config import settings

pool: asyncpg.Pool | None = None

async def init_pool() -> None:
    global pool
    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        max_inactive_connection_lifetime=0,
        command_timeout=5,
    )

async def close_pool() -> None:
    if pool:
        await pool.close()
