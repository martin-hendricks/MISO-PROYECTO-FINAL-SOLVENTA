import asyncpg
from .config import settings

pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global pool
    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,
        max_size=5,
        command_timeout=5,
    )


async def close_pool() -> None:
    if pool:
        await pool.close()
