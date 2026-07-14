from __future__ import annotations

import argparse
import json
import sys

from src.runners.common import run_experiment


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run phase-1 self-organization experiment.")
    parser.add_argument("--config", default="configs/experiments.json")
    parser.add_argument("--mode", choices=["free", "manual", "random"], default="free")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--split", choices=["train", "test", "shifted_test"], default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    summary, run_dir = run_experiment(
        config_path=args.config,
        mode=args.mode,
        limit=args.limit,
        task_offset=args.offset,
        task_split=args.split,
        run_name=args.run_name,
        seed=args.seed,
    )
    print(json.dumps({"run_dir": str(run_dir), "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

