"""AWS Lambda entry point for Security Hub finding ingestion.

The Lambda is designed as an EventBridge target for the
"Security Hub Findings - Imported" event type. It preserves the full
Security Hub finding JSON and sends accepted severities to SQS.
"""

from __future__ import annotations

import copy
import logging
from datetime import datetime, timezone
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from sqs_sender import send_finding_to_sqs

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ACCEPTED_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
IGNORED_SEVERITIES = {"INFORMATIONAL"}


def _severity_label(finding: dict[str, Any]) -> str:
    """Extract a normalized Security Hub severity label from a finding."""
    severity = finding.get("Severity", {})
    label = severity.get("Label") or severity.get("Normalized") or "UNKNOWN"
    return str(label).upper()


def _decorate_finding(finding: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the finding with ingestion metadata added."""
    decorated = copy.deepcopy(finding)
    decorated["received_at"] = datetime.now(timezone.utc).isoformat()
    decorated["processing_status"] = "queued"
    decorated["source"] = event.get("source", "aws.securityhub")
    return decorated


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Process Security Hub findings from EventBridge and enqueue them in SQS."""
    logger.info(
        "Lambda invocation received",
        extra={
            "event_source": event.get("source"),
            "detail_type": event.get("detail-type"),
            "request_id": getattr(context, "aws_request_id", None),
        },
    )

    findings = event.get("detail", {}).get("findings", [])
    if not isinstance(findings, list):
        logger.error("Invalid event shape: detail.findings must be a list")
        return {
            "statusCode": 400,
            "body": {
                "message": "Invalid EventBridge event: detail.findings must be a list",
                "processed": 0,
                "ignored": 0,
                "failed": 0,
            },
        }

    processed = 0
    ignored = 0
    failed = 0

    for finding in findings:
        if not isinstance(finding, dict):
            ignored += 1
            logger.warning("Finding ignored because it is not a JSON object")
            continue

        finding_id = finding.get("Id", "unknown")
        severity = _severity_label(finding)
        logger.info(
            "Finding received",
            extra={"finding_id": finding_id, "severity": severity},
        )

        if severity in IGNORED_SEVERITIES or severity not in ACCEPTED_SEVERITIES:
            ignored += 1
            logger.info(
                "Finding ignored",
                extra={"finding_id": finding_id, "severity": severity},
            )
            continue

        try:
            decorated = _decorate_finding(finding, event)
            send_finding_to_sqs(decorated)
            processed += 1
            logger.info(
                "Finding queued successfully",
                extra={"finding_id": finding_id, "severity": severity},
            )
        except (BotoCoreError, ClientError, TypeError):
            failed += 1
            logger.exception(
                "Finding failed to queue",
                extra={"finding_id": finding_id, "severity": severity},
            )

    status_code = 207 if failed else 200
    return {
        "statusCode": status_code,
        "body": {
            "message": "Security Hub findings processed",
            "processed": processed,
            "ignored": ignored,
            "failed": failed,
        },
    }

