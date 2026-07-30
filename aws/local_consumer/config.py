"""Runtime configuration for the local SQS consumer."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised when required local configuration is missing."""


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class AppConfig:
    """Application settings loaded from environment variables."""

    aws_region: str
    sqs_queue_url: str
    visibility_timeout: int = 60
    wait_time_seconds: int = 20
    max_number_of_messages: int = 10
    poll_retry_seconds: int = 5

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Build application configuration from .env or process environment."""
        return cls(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            sqs_queue_url=_required_env("SQS_QUEUE_URL"),
            visibility_timeout=int(os.getenv("SQS_VISIBILITY_TIMEOUT", "60")),
            wait_time_seconds=int(os.getenv("SQS_WAIT_TIME_SECONDS", "20")),
            max_number_of_messages=int(os.getenv("SQS_MAX_MESSAGES", "10")),
            poll_retry_seconds=int(os.getenv("SQS_POLL_RETRY_SECONDS", "5")),
        )

