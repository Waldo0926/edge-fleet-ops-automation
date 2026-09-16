from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import re
from typing import Any

from .ssh import SSHRunner


REMOTE_DISK_AUDIT = r'''sh -s <<'SH'
set +e
printf '__HOSTNAME__\n'; hostname 2>/dev/null || true
printf '__LSBLK__\n'; lsblk -b -P -o NAME,TYPE,SIZE,MODEL,SERIAL,ROTA,TRAN,MOUNTPOINT 2>/dev/null || true
printf '__DF__\n'; df -P -BM / 2>/dev/null || true
printf '__SMART__\n'
for dev in /dev/sda /dev/sdb /dev/nvme0n1 /dev/mmcblk0; do
  [ -b "$dev" ] || continue
  echo "DEVICE=$dev"
  smartctl -a "$dev" 2>/dev/null | grep -E 'SMART overall-health|Percentage Used|Media_Wearout_Indicator|Reallocated_Sector_Ct|Current_Pending_Sector|Offline_Uncorrectable|Power_On_Hours' || true
done
printf '__NVME__\n'; nvme smart-log /dev/nvme0 2>/dev/null || true
printf '__MMC__\n'; mmc extcsd read /dev/mmcblk0 2>/dev/null | grep -E 'DEVICE_LIFE_TIME_EST_TYP|PRE_EOL_INFO' || true
SH'''


@dataclass
class DiskHealthReport:
    node_id: str
    host: str
    severity: str
    root_used_percent: int | None
    root_free_mb: int | None
    warnings: list[str]
    raw_excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_root_df(text: str) -> tuple[int | None, int | None]:
    section = text.split("__DF__", 1)[-1].split("__SMART__", 1)[0]
    for line in section.splitlines():
        m = re.search(r"\s(\d+)M\s+(\d+)M\s+(\d+)M\s+(\d+)%\s+/\s*$", line)
        if m:
            return int(m.group(4)), int(m.group(3))
    return None, None


def classify_disk_health(text: str, warn_percent: int = 80, critical_percent: int = 90,
                         min_free_mb: int = 1024) -> tuple[str, list[str]]:
    used, free = parse_root_df(text)
    warnings: list[str] = []
    severity = "ok"
    if used is None:
        warnings.append("root filesystem usage could not be parsed")
        severity = "warning"
    else:
        if used >= critical_percent:
            warnings.append(f"root filesystem usage is critical ({used}%)")
            severity = "critical"
        elif used >= warn_percent:
            warnings.append(f"root filesystem usage is high ({used}%)")
            severity = "warning"
    if free is not None and free < min_free_mb:
        warnings.append(f"root filesystem free space is low ({free} MB)")
        severity = "critical" if severity == "critical" or free < min_free_mb // 2 else "warning"

    bad_patterns = {
        "reallocated sectors": r"Reallocated_Sector_Ct\s+.*?\s([1-9]\d*)\s*$",
        "pending sectors": r"Current_Pending_Sector\s+.*?\s([1-9]\d*)\s*$",
        "uncorrectable sectors": r"Offline_Uncorrectable\s+.*?\s([1-9]\d*)\s*$",
        "SMART failure": r"SMART overall-health.*?(FAILED|BAD)",
    }
    for label, pattern in bad_patterns.items():
        if re.search(pattern, text, re.I | re.M):
            warnings.append(label)
            severity = "critical"

    pct = re.search(r"percentage_used\s*:\s*(\d+)%", text, re.I)
    if pct and int(pct.group(1)) >= 80:
        warnings.append(f"NVMe wear is high ({pct.group(1)}% used)")
        severity = "warning" if severity == "ok" else severity
    return severity, warnings


def audit_node(node_id: str, hosts: list[str], runner: SSHRunner, *, warn_percent: int = 80,
               critical_percent: int = 90, min_free_mb: int = 1024) -> DiskHealthReport:
    result = runner.first_reachable(hosts, REMOTE_DISK_AUDIT)
    severity, warnings = classify_disk_health(result.stdout, warn_percent, critical_percent, min_free_mb)
    used, free = parse_root_df(result.stdout)
    return DiskHealthReport(
        node_id=node_id,
        host=result.host,
        severity=severity,
        root_used_percent=used,
        root_free_mb=free,
        warnings=warnings,
        raw_excerpt=result.stdout[-4000:],
    )


def reports_json(reports: list[DiskHealthReport]) -> str:
    return json.dumps([r.to_dict() for r in reports], ensure_ascii=False, indent=2)
