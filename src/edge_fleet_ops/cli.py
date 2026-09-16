from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Settings, load_nodes
from .control_plane import FleetControlClient
from .disk_health import audit_node as audit_disk
from .outbox import AlertOutbox
from .ssh import SSHRunner
from .workload_health import audit_node as audit_workload


def _context(config_path: str):
    settings = Settings.from_env()
    declared = load_nodes(config_path)
    live = FleetControlClient(settings.control_api_url).fetch()
    runner = SSHRunner(settings.ssh_user, settings.ssh_key)
    return settings, declared, live, runner


def cmd_audit_disk(args: argparse.Namespace) -> int:
    settings, declared, live, runner = _context(args.nodes)
    reports = []
    for item in declared:
        node_id = item["node_id"]
        record = live.get(node_id)
        hosts = list(record.ipv6_candidates if record else ()) + list(item.get("hosts") or [])
        if not hosts:
            reports.append({"node_id": node_id, "severity": "critical", "error": "no host candidates"})
            continue
        try:
            report = audit_disk(node_id, hosts, runner,
                                warn_percent=settings.disk_warn_percent,
                                critical_percent=settings.disk_critical_percent,
                                min_free_mb=settings.disk_min_free_mb)
            reports.append(report.to_dict())
        except Exception as exc:
            reports.append({"node_id": node_id, "severity": "critical", "error": str(exc)})
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0


def cmd_check_workloads(args: argparse.Namespace) -> int:
    _, declared, live, runner = _context(args.nodes)
    reports = []
    for item in declared:
        node_id = item["node_id"]
        record = live.get(node_id)
        hosts = list(record.ipv6_candidates if record else ()) + list(item.get("hosts") or [])
        if not hosts:
            reports.append({"node_id": node_id, "severity": "critical", "error": "no host candidates"})
            continue
        try:
            reports.append(audit_workload(node_id, hosts, runner).to_dict())
        except Exception as exc:
            reports.append({"node_id": node_id, "severity": "critical", "error": str(exc)})
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0


def cmd_drain(args: argparse.Namespace) -> int:
    for message in AlertOutbox(args.path).drain(args.limit):
        print(message)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="edge-fleet-ops")
    sub = p.add_subparsers(dest="command", required=True)
    d = sub.add_parser("audit-disk", help="audit disk health across configured nodes")
    d.add_argument("--nodes", default="config/nodes.example.json")
    d.set_defaults(func=cmd_audit_disk)
    w = sub.add_parser("check-workloads", help="check container/process health")
    w.add_argument("--nodes", default="config/nodes.example.json")
    w.set_defaults(func=cmd_check_workloads)
    q = sub.add_parser("drain-alerts", help="atomically drain pending alert messages")
    q.add_argument("--path", default="./var/state/alerts.jsonl")
    q.add_argument("--limit", type=int, default=10)
    q.set_defaults(func=cmd_drain)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
