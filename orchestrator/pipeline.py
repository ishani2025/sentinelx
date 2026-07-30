"""Wires ingestion connectors into the correlator.

Each connector normalizes its own source into NormalizedEvent; the pipeline
just fans those events out to an optional observer and into the Correlator,
forwarding any raised Incident to an optional observer as well.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from correlation.correlator import Correlator, Incident
from ingestion.connectors.base_connector import BaseConnector
from ingestion.connectors.edr_connector import EDRConnector
from ingestion.connectors.firewall_connector import FirewallConnector
from ingestion.connectors.okta_connector import OktaConnector
from normalization.event_model import NormalizedEvent

logger = logging.getLogger(__name__)


class Pipeline:
    """Starts a set of connectors and routes their events through a Correlator."""

    def __init__(
        self,
        correlator: Optional[Correlator] = None,
        on_event: Optional[Callable[[NormalizedEvent], None]] = None,
        on_incident: Optional[Callable[[Incident], None]] = None,
    ):
        self.correlator = correlator or Correlator()
        self.connectors: list[BaseConnector] = []
        self._on_event = on_event
        self._on_incident = on_incident

    def add_connector(self, connector: BaseConnector) -> BaseConnector:
        self.connectors.append(connector)
        return connector

    def handle_event(self, event: NormalizedEvent) -> None:
        logger.info("%s: %s [%s]", event.source_type, event.event_type, event.severity)
        if self._on_event:
            self._on_event(event)
        incident = self.correlator.ingest(event)
        if incident and self._on_incident:
            self._on_incident(incident)

    def start(self) -> None:
        for connector in self.connectors:
            connector.start()

    def stop(self) -> None:
        for connector in self.connectors:
            connector.stop()

    @classmethod
    def from_sample_logs(cls, sample_dir: str = "demo/sample_logs", **kwargs) -> "Pipeline":
        """Builds a pipeline over the three file-based demo sources
        (EDR, Okta, firewall) that carry the correlated jsmith attack story."""
        pipeline = cls(**kwargs)
        pipeline.add_connector(
            EDRConnector(file_path=f"{sample_dir}/1_edr_alert.json", on_event=pipeline.handle_event)
        )
        pipeline.add_connector(
            OktaConnector(file_path=f"{sample_dir}/2_okta_system_log.json", on_event=pipeline.handle_event)
        )
        pipeline.add_connector(
            FirewallConnector(
                mode="file",
                file_path=f"{sample_dir}/3_firewall_vpn.log",
                from_start=True,
                on_event=pipeline.handle_event,
            )
        )
        return pipeline
