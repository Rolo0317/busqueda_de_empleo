import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 5
    base_delay_s: float = 0.5
    max_delay_s: float = 15.0
    jitter_ratio: float = 0.2


def _should_retry(exc: Exception) -> bool:
    msg = str(exc).lower()
    # Selenium / network / DB / bot-detection common cases
    return any(
        needle in msg
        for needle in (
            "timeout",
            "timed out",
            "timed_out",
            "429",
            "too many requests",
            "temporarily",
            "connection reset",
            "connection refused",
            "net::err",
            "stale element",
            "invalid session id",
            "session deleted",
            "ecannot",
            "captcha",
            "access denied",
            "rate limit",
            "proxy",
            "read timed out",
        )
    )


def retry(policy: RetryPolicy, *, retryable: Callable[[Exception], bool] = _should_retry) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            delay = policy.base_delay_s
            last_exc: Exception | None = None
            for attempt in range(1, policy.max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if attempt >= policy.max_attempts or not retryable(exc):
                        raise
                    jitter = delay * policy.jitter_ratio * random.random()
                    time.sleep(delay + jitter)
                    delay = min(policy.max_delay_s, delay * 2)
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator

