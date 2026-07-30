"""Common interface shared by all ingestion connectors."""
from __future__ import annotations

import abc
import logging
from typing import Callable, Optional

from normalization.event_model import NormalizedEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[NormalizedEvent], None]


class BaseConnector(abc.ABC):
    """Base class for log/event source connectors.

    Subclasses acquire events from their source (a socket, a file tail, an
    API poll, ...) and call `self._emit(event)` for each one they normalize.
    """

    source_type: str = "generic"

    def __init__(self, name: str, on_event: Optional[EventHandler] = None):
        self.name = name
        self._on_event = on_event
        self._running = False

    @abc.abstractmethod
    def start(self) -> None:
        """Begin consuming events. Must not block the calling thread."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop consuming events and release any resources."""

    @property
    def running(self) -> bool:
        return self._running

    def _emit(self, event: NormalizedEvent) -> None:
        logger.debug("%s emitted %s event %s", self.name, event.event_type, event.event_id)
        if self._on_event:
            self._on_event(event)
