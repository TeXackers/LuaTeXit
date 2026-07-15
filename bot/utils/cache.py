import time
from collections.abc import Awaitable, Callable
from functools import wraps

"""
Utilities for caching the results of slow and infrequently-changing async calls.
"""


def async_ttl_cache[**P, T](
    days: float = 0,
    hours: float = 0,
    minutes: float = 0,
    seconds: float = 0,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Cache an async function's result, keyed by its arguments, for the given time-to-live."""
    ttl: float = days * 86400 + hours * 3600 + minutes * 60 + seconds

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        cache: dict[tuple, tuple[float, T]] = {}

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            key = (args, tuple(sorted(kwargs.items())))
            now: float = time.monotonic()

            cached = cache.get(key)
            if cached is not None and now - cached[0] < ttl:
                return cached[1]

            result = await func(*args, **kwargs)
            cache[key] = (now, result)
            return result

        return wrapper

    return decorator
