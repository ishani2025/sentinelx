"""Dispatcher entry point for future AI investigation pipelines."""

from __future__ import annotations

import logging
import threading
from queue import Empty
from typing import Any

from priority_queue_manager import PriorityQueueManager
from utils import get_attack_type, get_finding_title, get_primary_resource, get_severity_label

logger = logging.getLogger(__name__)


class Dispatcher:
    """Continuously dispatch findings from the priority queue."""

    def __init__(self, queue_manager: PriorityQueueManager) -> None:
        self.queue_manager = queue_manager
        self._stop_event = threading.Event()

    def stop(self) -> None:
        """Signal the dispatcher loop to stop."""
        self._stop_event.set()

    def run_forever(self) -> None:
        """Continuously pop the highest-priority finding and dispatch it."""
        logger.info("Dispatcher execution started")
        while not self._stop_event.is_set():
            try:
                finding = self.queue_manager.dequeue(block=True, timeout=1.0)
            except Empty:
                continue

            try:
                self.dispatch(finding)
            finally:
                self.queue_manager.task_done()

    def dispatch(self, finding: dict[str, Any]) -> None:
        """Print finding details for the future AI pipeline handoff."""
        finding_id = finding.get("Id", "unknown")
        severity = get_severity_label(finding)
        title = get_finding_title(finding)
        attack_type = get_attack_type(finding)
        resource = get_primary_resource(finding)

        logger.info(
            "Dispatcher execution",
            extra={"finding_id": finding_id, "severity": severity},
        )

        print("=" * 80)
        print(f"Finding ID : {finding_id}")
        print(f"Severity   : {severity}")
        print(f"Title      : {title}")
        print(f"Attack Type: {attack_type}")
        print(f"Resource   : {resource}")
        print("=" * 80)

