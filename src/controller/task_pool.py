from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_tasks(
    path: str | Path,
    limit: int | None = None,
    offset: int = 0,
    split: str | None = None,
) -> list[dict[str, Any]]:
    if offset < 0:
        raise ValueError("Task offset must be non-negative.")
    with Path(path).open("r", encoding="utf-8") as f:
        tasks = json.load(f)
    if split is not None:
        tasks = [task for task in tasks if task.get("split") == split]
    tasks = tasks[offset:]
    if limit is not None:
        return tasks[:limit]
    return tasks


def code_repair_subtasks() -> list[str]:
    return ["localize", "patch", "review"]

