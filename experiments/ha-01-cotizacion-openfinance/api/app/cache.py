from redis.asyncio import Redis
from .config import settings

redis_client: Redis | None = None


async def init_cache() -> None:
    global redis_client
    redis_client = Redis.from_url(settings.redis_url)


async def close_cache() -> None:
    if redis_client:
        await redis_client.aclose()
