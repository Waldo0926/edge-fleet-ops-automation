from __future__ import annotations

from dataclasses import dataclass
import subprocess
from typing import Iterable


@dataclass
class SSHResult:
    host: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class SSHRunner:
    """Key-based SSH runner with IPv6 support.

    The original private scripts used a shared plaintext password. The
    portfolio version intentionally removes password-based SSH and defaults to
    host-key verification via the operator's normal OpenSSH configuration.
    """

    def __init__(self, user: str = "root", key_file: str | None = None, timeout: int = 20):
        self.user = user
        self.key_file = key_file
        self.timeout = timeout

    def command(self, host: str, remote_command: str) -> list[str]:
        cmd = ["ssh", "-6", "-o", f"ConnectTimeout={self.timeout}"]
        if self.key_file:
            cmd += ["-i", self.key_file]
        cmd += [f"{self.user}@{host}", remote_command]
        return cmd

    def run(self, host: str, remote_command: str, *, timeout: int | None = None) -> SSHResult:
        cp = subprocess.run(
            self.command(host, remote_command),
            text=True,
            capture_output=True,
            timeout=timeout or self.timeout + 10,
        )
        return SSHResult(host, cp.returncode, cp.stdout, cp.stderr)

    def first_reachable(self, hosts: Iterable[str], remote_command: str = "date -Is") -> SSHResult:
        errors: list[str] = []
        for host in hosts:
            try:
                result = self.run(host, remote_command)
            except (subprocess.TimeoutExpired, OSError) as exc:
                errors.append(f"{host}: {exc}")
                continue
            if result.ok:
                return result
            errors.append(f"{host}: rc={result.returncode}")
        raise RuntimeError("no reachable host; " + "; ".join(errors))
