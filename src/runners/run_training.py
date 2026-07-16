from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from src.assets.store import AssetStore
from src.runners.common import run_experiment
from src.utils.config import load_json


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run an experiment with per-task terminal progress.")
    parser.add_argument("--config", default="configs/experiments_apps.json")
    parser.add_argument("--mode", choices=["free", "manual", "random"], default="free")
    parser.add_argument("--split", choices=["train", "test", "shifted_test"], required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--asset-mode", choices=["full", "role", "organization"], default="full")
    parser.add_argument("--reuse-strategy", choices=["prompt", "routing", "full"], default=None)
    args = parser.parse_args()

    successes = 0
    loaded_assets = None
    if args.reuse_strategy:
        config = load_json(args.config)
        loaded_assets = AssetStore(config["asset_root"]).load_latest(mode=args.asset_mode)

    def report(index: int, total: int, result: dict[str, Any], elapsed_sec: float) -> None:
        nonlocal successes
        successes += int(result["success"])
        print(json.dumps({
            "event": "progress",
            "completed": index,
            "total": total,
            "successes": successes,
            "task_id": result["task_id"],
            "success": result["success"],
            "elapsed_sec": round(elapsed_sec, 1),
        }, ensure_ascii=False), flush=True)

    summary, run_dir = run_experiment(
        config_path=args.config,
        mode=args.mode,
        limit=args.limit,
        task_offset=args.offset,
        task_split=args.split,
        run_name=args.run_name,
        seed=args.seed,
        loaded_assets=loaded_assets,
        reuse_strategy=args.reuse_strategy or "none",
        on_task_completed=report,
    )
    print(json.dumps({
        "event": "completed",
        "run_dir": str(run_dir),
        "success_rate": summary["success_rate"],
        "successes": sum(result["success"] for result in summary["results"]),
        "num_tasks": summary["num_tasks"],
        "tokens": summary["usage"]["total_tokens"],
        "wall_time_sec": summary["wall_time_sec"],
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
