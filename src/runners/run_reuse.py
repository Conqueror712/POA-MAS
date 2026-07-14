from __future__ import annotations

import argparse
import json

from src.assets.store import AssetStore
from src.runners.common import run_experiment
from src.utils.config import load_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Run held-out tasks with extracted assets.")
    parser.add_argument("--config", default="configs/experiments.json")
    parser.add_argument("--asset-mode", choices=["full", "role", "organization"], default="full")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    config = load_json(args.config)
    assets = AssetStore(config["asset_root"]).load_latest(mode=args.asset_mode)
    summary, run_dir = run_experiment(
        config_path=args.config,
        mode="free",
        limit=args.limit,
        loaded_assets=assets,
        run_name=f"reuse_{args.asset_mode}",
    )
    print(json.dumps({"run_dir": str(run_dir), "assets_loaded": assets, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

