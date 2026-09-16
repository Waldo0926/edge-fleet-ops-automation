from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class NodeRecord:
    node_id: str
    label: str = ""
    public_ipv4: str | None = None
    ipv6_candidates: tuple[str, ...] = ()
    raw: dict[str, Any] | None = None


def _unique(values: list[str]) -> tuple[str, ...]:
    out: list[str] = []
    for value in values:
        if value and value not in out:
            out.append(value)
    return tuple(out)


class FleetControlClient:
    """Small adapter around a fleet control-plane JSON endpoint.

    The production endpoint/shape used by the original tooling has been
    sanitized. This adapter intentionally accepts a loose schema so the
    portfolio project can be tested without proprietary infrastructure.
    """

    def __init__(self, url: str, timeout: int = 20):
        self.url = url
        self.timeout = timeout

    def fetch(self) -> dict[str, NodeRecord]:
        with urllib.request.urlopen(self.url, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError("control API must return a list")
        records: dict[str, NodeRecord] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            node_id = str(item.get("node_id") or item.get("box_id") or "").strip()
            if not node_id:
                continue
            candidates: list[str] = []
            for iface in item.get("net_ifaces") or item.get("interfaces") or []:
                if not isinstance(iface, dict):
                    continue
                if iface.get("ipv6"):
                    candidates.append(str(iface["ipv6"]))
                candidates.extend(str(v) for v in (iface.get("ipv6_list") or []) if v)
            records[node_id] = NodeRecord(
                node_id=node_id,
                label=str(item.get("label") or item.get("remark") or ""),
                public_ipv4=item.get("public_ipv4"),
                ipv6_candidates=_unique(candidates),
                raw=item,
            )
        return records
