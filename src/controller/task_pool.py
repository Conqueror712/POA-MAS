from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_tasks(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as f:
        tasks = json.load(f)
    if limit is not None:
        return tasks[:limit]
    return tasks


def code_repair_subtasks() -> list[str]:
    return ["localize", "patch", "review"]

