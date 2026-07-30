"""EDR connector.

Parses CrowdStrike Falcon style detection alerts, e.g.:

    {
      "meta": {"version": "1.0", "vendor": "CrowdStrike Falcon"},
      "event": {
        "DetectName": "Credential Theft via Infostealer",
        "Severity": 8, "SeverityName": "High",
        "Tactic": "Credential Access", "Technique": "T1555.003 Credentials from Web Browsers",
        "Timestamp": "2026-07-30T09:00:12Z", "ComputerName": "LAPTOP-JSMITH01",
        "UserName": "acme\\jsmith", "LocalIP": "10.4.12.55", "ExternalIP": "203.0.113.77", ...
      }
    }

which matches demo/sample_logs/1_edr_alert.json. Reads a JSON file: either a
single detection object, a JSON array of detection objects, or (once the
seed content has been replayed) newline-delimited JSON appended to the file
for continued live tailing.
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

_SEVERITY_BY_NAME = {
    "critical": "HIGH",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "INFO",
    "informational": "INFO",
}


class EDRConnector(BaseConnector):
    """Replays/tails CrowdStrike Falcon style EDR detection JSON."""

    source_type = "edr"

    def __init__(
        self,
        name: str = "edr",
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
        logger.info("EDRConnector started on %s", self.file_path)

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
            logger.debug("EDR seed file is not a single JSON document, skipping")
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
            logger.debug("Unrecognized EDR line: %s", line)
            return None
        return data if isinstance(data, dict) else None

    def parse_event(self, raw: dict[str, Any]) -> Optional[NormalizedEvent]:
        ev = raw.get("event", raw)

        detect_name = ev.get("DetectName", "Detection")
        severity_name = ev.get("SeverityName", "Informational")
        severity = _SEVERITY_BY_NAME.get(str(severity_name).lower(), "INFO")
        technique = ev.get("Technique") or ""
        technique_id = technique.split(" ", 1)[0].lower().replace(".", "_") if technique else "unknown"

        return NormalizedEvent(
            source=ev.get("ComputerName", "edr"),
            source_type="edr",
            event_type=f"edr.detection.{technique_id}",
            raw=json.dumps(raw),
            timestamp=ev.get("Timestamp"),
            severity=severity,
            host=ev.get("ComputerName"),
            user=ev.get("UserName"),
            src_ip=ev.get("LocalIP"),
            dest_ip=ev.get("ExternalIP"),
            details={
                "detect_name": detect_name,
                "description": ev.get("DetectDescription"),
                "severity_score": ev.get("Severity"),
                "tactic": ev.get("Tactic"),
                "technique": technique,
                "file_name": ev.get("FileName"),
                "sha256": ev.get("SHA256"),
                "parent_process": ev.get("ParentProcess"),
            },
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the EDR connector standalone and print received events.")
    parser.add_argument("--file", default="demo/sample_logs/1_edr_alert.json")
    parser.add_argument("--delay", type=float, default=0.0, help="seconds to sleep between replayed events")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    def _print_event(event: NormalizedEvent) -> None:
        print(event.to_dict())

    connector = EDRConnector(file_path=args.file, replay_delay=args.delay, on_event=_print_event)
    connector.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        connector.stop()
