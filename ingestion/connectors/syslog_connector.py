"""Syslog connector.

Receives Linux syslog/auth events over UDP, plus Windows Event Log entries
forwarded as syslog by an agent such as NXLog or Snare (the common way to
get Windows Security log events onto a syslog pipeline without WEF/WinRM).
Normalizes both into `NormalizedEvent`.
"""
from __future__ import annotations

import logging
import re
import socket
import threading
from typing import Optional

from ingestion.connectors.base_connector import BaseConnector, EventHandler
from normalization.event_model import NormalizedEvent

logger = logging.getLogger(__name__)

# RFC 3164: <PRI>Mon DD HH:MM:SS host process[pid]: message
_RFC3164_RE = re.compile(
    r"^<(?P<pri>\d+)>"
    r"(?P<ts>\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})\s"
    r"(?P<host>\S+)\s"
    r"(?P<process>[\w\-.]+?)(\[(?P<pid>\d+)\])?:\s"
    r"(?P<message>.*)$"
)

_SSH_FAILED_RE = re.compile(r"Failed password for (invalid user )?(?P<user>\S+) from (?P<ip>[\d.]+) port \d+")
_SSH_ACCEPTED_RE = re.compile(r"Accepted (password|publickey) for (?P<user>\S+) from (?P<ip>[\d.]+) port \d+")
_SUDO_RE = re.compile(r"^(?P<user>\S+) : .*COMMAND=(?P<command>.*)$")

# Windows Event Log forwarded via syslog (Snare/NXLog style single-line format).
_WIN_EVENT_ID_RE = re.compile(r"\b(?P<event_id>4624|4625|4688|4720|4732|1102)\b")
_WIN_ACCOUNT_RE = re.compile(r"Account Name:\s*(?P<user>[\w.\-\\]+)")
_WIN_SRC_IP_RE = re.compile(r"Source Network Address:\s*(?P<ip>[\d.]+)")

_WIN_EVENT_MEANING = {
    "4624": ("windows.logon.success", "INFO"),
    "4625": ("windows.logon.failure", "MEDIUM"),
    "4688": ("windows.process.create", "INFO"),
    "4720": ("windows.account.created", "MEDIUM"),
    "4732": ("windows.group.member_added", "MEDIUM"),
    "1102": ("windows.audit_log.cleared", "HIGH"),
}


class SyslogConnector(BaseConnector):
    """UDP syslog receiver for Linux hosts and Windows hosts forwarding
    Event Log entries via a syslog agent."""

    source_type = "syslog"

    def __init__(
        self,
        name: str = "syslog",
        host: str = "0.0.0.0",
        port: int = 5514,
        on_event: Optional[EventHandler] = None,
    ):
        super().__init__(name, on_event)
        self.host = host
        self.port = port
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self.host, self.port))
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        logger.info("SyslogConnector listening on %s:%d", self.host, self.port)

    def stop(self) -> None:
        self._running = False
        if self._sock:
            self._sock.close()
        if self._thread:
            self._thread.join(timeout=1)

    def _listen(self) -> None:
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
        match = _RFC3164_RE.match(line)
        if not match:
            logger.debug("Unrecognized syslog line: %s", line)
            return None

        host = match.group("host")
        process = match.group("process")
        message = match.group("message")

        win_match = _WIN_EVENT_ID_RE.search(message)
        if process == "MSWinEventLog" or win_match:
            return self._parse_windows_event(line, host, message, win_match)

        return self._parse_linux_event(line, host, process, message)

    def _parse_linux_event(self, raw: str, host: str, process: str, message: str) -> NormalizedEvent:
        event_type = "linux.syslog"
        severity = "INFO"
        user = None
        src_ip = None

        failed = _SSH_FAILED_RE.search(message)
        accepted = _SSH_ACCEPTED_RE.search(message)
        sudo = _SUDO_RE.search(message)

        if failed:
            event_type, severity = "linux.ssh.login_failed", "MEDIUM"
            user, src_ip = failed.group("user"), failed.group("ip")
        elif accepted:
            event_type = "linux.ssh.login_success"
            user, src_ip = accepted.group("user"), accepted.group("ip")
        elif sudo:
            event_type = "linux.sudo.command"
            user = sudo.group("user")

        return NormalizedEvent(
            source=host,
            source_type="linux",
            event_type=event_type,
            raw=raw,
            severity=severity,
            host=host,
            user=user,
            src_ip=src_ip,
            details={"process": process, "message": message},
        )

    def _parse_windows_event(
        self, raw: str, host: str, message: str, win_match: Optional[re.Match]
    ) -> NormalizedEvent:
        event_id = win_match.group("event_id") if win_match else None
        event_type, severity = _WIN_EVENT_MEANING.get(event_id, ("windows.event", "INFO"))

        user_match = _WIN_ACCOUNT_RE.search(message)
        ip_match = _WIN_SRC_IP_RE.search(message)

        return NormalizedEvent(
            source=host,
            source_type="windows",
            event_type=event_type,
            raw=raw,
            severity=severity,
            host=host,
            user=user_match.group("user") if user_match else None,
            src_ip=ip_match.group("ip") if ip_match else None,
            details={"windows_event_id": event_id, "message": message},
        )


if __name__ == "__main__":
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Run the syslog connector standalone and print received events.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5514)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    def _print_event(event: NormalizedEvent) -> None:
        print(event.to_dict())

    connector = SyslogConnector(host=args.host, port=args.port, on_event=_print_event)
    connector.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        connector.stop()
