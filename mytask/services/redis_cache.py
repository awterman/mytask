from functools import lru_cache

from aiocache import RedisCache

from mytask.common.settings import get_settings


@lru_cache(maxsize=1)
def get_redis_cache() -> RedisCache:
    settings = get_settings()
    return RedisCache(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password)
