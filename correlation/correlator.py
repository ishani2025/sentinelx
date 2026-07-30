"""Cross-source event correlation.

Groups NormalizedEvents by the entity they share (primarily the user
account, normalized across each source's identity format: "jsmith",
"acme\\jsmith", "jsmith@acme.com" all resolve to the same key) within a
sliding time window. When a group spans two or more distinct source types
and includes at least one HIGH severity event, it is raised as an Incident
-- e.g. an Okta impossible-travel login, an EDR credential-theft detection,
and a firewall threat alert for the same user within minutes of each other.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from normalization.event_model import NormalizedEvent

logger = logging.getLogger(__name__)

_SEVERITY_RANK = {"INFO": 0, "MEDIUM": 1, "HIGH": 2}


@dataclass
class Incident:
    entity: str
    events: list[NormalizedEvent]
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def severity(self) -> str:
        return max((e.severity for e in self.events), key=lambda s: _SEVERITY_RANK.get(s, 0))

    @property
    def source_types(self) -> list[str]:
        return sorted({e.source_type for e in self.events})

    @property
    def title(self) -> str:
        return f"Correlated activity for '{self.entity}' across {', '.join(self.source_types)}"

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "entity": self.entity,
            "title": self.title,
            "severity": self.severity,
            "source_types": self.source_types,
            "created_at": self.created_at,
            "events": [e.to_dict() for e in self.events],
        }


def _canonical_user(user: Optional[str]) -> Optional[str]:
    if not user:
        return None
    name = user.split("\\")[-1]
    name = name.split("@")[0]
    return name.lower() or None


def _parse_timestamp(value: str, fallback: datetime) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return fallback


class Correlator:
    """Correlates events sharing a user entity within a sliding time window."""

    def __init__(
        self,
        window_seconds: float = 900,
        min_source_types: int = 2,
        on_incident: Optional[Callable[[Incident], None]] = None,
    ):
        self.window = timedelta(seconds=window_seconds)
        self.min_source_types = min_source_types
        self._on_incident = on_incident
        self._groups: dict[str, list[tuple[datetime, NormalizedEvent]]] = {}
        self._raised: set[str] = set()

    def ingest(self, event: NormalizedEvent) -> Optional[Incident]:
        key = _canonical_user(event.user)
        if key is None:
            return None

        now = datetime.now(timezone.utc)
        ts = _parse_timestamp(event.timestamp, fallback=now)
        bucket = self._groups.setdefault(key, [])
        bucket.append((ts, event))

        cutoff = max(t for t, _ in bucket) - self.window
        bucket[:] = [(t, e) for t, e in bucket if t >= cutoff]

        events = [e for _, e in bucket]
        source_types = {e.source_type for e in events}
        has_high = any(e.severity == "HIGH" for e in events)

        if len(source_types) < self.min_source_types or not has_high:
            return None

        event_ids = frozenset(e.event_id for e in events)
        if event_ids in self._raised:
            return None
        self._raised.add(event_ids)

        incident = Incident(entity=key, events=events)
        logger.info("Correlated incident %s: %s", incident.incident_id, incident.title)
        if self._on_incident:
            self._on_incident(incident)
        return incident
