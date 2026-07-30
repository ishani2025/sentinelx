"""Structured logging for the Business Context Node."""
from __future__ import annotations
import json, logging
from typing import Any

_logger = logging.getLogger("sentinelx.business")
if not _logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        '{"ts":"%(asctime)s","level":"%(levelname)s","component":"%(name)s","msg":%(message)s}'))
    _logger.addHandler(_h); _logger.setLevel(logging.INFO)

def log(event: str, **fields: Any) -> None:
    _logger.info(json.dumps({"event": event, **fields}, default=str))

def log_error(event: str, error, **fields: Any) -> None:
    _logger.error(json.dumps({"event": event, "error": str(error), **fields}, default=str))
