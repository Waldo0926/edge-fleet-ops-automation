from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Any

from .ssh import SSHRunner


REMOTE_WORKLOAD_AUDIT = r'''sh -s <<'SH'
set +e
echo '__HOST__'; hostname 2>/dev/null; date -Is 2>/dev/null
echo '__DF__'; df -P -BM / 2>/dev/null || true
echo '__CONTAINERS__'
if command -v docker >/dev/null 2>&1; then
  for c in $(docker ps -a --format '{{.Names}}' 2>/dev/null); do
    status=$(docker inspect "$c" --format '{{.State.Status}}' 2>/dev/null)
    pid=$(docker inspect "$c" --format '{{.State.Pid}}' 2>/dev/null)
    image=$(docker inspect "$c" --format '{{.Config.Image}}' 2>/dev/null)
    estab=0; sockets=0
    if [ -n "$pid" ] && [ "$pid" != 0 ] && [ -d "/proc/$pid" ]; then
      estab=$(ss -tnp 2>/dev/null | grep "$pid" | grep -c ESTAB || true)
      sockets=$(find "/proc/$pid/fd" -maxdepth 1 -type l -lname 'socket:*' 2>/dev/null | wc -l)
    fi
    printf 'CT\t%s\t%s\t%s\tPID=%s\tESTAB=%s\tSOCK=%s\n' "$c" "$image" "$status" "$pid" "$estab" "$sockets"
  done
fi
SH'''


@dataclass
class ContainerState:
    name: str
    image: str
    status: str
    pid: int | None
    established: int
    sockets: int


@dataclass
class WorkloadReport:
    node_id: str
    host: str
    severity: str
    containers: list[ContainerState]
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        return out


def parse_containers(text: str) -> list[ContainerState]:
    out: list[ContainerState] = []
    for line in text.splitlines():
        if not line.startswith("CT\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        extras = {m.group(1): m.group(2) for m in re.finditer(r"(PID|ESTAB|SOCK)=([^\t]+)", line)}
        try:
            pid = int(extras.get("PID", "0")) or None
        except ValueError:
            pid = None
        out.append(ContainerState(
            name=parts[1], image=parts[2], status=parts[3], pid=pid,
            established=int(extras.get("ESTAB", "0") or 0),
            sockets=int(extras.get("SOCK", "0") or 0),
        ))
    return out


def classify_workloads(containers: list[ContainerState]) -> tuple[str, list[str]]:
    if not containers:
        return "warning", ["no containers discovered"]
    reasons: list[str] = []
    severity = "ok"
    for c in containers:
        if c.status != "running":
            reasons.append(f"{c.name} is {c.status}")
            severity = "critical"
        elif c.established == 0 and c.sockets == 0:
            reasons.append(f"{c.name} is running but has no observed sockets")
            if severity != "critical":
                severity = "warning"
    return severity, reasons


def audit_node(node_id: str, hosts: list[str], runner: SSHRunner) -> WorkloadReport:
    result = runner.first_reachable(hosts, REMOTE_WORKLOAD_AUDIT)
    containers = parse_containers(result.stdout)
    severity, reasons = classify_workloads(containers)
    return WorkloadReport(node_id=node_id, host=result.host, severity=severity,
                          containers=containers, reasons=reasons)
