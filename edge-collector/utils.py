import time
from typing import Any, Callable


def log(msg: str) -> None:
    print(msg, flush=True)


def retry(n: int, delay: float, func: Callable, *args, **kwargs) -> Any:
    for attempt in range(1, n + 1):
        try:
            return func(*args, **kwargs)
        except Exception:
            if attempt < n:
                time.sleep(delay)
            else:
                raise
