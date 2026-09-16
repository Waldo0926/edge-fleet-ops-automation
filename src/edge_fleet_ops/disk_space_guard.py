from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex

from .ssh import SSHRunner


@dataclass
class CleanupPolicy:
    trigger_percent: int = 85
    min_free_mb: int = 1024
    log_roots: tuple[str, ...] = ("/var/log", "/opt/edge-agent/logs")
    max_age_days: int = 2


def safe_cleanup_command(policy: CleanupPolicy, *, apply: bool = False) -> str:
    """Build a constrained cleanup command.

    The public version is dry-run by default and only targets explicitly
    configured log roots. It does not format disks, remove containers, or
    recurse through arbitrary cache paths.
    """
    roots = " ".join(shlex.quote(p) for p in policy.log_roots)
    action = "-delete" if apply else "-print"
    return f'''sh -s <<'SH'\nset -eu\nused=$(df -P / | awk 'NR==2{{gsub("%","",$5); print $5}}')\nfree=$(df -Pm / | awk 'NR==2{{print $4}}')\necho "BEFORE used=${{used}} free_mb=${{free}}"\nif [ "$used" -lt {policy.trigger_percent} ] && [ "$free" -ge {policy.min_free_mb} ]; then\n  echo "NO_ACTION"\n  exit 0\nfi\nfor root in {roots}; do\n  [ -d "$root" ] || continue\n  find "$root" -type f \\( -name '*.log.*' -o -name '*.gz' -o -name '*.old' \\) -mtime +{policy.max_age_days} {action}\ndone\necho "AFTER used=$(df -P / | awk 'NR==2{{print $5}}') free_mb=$(df -Pm / | awk 'NR==2{{print $4}}')"\nSH'''


def run_guard(host: str, runner: SSHRunner, policy: CleanupPolicy, *, apply: bool = False):
    return runner.run(host, safe_cleanup_command(policy, apply=apply), timeout=120)
