from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    control_api_url: str
    ssh_user: str = "root"
    ssh_key: str | None = None
    state_dir: Path = Path("./var/state")
    log_dir: Path = Path("./var/log")
    disk_warn_percent: int = 80
    disk_critical_percent: int = 90
    disk_min_free_mb: int = 1024

    @classmethod
    def from_env(cls) -> "Settings":
        url = os.environ.get("EDGE_CONTROL_API", "").strip()
        if not url:
            raise ValueError("EDGE_CONTROL_API is required")
        return cls(
            control_api_url=url,
            ssh_user=os.environ.get("EDGE_SSH_USER", "root"),
            ssh_key=os.environ.get("EDGE_SSH_KEY") or None,
            state_dir=Path(os.environ.get("EDGE_STATE_DIR", "./var/state")),
            log_dir=Path(os.environ.get("EDGE_LOG_DIR", "./var/log")),
            disk_warn_percent=int(os.environ.get("EDGE_DISK_WARN_PERCENT", "80")),
            disk_critical_percent=int(os.environ.get("EDGE_DISK_CRITICAL_PERCENT", "90")),
            disk_min_free_mb=int(os.environ.get("EDGE_DISK_MIN_FREE_MB", "1024")),
        )


def load_nodes(path: str | Path) -> list[dict[str, Any]]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, list):
        raise ValueError("node config must be a JSON array")
    nodes: list[dict[str, Any]] = []
    for item in obj:
        if not isinstance(item, dict) or not item.get("node_id"):
            raise ValueError("each node requires node_id")
        nodes.append(item)
    return nodes
