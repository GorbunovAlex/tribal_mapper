import threading
import time


class RateLimiter:
    """Thread-safe token-bucket rate limiter.

    Ensures no more than *rpm* requests are made per 60-second window by
    spacing calls evenly.  Each call to :meth:`acquire` blocks the calling
    thread until a slot is available.
    """

    def __init__(self, rpm: int) -> None:
        if rpm <= 0:
            msg = "rpm must be a positive integer"
            raise ValueError(msg)
        self._interval = 60.0 / rpm
        self._lock = threading.Lock()
        self._last: float = 0.0

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = self._last + self._interval - now
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
