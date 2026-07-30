"""Configuration helpers for the Security Hub ingestion Lambda."""

from __future__ import annotations

import os


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing."""


def get_required_env(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SQS_QUEUE_URL = get_required_env("SQS_QUEUE_URL")

