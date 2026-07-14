from __future__ import annotations

import argparse
import json

from src.runners.common import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run phase-1 self-organization experiment.")
    parser.add_argument("--config", default="configs/experiments.json")
    parser.add_argument("--mode", choices=["free", "manual", "random"], default="free")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    summary, run_dir = run_experiment(config_path=args.config, mode=args.mode, limit=args.limit)
    print(json.dumps({"run_dir": str(run_dir), "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

