from functools import lru_cache

from aiocache import RedisCache

from mytask.common.settings import get_settings


def get_redis_cache() -> RedisCache:
    settings = get_settings()
    return RedisCache(endpoint=settings.redis_host, port=settings.redis_port, password=settings.redis_password)