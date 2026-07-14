from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.agents.team import build_team
from src.controller.self_org_controller import SelfOrgController
from src.controller.task_pool import load_tasks
from src.eval.metrics import specialization_index, success_rate, task_overlap_rate
from src.utils.config import load_json
from src.utils.llm_client import build_llm_client
from src.utils.logging import TrajectoryLogger


def load_events_from_logger(logger: TrajectoryLogger) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not logger.events_path.exists():
        return events
    with logger.events_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def run_experiment(
    *,
    config_path: str,
    mode: str,
    limit: int | None = None,
    loaded_assets: dict[str, Any] | None = None,
    run_name: str | None = None,
) -> tuple[dict[str, Any], Path]:
    config = load_json(config_path)
    tasks = load_tasks(config["task_file"], limit=limit)
    llm_client = build_llm_client(config)
    agents = build_team(config["num_agents"], llm_client)
    if run_name is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"{stamp}_{mode}"
    logger = TrajectoryLogger(config["output_root"], run_name)
    controller = SelfOrgController(
        agents,
        logger,
        mode=mode,
        seed=int(config.get("random_seed", 0)),
        loaded_assets=loaded_assets,
    )

    results = [controller.run_code_task(task) for task in tasks]
    events = load_events_from_logger(logger)
    summary = {
        "run_name": run_name,
        "mode": mode,
        "num_tasks": len(tasks),
        "num_agents": config["num_agents"],
        "success_rate": success_rate(results),
        "specialization_index": specialization_index(events),
        "task_overlap_rate": task_overlap_rate(events, config["num_agents"]),
        "results": results,
        "used_assets": bool(loaded_assets),
    }
    logger.write_summary(summary)
    logger.mark_latest(config["output_root"])
    return summary, logger.run_dir

