from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.utils.config import ensure_dir


class TrajectoryLogger:
    def __init__(self, output_root: str | Path, run_name: str):
        self.run_dir = ensure_dir(Path(output_root) / run_name)
        self.events_path = self.run_dir / "events.jsonl"
        self.summary_path = self.run_dir / "summary.json"

    def log_event(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def write_summary(self, summary: dict[str, Any]) -> None:
        with self.summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def mark_latest(self, output_root: str | Path) -> None:
        latest = Path(output_root) / "latest"
        if latest.exists() or latest.is_symlink():
            if latest.is_dir() and not latest.is_symlink():
                shutil.rmtree(latest)
            else:
                latest.unlink()
        shutil.copytree(self.run_dir, latest)

