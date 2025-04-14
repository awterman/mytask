import asyncio
import inspect
import json
from functools import wraps
from typing import (Any, Callable, Dict, List, Optional, TypeVar, cast,
                    get_args, get_origin)
from uuid import uuid4

from aioredis import Redis
from pydantic import BaseModel

RT = TypeVar("RT")


class RedisCache:
    def __init__(self, redis: Redis, default_ttl: int = 60*2):
        self.redis = redis
        self.default_ttl = default_ttl

    async def get(self, key: str, result_type: type[RT]) -> Optional[RT]:
        data = await self.redis.get(key)
        if data is None:
            return None

        parsed_data = json.loads(data)
        return self._parse_with_type(parsed_data, result_type)

    def _parse_with_type(self, data: Any, type_hint: Any) -> Any:
        # Handle single Pydantic model
        if inspect.isclass(type_hint) and issubclass(type_hint, BaseModel):
            return type_hint.model_validate(data)
        
        # Handle container types (list, dict)
        origin = get_origin(type_hint)
        if origin is not None:
            args = get_args(type_hint)
            
            # Handle lists 
            if origin is list or origin is List:
                item_type = args[0]
                return [self._parse_with_type(item, item_type) for item in data]
            
            # Handle dictionaries
            elif origin is dict or origin is Dict:
                key_type, value_type = args
                return {k: self._parse_with_type(v, value_type) for k, v in data.items()}
        
        # Default case for primitive types
        return data

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        if isinstance(value, BaseModel):
            data = value.model_dump_json()
        elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
            data = json.dumps([item.model_dump() for item in value])
        elif isinstance(value, dict) and value and isinstance(next(iter(value.values())), BaseModel):
            data = json.dumps({k: v.model_dump() for k, v in value.items()})
        else:
            data = json.dumps(value)

        await self.redis.set(key, data, ex=ttl or self.default_ttl)


def redis_cache(
    redis_cache: RedisCache,
    prefix: str = "cache",
    ttl: Optional[int] = None,
    key_builder: Optional[Callable[..., str]] = None,
):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return_type = inspect.signature(func).return_annotation

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = _build_cache_key(
                prefix=prefix,
                func=func,
                args=args,
                kwargs=kwargs,
                key_builder=key_builder,
            )

            cached = await redis_cache.get(cache_key, return_type)
            if cached is not None:
                return cached

            result = await func(*args, **kwargs)

            await redis_cache.set(
                key=cache_key,
                value=result,
                ttl=ttl,
            )

            return result

        return wrapper

    return decorator


def _build_cache_key(
    prefix: str,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    key_builder: Optional[Callable[..., str]] = None,
) -> str:
    if key_builder:
        return key_builder(*args, **kwargs)

    arg_str = ":".join(str(arg) for arg in args)
    kwarg_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return f"{prefix}:{func.__module__}:{func.__name__}:{arg_str}:{kwarg_str}"