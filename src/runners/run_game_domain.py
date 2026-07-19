from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.agents.team import build_team
from src.controller.task_pool import load_tasks
from src.games.evaluator import parse_action, score_round, summarize_game_results
from src.utils.config import ensure_dir, load_json
from src.utils.llm_client import build_llm_client
from src.utils.logging import TrajectoryLogger


SETTINGS = ("no_persona", "persona", "reuse_assets")
PERSONA_POOL = [
    "cooperative norm follower",
    "self-interested payoff maximizer",
    "reciprocal tit-for-tat player",
    "conditional cooperator",
    "fairness-oriented contributor",
]
GAME_ASSETS = {
    "strategy_assets": [
        "Start cooperatively when repeated interaction is expected.",
        "Use reciprocity: maintain cooperation after cooperative behavior and punish persistent defection.",
        "In public-goods games, preserve social welfare by contributing unless the group repeatedly defects.",
        "Return exactly one legal action token so the evaluator can score the round.",
    ]
}


def compact_history(history: list[dict[str, Any]], limit: int = 3) -> str:
    if not history:
        return "No previous rounds."
    lines = []
    for item in history[-limit:]:
        actions = ", ".join(f"{player}:{action}" for player, action in sorted(item["actions"].items()))
        lines.append(f"r{item['round']}[{actions}]")
    return "; ".join(lines)


def assigned_persona(setting: str, player_index: int) -> str:
    if setting == "no_persona":
        return "unspecified"
    return PERSONA_POOL[player_index % len(PERSONA_POOL)]


def run_task(task: dict[str, Any], setting: str, config: dict[str, Any], run_name: str) -> dict[str, Any]:
    llm_client = build_llm_client(config)
    agents = build_team(int(task["num_players"]), llm_client)
    logger = TrajectoryLogger(config["output_root"], run_name)
    history: list[dict[str, Any]] = []

    for round_index in range(1, int(task["rounds"]) + 1):
        actions: dict[str, str] = {}
        action_valid: dict[str, bool] = {}
        raw_outputs: dict[str, str] = {}
        for player_index, agent in enumerate(agents):
            context = {
                "setting": setting,
                "persona": assigned_persona(setting, player_index),
                "history": history,
                "history_text": compact_history(history),
                "game_assets": GAME_ASSETS if setting == "reuse_assets" else {},
            }
            response = agent.run_subtask("decide", task, context)
            action, is_valid = parse_action(str(task["game_type"]), response.text)
            if not is_valid:
                retry_context = dict(context)
                retry_context["force_action_retry"] = True
                response = agent.run_subtask("decide", task, retry_context)
                action, is_valid = parse_action(str(task["game_type"]), response.text)
            actions[agent.agent_id] = action
            action_valid[agent.agent_id] = is_valid
            raw_outputs[agent.agent_id] = response.text
            logger.log_event({
                "event_type": "game_action",
                "task_id": task["task_id"],
                "round": round_index,
                "agent_id": agent.agent_id,
                "setting": setting,
                "persona": context["persona"],
                "action": action,
                "action_valid": is_valid,
                "raw_output": response.text,
                "used_strategy_assets": bool(context["game_assets"]),
                "llm_metadata": response.metadata,
            })

        scores = score_round(task, actions)
        round_result = {
            "round": round_index,
            "actions": actions,
            "action_valid": action_valid,
            "raw_outputs": raw_outputs,
            "scores": scores,
        }
        history.append(round_result)
        logger.log_event({
            "event_type": "game_round_finished",
            "task_id": task["task_id"],
            "round": round_index,
            "setting": setting,
            "actions": actions,
            "scores": scores,
        })

    result = {
        "task_id": task["task_id"],
        "split": task["split"],
        "game_type": task["game_type"],
        "setting": setting,
        "rounds": history,
        "metrics": summarize_game_results([{"rounds": history}]),
    }
    summary = {
        "run_name": run_name,
        "domain": "game_theory",
        "setting": setting,
        "task_id": task["task_id"],
        "task_split": task["split"],
        "game_type": task["game_type"],
        "num_players": task["num_players"],
        "rounds": task["rounds"],
        "result": result,
        "metrics": result["metrics"],
    }
    logger.write_summary(summary)
    logger.mark_latest(config["output_root"])
    return result


def aggregate(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for result in results:
        key = (result["split"], result["game_type"], result["setting"])
        groups.setdefault(key, []).append(result)

    rows = []
    for (split, game_type, setting), group in sorted(groups.items()):
        rows.append({
            "split": split,
            "game_type": game_type,
            "setting": setting,
            "tasks": len(group),
            "cooperation_rate": sum(item["metrics"]["cooperation_rate"] for item in group) / len(group),
            "nash_deviation_rate": sum(item["metrics"]["nash_deviation_rate"] for item in group) / len(group),
            "invalid_action_rate": sum(item["metrics"]["invalid_action_rate"] for item in group) / len(group),
            "average_payoff": sum(item["metrics"]["average_payoff"] for item in group) / len(group),
            "social_welfare": sum(item["metrics"]["social_welfare"] for item in group),
        })
    return rows


def write_summary_tables(rows: list[dict[str, Any]], out_dir: Path) -> None:
    ensure_dir(out_dir)
    csv_path = out_dir / "game_domain_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

    lines = [
        "# Domain 2 Game-Theory Summary",
        "",
        "| split | game | setting | tasks | cooperation | nash deviation | invalid action | avg payoff | social welfare |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {split} | {game_type} | {setting} | {tasks} | {cooperation_rate:.3f} | "
            "{nash_deviation_rate:.3f} | {invalid_action_rate:.3f} | {average_payoff:.3f} | {social_welfare:.3f} |".format(**row)
        )
    (out_dir / "game_domain_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run minimal game-theory Domain 2 experiments.")
    parser.add_argument("--config", default="configs/experiments_game_mock.json")
    parser.add_argument("--splits", nargs="+", default=["test", "shifted_test"], choices=["train", "test", "shifted_test"])
    parser.add_argument("--settings", nargs="+", default=list(SETTINGS), choices=list(SETTINGS))
    parser.add_argument("--run-prefix", default=None)
    args = parser.parse_args()

    config = load_json(args.config)
    tasks = [
        task for task in load_tasks(config["task_file"])
        if task.get("split") in set(args.splits)
    ]
    prefix = args.run_prefix or f"game_domain_{datetime.now():%Y%m%d_%H%M%S}"
    results = []
    for task in tasks:
        for setting in args.settings:
            run_name = f"{prefix}_{task['task_id']}_{setting}"
            result = run_task(task, setting, config, run_name)
            results.append(result)
            print(json.dumps({
                "event": "game_task_completed",
                "task_id": task["task_id"],
                "setting": setting,
                "metrics": result["metrics"],
            }, ensure_ascii=False), flush=True)

    rows = aggregate(results)
    write_summary_tables(rows, Path("results/tables"))
    print(json.dumps({
        "event": "game_domain_completed",
        "tasks": len(tasks),
        "runs": len(results),
        "summary": "results/tables/game_domain_summary.md",
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
