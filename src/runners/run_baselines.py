from __future__ import annotations

import argparse
import json

from src.runners.common import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run phase-1 baseline modes.")
    parser.add_argument("--config", default="configs/experiments.json")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    summaries = {}
    for mode in ["free", "manual", "random"]:
        summary, run_dir = run_experiment(
            config_path=args.config,
            mode=mode,
            limit=args.limit,
            run_name=f"baseline_{mode}",
        )
        summaries[mode] = {"run_dir": str(run_dir), "summary": summary}
    print(json.dumps(summaries, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

