from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


class AlertOutbox:
    """Persistent JSONL alert queue with atomic drain semantics."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def enqueue(self, message: str, **metadata: object) -> None:
        record = {"message": message, **metadata}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def drain(self, limit: int = 10) -> list[str]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return []
        sending = self.path.with_suffix(self.path.suffix + ".sending")
        try:
            self.path.replace(sending)
        except FileNotFoundError:
            return []
        messages: list[str] = []
        leftovers: list[str] = []
        for line in sending.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                msg = str(obj.get("message") or "")
            except Exception:
                msg = line
            if msg and len(messages) < limit:
                messages.append(msg)
            elif msg:
                leftovers.append(line)
        sending.unlink(missing_ok=True)
        if leftovers:
            self.path.write_text("\n".join(leftovers) + "\n", encoding="utf-8")
        return messages
