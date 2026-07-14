from __future__ import annotations

import argparse
import json
import sys

from src.assets.store import AssetStore
from src.runners.common import run_experiment
from src.utils.config import load_json


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run held-out tasks with extracted assets.")
    parser.add_argument("--config", default="configs/experiments.json")
    parser.add_argument("--asset-mode", choices=["full", "role", "organization"], default="full")
    parser.add_argument("--reuse-strategy", choices=["prompt", "routing", "full"], default="full")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--split", choices=["train", "test", "shifted_test"], default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    config = load_json(args.config)
    assets = AssetStore(config["asset_root"]).load_latest(mode=args.asset_mode)
    summary, run_dir = run_experiment(
        config_path=args.config,
        mode="free",
        limit=args.limit,
        task_offset=args.offset,
        task_split=args.split,
        loaded_assets=assets,
        reuse_strategy=args.reuse_strategy,
        run_name=args.run_name or f"reuse_{args.asset_mode}",
        seed=args.seed,
    )
    print(json.dumps({"run_dir": str(run_dir), "assets_loaded": assets, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

