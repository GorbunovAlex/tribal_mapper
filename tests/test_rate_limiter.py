import threading
import time

from infrastructure.ai.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_first_acquire_is_instant(self):
        limiter = RateLimiter(rpm=60)  # 1 req/sec
        start = time.monotonic()
        limiter.acquire()
        assert time.monotonic() - start < 0.1

    def test_second_acquire_waits(self):
        limiter = RateLimiter(rpm=60)  # 1 req/sec → 1s interval
        limiter.acquire()
        start = time.monotonic()
        limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.9

    def test_high_rpm_allows_fast_calls(self):
        limiter = RateLimiter(rpm=6000)  # 0.01s interval
        start = time.monotonic()
        for _ in range(5):
            limiter.acquire()
        assert time.monotonic() - start < 0.5

    def test_thread_safety(self):
        limiter = RateLimiter(rpm=600)  # 0.1s interval
        timestamps: list[float] = []
        lock = threading.Lock()

        def worker():
            limiter.acquire()
            with lock:
                timestamps.append(time.monotonic())

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        timestamps.sort()
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i - 1]
            assert gap >= 0.08  # allow small timing margin

    def test_invalid_rpm_raises(self):
        import pytest

        with pytest.raises(ValueError, match="positive"):
            RateLimiter(rpm=0)
        with pytest.raises(ValueError, match="positive"):
            RateLimiter(rpm=-5)
