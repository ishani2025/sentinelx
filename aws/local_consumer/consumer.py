"""Long-polling SQS consumer for raw Security Hub findings."""

from __future__ import annotations

import json
import logging
import time
from json import JSONDecodeError
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import AppConfig
from priority_queue_manager import PriorityQueueManager

logger = logging.getLogger(__name__)


class SQSConsumer:
    """Poll SQS for Security Hub findings and enqueue them locally."""

    def __init__(self, config: AppConfig, queue_manager: PriorityQueueManager) -> None:
        self.config = config
        self.queue_manager = queue_manager
        self.client = boto3.client("sqs", region_name=config.aws_region)

    def run_forever(self) -> None:
        """Continuously poll SQS using long polling."""
        logger.info("SQS consumer started")
        while True:
            try:
                processed_count = self.poll_once()
                if processed_count == 0:
                    logger.debug("No SQS messages received")
            except (BotoCoreError, ClientError, JSONDecodeError, ValueError):
                logger.exception("SQS polling cycle failed")
                time.sleep(self.config.poll_retry_seconds)

    def poll_once(self) -> int:
        """Poll SQS once and process any received messages.

        Returns:
            Number of messages successfully enqueued and deleted.
        """
        response = self.client.receive_message(
            QueueUrl=self.config.sqs_queue_url,
            MaxNumberOfMessages=self.config.max_number_of_messages,
            WaitTimeSeconds=self.config.wait_time_seconds,
            VisibilityTimeout=self.config.visibility_timeout,
            MessageAttributeNames=["All"],
            AttributeNames=["All"],
        )

        messages = response.get("Messages", [])
        processed_count = 0

        for message in messages:
            if self._process_message(message):
                processed_count += 1

        return processed_count

    def _process_message(self, message: dict[str, Any]) -> bool:
        """Deserialize, enqueue, and delete a single SQS message."""
        message_id = message.get("MessageId", "unknown")
        receipt_handle = message["ReceiptHandle"]
        logger.info("Message received", extra={"message_id": message_id})

        try:
            finding = json.loads(message["Body"])
            if not isinstance(finding, dict):
                raise ValueError("SQS message body must be a JSON object")

            self.queue_manager.enqueue(finding)
            self._delete_message(receipt_handle, message_id)
            return True
        except (JSONDecodeError, ValueError):
            logger.exception(
                "Message processing failed; message will not be deleted",
                extra={"message_id": message_id},
            )
            return False
        except (BotoCoreError, ClientError):
            logger.exception(
                "AWS operation failed; message will not be deleted",
                extra={"message_id": message_id},
            )
            return False

    def _delete_message(self, receipt_handle: str, message_id: str) -> None:
        """Delete a successfully processed SQS message."""
        self.client.delete_message(
            QueueUrl=self.config.sqs_queue_url,
            ReceiptHandle=receipt_handle,
        )
        logger.info("Message deleted", extra={"message_id": message_id})

