from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.assets.game_extractor import extract_game_strategy_assets, load_game_summaries
from src.assets.store import AssetStore
from src.utils.config import load_json


def resolve_run_dirs(root: Path, prefix: str) -> list[Path]:
    candidates = [
        path for path in root.iterdir()
        if path.is_dir() and path.name.startswith(prefix) and (path / "summary.json").exists()
    ]
    return sorted(candidates)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract game-theory strategy assets from train trajectories.")
    parser.add_argument("--config", default="configs/experiments_game_mock.json")
    parser.add_argument("--run-prefix", required=True)
    parser.add_argument("--trajectories-root", default=None)
    parser.add_argument("--filename", default="latest_strategy_assets.json")
    args = parser.parse_args()

    config = load_json(args.config)
    trajectories_root = Path(args.trajectories_root or config.get("output_root", "trajectories"))
    run_dirs = resolve_run_dirs(trajectories_root, args.run_prefix)
    if not run_dirs:
        raise RuntimeError(f"No train game trajectories found for prefix: {args.run_prefix}")

    summaries = load_game_summaries(run_dirs)
    assets = extract_game_strategy_assets(summaries)
    asset_path = AssetStore(config["asset_root"]).save_game_assets(assets, args.filename)

    print(json.dumps({
        "event": "game_assets_extracted",
        "source_runs": len(summaries),
        "num_assets": len(assets),
        "asset_path": str(asset_path),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
