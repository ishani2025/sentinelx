"""Synthetic log generator for local connectors.

Emits realistic Linux syslog, Windows Event Log (forwarded via syslog), and
PAN-OS style firewall/VPN log lines so that SyslogConnector and
FirewallConnector have something to ingest. Runs continuously at a
configurable rate; with --scenario attack it periodically weaves in a
coordinated intrusion (compromised laptop logging in from Russia, an SSH
brute force, and a firewall threat alert) alongside random benign noise.
"""
from __future__ import annotations

import argparse
import random
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

LINUX_HOSTS = ["web01", "db02", "app03", "bastion01"]
LINUX_USERS = ["deploy", "ops", "svc-backup", "jsmith"]
WINDOWS_HOSTS = ["LAPTOP-JSMITH01", "WKSTN-MCHEN02", "DC01"]
FIREWALL_HOST = "acme-fw01"

ATTACKER_IP = "203.0.113.77"
INTERNAL_IPS = ["10.4.12.55", "10.4.12.71", "10.4.13.20", "198.51.100.10"]


def _rfc3164_ts(dt: datetime) -> str:
    return f"{dt.strftime('%b')} {dt.day:2d} {dt.strftime('%H:%M:%S')}"


def _rand_ip() -> str:
    return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


# ---------------------------------------------------------------------------
# Linux syslog lines
# ---------------------------------------------------------------------------

def gen_linux_benign(dt: datetime) -> str:
    host = random.choice(LINUX_HOSTS)
    user = random.choice(LINUX_USERS)
    pid = random.randint(1000, 32000)
    kind = random.choice(["ssh_ok", "sudo", "cron"])
    if kind == "ssh_ok":
        msg = (
            f"sshd[{pid}]: Accepted publickey for {user} from "
            f"{random.choice(INTERNAL_IPS)} port {random.randint(1024, 65000)} ssh2"
        )
    elif kind == "sudo":
        msg = f"sudo: {user} : TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND=/usr/bin/systemctl restart nginx"
    else:
        msg = f"CRON[{pid}]: ({user}) CMD (/usr/local/bin/backup.sh)"
    return f"<38>{_rfc3164_ts(dt)} {host} {msg}"


def gen_linux_bruteforce(dt: datetime, host: Optional[str] = None, src_ip: Optional[str] = None) -> str:
    host = host or random.choice(LINUX_HOSTS)
    pid = random.randint(1000, 32000)
    user = random.choice(["root", "admin", "test", "oracle"])
    ip = src_ip or _rand_ip()
    return (
        f"<38>{_rfc3164_ts(dt)} {host} sshd[{pid}]: Failed password for invalid user {user} "
        f"from {ip} port {random.randint(1024, 65000)} ssh2"
    )


# ---------------------------------------------------------------------------
# Windows Event Log lines (forwarded via syslog, Snare/NXLog style)
# ---------------------------------------------------------------------------

def _win_event_line(dt: datetime, host: str, user: str, ip: str, event_id: str, name: str, desc: str, logon_type: int) -> str:
    msg = (
        f"MSWinEventLog: 1 Security {random.randint(1000, 99999)} {dt.ctime()} {event_id} "
        f"Microsoft-Windows-Security-Auditing N/A N/A Success Audit {host} {name} {desc} "
        f"Account Name: {user} Source Network Address: {ip} Logon Type: {logon_type}"
    )
    return f"<14>{_rfc3164_ts(dt)} {host} {msg}"


def gen_windows_benign(dt: datetime) -> str:
    host = random.choice(WINDOWS_HOSTS)
    user = random.choice(["jsmith", "mchen", "svc-updater"])
    ip = random.choice(INTERNAL_IPS)
    event_id, name, desc = random.choice(
        [
            ("4624", "Logon", "An account was successfully logged on."),
            ("4688", "Process Creation", "A new process has been created."),
        ]
    )
    return _win_event_line(dt, host, user, ip, event_id, name, desc, logon_type=3)


def gen_windows_suspicious(
    dt: datetime, host: Optional[str] = None, user: Optional[str] = None, src_ip: Optional[str] = None
) -> str:
    host = host or random.choice(WINDOWS_HOSTS)
    user = user or "jsmith"
    ip = src_ip or ATTACKER_IP
    event_id, name, desc = random.choice(
        [
            ("4625", "Logon Failure", "An account failed to log on."),
            ("4720", "User Account Created", "A user account was created."),
            ("1102", "Audit Log Cleared", "The audit log was cleared."),
        ]
    )
    return _win_event_line(dt, host, user, ip, event_id, name, desc, logon_type=10)


def gen_windows_impossible_travel(dt: datetime) -> str:
    return _win_event_line(
        dt, "LAPTOP-JSMITH01", "jsmith", ATTACKER_IP, "4624", "Logon", "An account was successfully logged on.", 10
    )


