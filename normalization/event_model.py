"""Normalized event shape produced by every ingestion connector."""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class NormalizedEvent:
    source: str
    source_type: str
    event_type: str
    raw: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: str = "INFO"
    host: Optional[str] = None
    user: Optional[str] = None
    src_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
