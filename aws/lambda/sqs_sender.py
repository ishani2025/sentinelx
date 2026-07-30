"""SQS sender for raw AWS Security Hub findings."""

from __future__ import annotations

import json
import logging
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import AWS_REGION, SQS_QUEUE_URL

logger = logging.getLogger(__name__)


class SQSSender:
    """Send Security Hub finding documents to an SQS standard queue."""

    def __init__(self, queue_url: str = SQS_QUEUE_URL, region_name: str = AWS_REGION) -> None:
        self.queue_url = queue_url
        self.client = boto3.client("sqs", region_name=region_name)

    def send_finding(self, finding: dict[str, Any]) -> str:
        """Send a single Security Hub finding as a JSON SQS message.

        Args:
            finding: Complete Security Hub finding document.

        Returns:
            The SQS message ID.

        Raises:
            BotoCoreError: If boto3 cannot complete the request.
            ClientError: If SQS rejects the request.
            TypeError: If the finding cannot be serialized to JSON.
        """
        response = self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(finding, default=str),
        )
        message_id = response["MessageId"]
        logger.info("Finding pushed to SQS", extra={"message_id": message_id})
        return message_id


def send_finding_to_sqs(finding: dict[str, Any]) -> str:
    """Send a finding using a short-lived sender instance."""
    try:
        return SQSSender().send_finding(finding)
    except (BotoCoreError, ClientError, TypeError):
        logger.exception("Failed to push finding to SQS")
        raise

