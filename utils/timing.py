"""Execution-time measurement helper used by every graph node."""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def timed() -> Iterator[callable]:
    """Context manager yielding a zero-arg callable that returns elapsed seconds.

    Usage:
        with timed() as elapsed:
            do_work()
        duration = elapsed()
    """
    start = time.perf_counter()
    yield lambda: round(time.perf_counter() - start, 4)
