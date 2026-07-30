"""Structured logging for the Risk Assessment Node."""
from __future__ import annotations
import json, logging
from typing import Any
_logger = logging.getLogger("sentinelx.risk")
if not _logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        '{"ts":"%(asctime)s","level":"%(levelname)s","component":"%(name)s","msg":%(message)s}'))
    _logger.addHandler(_h); _logger.setLevel(logging.INFO)
def log(event: str, **f: Any) -> None: _logger.info(json.dumps({"event": event, **f}, default=str))
def log_error(event: str, error, **f: Any) -> None: _logger.error(json.dumps({"event": event, "error": str(error), **f}, default=str))
