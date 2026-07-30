"""Structured logging configuration for SentinelX.

Every graph node logs a `node_start` / `node_end` (or `node_error`) event
through the logger returned by `get_logger`, so the full investigation is
traceable as a structured event stream (JSON in production, console-rendered
in development).
"""
from __future__ import annotations

import logging
import sys
from functools import lru_cache

import structlog

from config.settings import get_settings

_CONFIGURED = False


def configure_logging() -> None:
    """Idempotently configures structlog + stdlib logging from Settings."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True


@lru_cache(maxsize=None)
def get_logger(name: str) -> structlog.BoundLogger:
    """Returns a cached, structured logger bound to `name` (usually `__name__`)."""
    configure_logging()
    return structlog.get_logger(name)
