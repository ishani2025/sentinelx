"""Okta connector.

Parses Okta System Log events, e.g.:

    {
      "uuid": "a1b2c3d4-0001", "published": "2026-07-30T09:12:44Z",
      "eventType": "user.session.start", "severity": "WARN",
      "outcome": {"result": "SUCCESS"},
      "actor": {"alternateId": "jsmith@acme.com", "displayName": "Jane Smith"},
      "client": {"ipAddress": "203.0.113.77", "geographicalContext": {"country": "Russia"}},
      "debugContext": {"debugData": {"riskLevel": "HIGH", "riskReasons": "..."}}
    }

which matches demo/sample_logs/2_okta_system_log.json (a JSON array of such
events, as returned by the Okta System Log API). Reads a JSON file: a JSON
array of events, a single event object, or (once the seed content has been
replayed) newline-delimited JSON appended to the file for continued live
tailing.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Optional

from ingestion.connectors.base_connector import BaseConnector, EventHandler
from normalization.event_model import NormalizedEvent

logger = logging.getLogger(__name__)

_SEVERITY_BY_RISK_LEVEL = {
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "INFO",
}

_SEVERITY_BY_OKTA_LEVEL = {
    "error": "HIGH",
    "warn": "MEDIUM",
    "info": "INFO",
    "debug": "INFO",
}


class OktaConnector(BaseConnector):
    """Replays/tails Okta System Log JSON."""

    source_type = "okta"

    def __init__(
        self,
        name: str = "okta",
        file_path: Optional[str] = None,
        from_start: bool = True,
        replay_delay: float = 0.0,
        poll_interval: float = 0.5,
        on_event: Optional[EventHandler] = None,
    ):
        super().__init__(name, on_event)
        if not file_path:
            raise ValueError("file_path is required")
        self.file_path = Path(file_path)
        self.from_start = from_start
        self.replay_delay = replay_delay
        self.poll_interval = poll_interval
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("OktaConnector started on %s", self.file_path)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self) -> None:
        while self._running and not self.file_path.exists():
            time.sleep(self.poll_interval)
        if not self._running:
            return

        with self.file_path.open("r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
            end_of_seed = handle.tell()

        if self.from_start and text.strip():
            for raw in self._parse_seed(text):
                if not self._running:
                    return
                event = self.parse_event(raw)
                if event:
                    self._emit(event)
                if self.replay_delay:
                    time.sleep(self.replay_delay)

        with self.file_path.open("r", encoding="utf-8", errors="replace") as handle:
            handle.seek(end_of_seed)
            while self._running:
                line = handle.readline()
                if not line or not line.strip():
                    time.sleep(self.poll_interval)
                    continue
                raw = self._parse_line(line)
                if raw is None:
                    continue
                event = self.parse_event(raw)
                if event:
                    self._emit(event)

    @staticmethod
    def _parse_seed(text: str) -> list[dict[str, Any]]:
        try:
            data = json.loads(text)
        except ValueError:
            logger.debug("Okta seed file is not a single JSON document, skipping")
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            return [data]
        return []

    @staticmethod
    def _parse_line(line: str) -> Optional[dict[str, Any]]:
        try:
            data = json.loads(line)
        except ValueError:
            logger.debug("Unrecognized Okta line: %s", line)
            return None
        return data if isinstance(data, dict) else None

    def parse_event(self, raw: dict[str, Any]) -> Optional[NormalizedEvent]:
        actor = raw.get("actor") or {}
        client = raw.get("client") or {}
        outcome = raw.get("outcome") or {}
        geo = client.get("geographicalContext") or {}
        debug_data = (raw.get("debugContext") or {}).get("debugData") or {}
        security_context = raw.get("securityContext") or {}

        risk_level = debug_data.get("riskLevel")
        if risk_level:
            severity = _SEVERITY_BY_RISK_LEVEL.get(str(risk_level).lower(), "INFO")
        else:
            severity = _SEVERITY_BY_OKTA_LEVEL.get(str(raw.get("severity", "")).lower(), "INFO")

        event_type = raw.get("eventType") or "event"

        return NormalizedEvent(
            source="okta",
            source_type="okta",
            event_type=f"okta.{event_type}",
            raw=json.dumps(raw),
            timestamp=raw.get("published"),
            severity=severity,
            host=None,
            user=actor.get("alternateId") or actor.get("displayName"),
            src_ip=client.get("ipAddress"),
            dest_ip=None,
            details={
                "uuid": raw.get("uuid"),
                "display_message": raw.get("displayMessage"),
                "outcome_result": outcome.get("result"),
                "geo_country": geo.get("country"),
                "geo_city": geo.get("city"),
                "risk_level": risk_level,
                "risk_reasons": debug_data.get("riskReasons"),
                "as_org": security_context.get("asOrg"),
                "is_proxy": security_context.get("isProxy"),
            },
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the Okta connector standalone and print received events.")
    parser.add_argument("--file", default="demo/sample_logs/2_okta_system_log.json")
    parser.add_argument("--delay", type=float, default=0.0, help="seconds to sleep between replayed events")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    def _print_event(event: NormalizedEvent) -> None:
        print(event.to_dict())

    connector = OktaConnector(file_path=args.file, replay_delay=args.delay, on_event=_print_event)
    connector.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        connector.stop()