# ---------------------------------------------------------------------------
# Firewall / VPN lines (PAN-OS style CSV, matches demo/sample_logs/3_firewall_vpn.log)
# ---------------------------------------------------------------------------

def gen_firewall_traffic(dt: datetime) -> str:
    src = random.choice(INTERNAL_IPS)
    dst = _rand_ip()
    port = random.choice([443, 80, 22, 3389])
    return (
        f"{dt.strftime('%Y-%m-%dT%H:%M:%SZ')} {FIREWALL_HOST} "
        f"1,{dt.strftime('%Y/%m/%d %H:%M:%S')},PA-VM,TRAFFIC,allow,outbound-web,"
        f"{src},{dst},{port},tcp,ALLOW,web-browsing,{random.choice(LINUX_USERS)},geo:United States,"
        f"bytes={random.randint(500, 50000)}"
    )


def gen_firewall_threat(dt: datetime, src_ip: Optional[str] = None, user: str = "jsmith", geo: str = "Russia") -> str:
    src = src_ip or ATTACKER_IP
    dst = random.choice(INTERNAL_IPS)
    return (
        f"{dt.strftime('%Y-%m-%dT%H:%M:%SZ')} {FIREWALL_HOST} "
        f"1,{dt.strftime('%Y/%m/%d %H:%M:%S')},PA-VM,THREAT,alert,anomaly,"
        f"{src},{dst},443,tcp,ALERT,impossible-travel,{user},geo:{geo}"
    )


Generator = Callable[[datetime], str]

BENIGN_CHOICES: list[tuple[str, Generator]] = [
    ("syslog", gen_linux_benign),
    ("syslog", gen_windows_benign),
    ("firewall", gen_firewall_traffic),
]

ATTACK_SEQUENCE: list[tuple[str, Generator]] = [
    ("syslog", gen_windows_impossible_travel),
    ("syslog", lambda dt: gen_linux_bruteforce(dt, host="bastion01", src_ip=ATTACKER_IP)),
    ("firewall", lambda dt: gen_firewall_threat(dt)),
]


class Sink:
    def send(self, category: str, line: str) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass


class UdpSink(Sink):
    def __init__(self, syslog_host: str, syslog_port: int, firewall_host: str, firewall_port: int):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._addrs = {
            "syslog": (syslog_host, syslog_port),
            "firewall": (firewall_host, firewall_port),
        }

    def send(self, category: str, line: str) -> None:
        self._sock.sendto(line.encode("utf-8"), self._addrs[category])

    def close(self) -> None:
        self._sock.close()


class FileSink(Sink):
    def __init__(self, syslog_file: str, firewall_file: str):
        self._paths = {"syslog": Path(syslog_file), "firewall": Path(firewall_file)}
        for path in self._paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, category: str, line: str) -> None:
        with self._paths[category].open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def run(args: argparse.Namespace) -> None:
    if args.seed is not None:
        random.seed(args.seed)

    sink: Sink
    if args.sink == "udp":
        sink = UdpSink(args.syslog_host, args.syslog_port, args.firewall_host, args.firewall_port)
    else:
        sink = FileSink(args.syslog_file, args.firewall_file)

    interval = 1.0 / args.rate if args.rate > 0 else 0
    emitted = 0
    tick = 0

    print(f"Generating logs (scenario={args.scenario}, sink={args.sink}, rate={args.rate}/s). Ctrl+C to stop.")

    try:
        while args.count == 0 or emitted < args.count:
            dt = datetime.now(timezone.utc)
            tick += 1

            if args.scenario == "attack" and tick % 8 == 0:
                category, generator = ATTACK_SEQUENCE[(tick // 8 - 1) % len(ATTACK_SEQUENCE)]
            elif args.scenario == "normal" and random.random() < 0.05:
                category, generator = "syslog", gen_linux_bruteforce
            else:
                category, generator = random.choice(BENIGN_CHOICES)

            line = generator(dt)
            sink.send(category, line)
            print(line)

            emitted += 1
            if interval:
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        sink.close()

    print(f"Emitted {emitted} events.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synthetic Windows/Linux/firewall log generator for local connectors."
    )
    parser.add_argument("--sink", choices=["udp", "file"], default="udp")
    parser.add_argument("--syslog-host", default="127.0.0.1")
    parser.add_argument("--syslog-port", type=int, default=5514)
    parser.add_argument("--firewall-host", default="127.0.0.1")
    parser.add_argument("--firewall-port", type=int, default=5515)
    parser.add_argument("--syslog-file", default="demo/sample_logs/live_syslog.log")
    parser.add_argument("--firewall-file", default="demo/sample_logs/live_firewall.log")
    parser.add_argument("--rate", type=float, default=1.0, help="events per second")
    parser.add_argument("--count", type=int, default=0, help="total events to emit, 0 = run forever")
    parser.add_argument("--scenario", choices=["normal", "attack"], default="normal")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
