from redis.asyncio import Redis

from mytask.common.redis_cache import RedisCache
from mytask.common.settings import get_settings
from mytask.common.singleton import singleton


@singleton
def get_redis_cache() -> RedisCache:
    settings = get_settings()

    redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
    )
    return RedisCache(redis)
