from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.agents.team import build_team
from src.controller.self_org_controller import SelfOrgController
from src.controller.task_pool import load_tasks
from src.eval.metrics import asset_routing_rate, specialization_index, success_rate, task_overlap_rate, usage_metrics
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
    task_offset: int = 0,
    task_split: str | None = None,
    loaded_assets: dict[str, Any] | None = None,
    reuse_strategy: str = "none",
    run_name: str | None = None,
    seed: int | None = None,
    on_task_completed: Callable[[int, int, dict[str, Any], float], None] | None = None,
) -> tuple[dict[str, Any], Path]:
    config = load_json(config_path)
    tasks = load_tasks(
        config["task_file"],
        limit=limit,
        offset=task_offset,
        split=task_split,
    )
    llm_client = build_llm_client(config)
    agents = build_team(config["num_agents"], llm_client)
    if run_name is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"{stamp}_{mode}"
    logger = TrajectoryLogger(config["output_root"], run_name)
    experiment_seed = int(config.get("random_seed", 0)) if seed is None else seed
    controller = SelfOrgController(
        agents,
        logger,
        mode=mode,
        seed=experiment_seed,
        loaded_assets=loaded_assets,
        reuse_strategy=reuse_strategy,
        evaluation_timeout_sec=float(config.get("evaluation_timeout_sec", 5.0)),
    )

    started_at = time.perf_counter()
    results = []
    for index, task in enumerate(tasks, start=1):
        result = controller.run_code_task(task)
        results.append(result)
        if on_task_completed:
            on_task_completed(index, len(tasks), result, time.perf_counter() - started_at)
    wall_time_sec = round(time.perf_counter() - started_at, 4)
    events = load_events_from_logger(logger)
    summary = {
        "run_name": run_name,
        "mode": mode,
        "num_tasks": len(tasks),
        "task_offset": task_offset,
        "task_split": task_split,
        "task_ids": [task["task_id"] for task in tasks],
        "num_agents": config["num_agents"],
        "seed": experiment_seed,
        "success_rate": success_rate(results),
        "specialization_index": specialization_index(events),
        "task_overlap_rate": task_overlap_rate(events, config["num_agents"]),
        "results": results,
        "used_assets": bool(loaded_assets) and reuse_strategy != "none",
        "reuse_strategy": reuse_strategy,
        "asset_routing_rate": asset_routing_rate(events),
        "usage": usage_metrics(events),
        "wall_time_sec": wall_time_sec,
    }
    logger.write_summary(summary)
    logger.mark_latest(config["output_root"])
    return summary, logger.run_dir

