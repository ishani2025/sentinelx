"""Firewall / VPN connector.

Parses PAN-OS style CSV log lines, e.g.:

    2026-07-30T09:11:59Z acme-fw01 1,2026/07/30 09:11:59,PA-VM,TRAFFIC,allow,vpn-portal,
    203.0.113.77,198.51.100.10,443,tcp,ALLOW,gp-portal,jsmith,geo:Russia,bytes=8421

which matches demo/sample_logs/3_firewall_vpn.log. Supports two ingestion
modes: tailing a log file (as a firewall's local syslog-ng/rsyslog output
would be tailed) or listening on a UDP port (as most firewalls emit).
"""
from __future__ import annotations

import logging
import re
import socket
import threading
import time
from pathlib import Path
from typing import Optional

from ingestion.connectors.base_connector import BaseConnector, EventHandler
from normalization.event_model import NormalizedEvent

logger = logging.getLogger(__name__)

# <iso-timestamp> <host> <seq>,<date>,<device>,<log_type>,<action>,<rule_or_threat>,
# <src_ip>,<dst_ip>,<port>,<proto>,<verdict>,<app_or_category>,<user>,<geo>[,<extra>...]
_LINE_RE = re.compile(r"^(?P<ts>\S+)\s+(?P<host>\S+)\s+(?P<csv>.+)$")

_FIELDS = (
    "seq",
    "device_date",
    "device",
    "log_type",
    "action",
    "rule_or_threat",
    "src_ip",
    "dst_ip",
    "port",
    "proto",
    "verdict",
    "app_or_category",
    "user",
    "geo",
)

_SEVERITY_BY_LOG_TYPE = {
    "TRAFFIC": "INFO",
    "THREAT": "HIGH",
}


class FirewallConnector(BaseConnector):
    """Reads PAN-OS style firewall/VPN logs from a file tail or a UDP socket."""

    source_type = "firewall"

    def __init__(
        self,
        name: str = "firewall",
        mode: str = "file",
        file_path: Optional[str] = None,
        host: str = "0.0.0.0",
        port: int = 5515,
        from_start: bool = False,
        poll_interval: float = 0.5,
        on_event: Optional[EventHandler] = None,
    ):
        super().__init__(name, on_event)
        if mode not in ("file", "udp"):
            raise ValueError("mode must be 'file' or 'udp'")
        self.mode = mode
        self.file_path = Path(file_path) if file_path else None
        self.host = host
        self.port = port
        self.from_start = from_start
        self.poll_interval = poll_interval
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None

        if mode == "file" and not self.file_path:
            raise ValueError("file_path is required when mode='file'")

    def start(self) -> None:
        self._running = True
        if self.mode == "file":
            self._thread = threading.Thread(target=self._tail_file, daemon=True)
        else:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.bind((self.host, self.port))
            self._thread = threading.Thread(target=self._listen_udp, daemon=True)
        self._thread.start()
        logger.info("FirewallConnector started in %s mode", self.mode)

    def stop(self) -> None:
        self._running = False
        if self._sock:
            self._sock.close()
        if self._thread:
            self._thread.join(timeout=1)

    def _tail_file(self) -> None:
        while self._running and not self.file_path.exists():
            time.sleep(self.poll_interval)

        with self.file_path.open("r", encoding="utf-8", errors="replace") as handle:
            if not self.from_start:
                handle.seek(0, 2)  # jump to end, only consume new lines
            while self._running:
                line = handle.readline()
                if not line:
                    time.sleep(self.poll_interval)
                    continue
                event = self.parse_line(line.strip())
                if event:
                    self._emit(event)

    def _listen_udp(self) -> None:
        while self._running:
            try:
                data, _addr = self._sock.recvfrom(65535)
            except OSError:
                break
            line = data.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            event = self.parse_line(line)
            if event:
                self._emit(event)

    def parse_line(self, line: str) -> Optional[NormalizedEvent]:
        if not line:
            return None
        match = _LINE_RE.match(line)
        if not match:
            logger.debug("Unrecognized firewall line: %s", line)
            return None

        parts = match.group("csv").split(",")
        if len(parts) < len(_FIELDS):
            logger.debug("Firewall line missing fields: %s", line)
            return None

        fields = dict(zip(_FIELDS, parts))
        extra = parts[len(_FIELDS):]
        fields["extra"] = extra

        log_type = fields["log_type"]
        severity = _SEVERITY_BY_LOG_TYPE.get(log_type, "INFO")
        event_type = f"firewall.{log_type.lower()}.{fields['action'].lower()}"

        return NormalizedEvent(
            source=match.group("host"),
            source_type="firewall",
            event_type=event_type,
            raw=line,
            timestamp=match.group("ts"),
            severity=severity,
            host=match.group("host"),
            user=fields["user"] or None,
            src_ip=fields["src_ip"] or None,
            dest_ip=fields["dst_ip"] or None,
            details=fields,
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the firewall connector standalone and print received events.")
    parser.add_argument("--mode", choices=["file", "udp"], default="file")
    parser.add_argument("--file", default="demo/sample_logs/3_firewall_vpn.log")
    parser.add_argument("--from-start", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5515)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    def _print_event(event: NormalizedEvent) -> None:
        print(event.to_dict())

    connector = FirewallConnector(
        mode=args.mode,
        file_path=args.file,
        host=args.host,
        port=args.port,
        from_start=args.from_start,
        on_event=_print_event,
    )
    connector.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        connector.stop()
