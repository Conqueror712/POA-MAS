from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import Any

from src.assets.store import AssetStore
from src.runners.common import run_experiment
from src.utils.config import load_json


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run all APPS held-out conditions with terminal progress.")
    parser.add_argument("--config", default="configs/experiments_apps.json")
    parser.add_argument("--seed", type=int, default=712)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--splits", nargs="+", choices=["test", "shifted_test"], default=["test", "shifted_test"])
    parser.add_argument("--run-prefix", default=None)
    args = parser.parse_args()

    config = load_json(args.config)
    assets = AssetStore(config["asset_root"]).load_latest(mode="full")
    if not assets:
        raise RuntimeError("No extracted assets found. Run the train source and asset extraction first.")
    prefix = args.run_prefix or f"apps_protocol_{datetime.now():%Y%m%d_%H%M%S}_s{args.seed}"
    conditions = [(mode, "none") for mode in ("free", "manual", "random")]
    conditions.extend(("free", strategy) for strategy in ("prompt", "routing", "full"))

    completed_runs = []
    for split in args.splits:
        for mode, strategy in conditions:
            label = mode if strategy == "none" else f"reuse_{strategy}"
            successes = 0

            def report(index: int, total: int, result: dict[str, Any], elapsed_sec: float) -> None:
                nonlocal successes
                successes += int(result["success"])
                print(json.dumps({
                    "event": "progress",
                    "split": split,
                    "condition": label,
                    "completed": index,
                    "total": total,
                    "successes": successes,
                    "task_id": result["task_id"],
                    "success": result["success"],
                    "elapsed_sec": round(elapsed_sec, 1),
                }, ensure_ascii=False), flush=True)

            summary, run_dir = run_experiment(
                config_path=args.config,
                mode=mode,
                limit=args.limit,
                task_split=split,
                loaded_assets=assets if strategy != "none" else None,
                reuse_strategy=strategy,
                run_name=f"{prefix}_{split}_{label}",
                seed=args.seed,
                on_task_completed=report,
            )
            completed_runs.append({
                "split": split,
                "condition": label,
                "run_dir": str(run_dir),
                "success_rate": summary["success_rate"],
                "tokens": summary["usage"]["total_tokens"],
            })
            print(json.dumps({"event": "condition_completed", **completed_runs[-1]}, ensure_ascii=False), flush=True)

    print(json.dumps({"event": "protocol_completed", "runs": completed_runs}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
