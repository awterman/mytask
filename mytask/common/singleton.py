import asyncio
import threading
from functools import wraps
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


def singleton(func: Callable[[], T]) -> Callable[[], T]:
    """Decorator that ensures only one instance of the decorated function's return value exists."""
    lock = threading.Lock()
    instance: T | None = None

    @wraps(func)
    def wrapper() -> T:
        nonlocal instance
        if instance is None:
            with lock:
                if instance is None:
                    instance = func()
        return instance

    return wrapper


def async_singleton(func: Callable[[], Awaitable[T]]) -> Callable[[], Awaitable[T]]:
    """Decorator that ensures only one instance of the decorated async function's return value exists."""
    lock = asyncio.Lock()
    instance: T | None = None

    @wraps(func)
    async def wrapper() -> T:
        nonlocal instance
        if instance is None:
            async with lock:
                if instance is None:
                    instance = await func()
        return instance

    return wrapper
