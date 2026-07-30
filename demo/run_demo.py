"""End-to-end demo: replay the sample logs, correlate them, print the incident.

Ingests demo/sample_logs/1_edr_alert.json, 2_okta_system_log.json, and
3_firewall_vpn.log through their connectors, feeds every NormalizedEvent
through the Correlator, and prints the resulting incident once the same
user (jsmith) shows up across all three sources within the correlation
window.
"""
from __future__ import annotations

import logging
import time

from correlation.correlator import Incident
from normalization.event_model import NormalizedEvent
from orchestrator.pipeline import Pipeline

REPLAY_SECONDS = 2


def _print_event(event: NormalizedEvent) -> None:
    print(f"  [{event.severity:6}] {event.source_type:8} {event.event_type:35} user={event.user}")


def _print_incident(incident: Incident) -> None:
    print()
    print(f"INCIDENT {incident.incident_id}")
    print(f"  {incident.title}")
    print(f"  severity={incident.severity} sources={incident.source_types}")
    for event in incident.events:
        print(f"    - {event.timestamp} {event.event_type} ({event.severity})")
    print()


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")

    print("Ingesting demo/sample_logs ...")
    pipeline = Pipeline.from_sample_logs(on_event=_print_event, on_incident=_print_incident)
    pipeline.start()
    time.sleep(REPLAY_SECONDS)
    pipeline.stop()
    print("Done.")


if __name__ == "__main__":
    main()
