"""Priority queue management for Security Hub findings."""

from __future__ import annotations

import itertools
import logging
from queue import Empty, PriorityQueue
from typing import Any

from utils import get_severity_label

logger = logging.getLogger(__name__)


class PriorityQueueManager:
    """Manage Security Hub findings ordered by severity priority."""

    PRIORITY_MAP = {
        "CRITICAL": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4,
    }

    def __init__(self) -> None:
        self._queue: PriorityQueue[tuple[int, int, dict[str, Any]]] = PriorityQueue()
        self._counter = itertools.count()

    def enqueue(self, finding: dict[str, Any]) -> int:
        """Assign priority and enqueue a finding.

        Args:
            finding: Complete Security Hub finding document.

        Returns:
            The assigned numeric priority.

        Raises:
            ValueError: If the finding severity is unsupported.
        """
        severity = get_severity_label(finding)
        if severity not in self.PRIORITY_MAP:
            raise ValueError(f"Unsupported finding severity: {severity}")

        priority = self.PRIORITY_MAP[severity]
        self._queue.put((priority, next(self._counter), finding))
        logger.info(
            "Priority assigned",
            extra={
                "finding_id": finding.get("Id", "unknown"),
                "severity": severity,
                "priority": priority,
            },
        )
        return priority

    def dequeue(self, block: bool = True, timeout: float | None = None) -> dict[str, Any]:
        """Return the highest-priority finding from the queue."""
        try:
            _priority, _sequence, finding = self._queue.get(block=block, timeout=timeout)
            return finding
        except Empty:
            raise

    def task_done(self) -> None:
        """Mark the last dequeued item as processed."""
        self._queue.task_done()

    def is_empty(self) -> bool:
        """Return True when no findings are queued."""
        return self._queue.empty()

    def size(self) -> int:
        """Return the current number of queued findings."""
        return self._queue.qsize()

