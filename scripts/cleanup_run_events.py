#!/usr/bin/env python3
"""Strip pre-cutoff events from a trajectory directory, then recompute summary metrics.

Motivation
----------
`TrajectoryLogger.log_event` opens the events file in append mode, so if the
same `run_name` gets executed twice (e.g. after fixing a config bug), old events
from the aborted first attempt end up mixed with the fresh events.

`summary.json` on the other hand is rewritten with `"w"`, so `success_rate`
(which is derived from `results`) is always correct. But metrics that are
recomputed from `events.jsonl` (`usage`, `specialization_index`,
`task_overlap_rate`, `asset_routing_rate`) inherit the contamination.

Usage
-----
    python3 scripts/cleanup_run_events.py <run_dir> <cutoff_utc_iso>

Example (drops events strictly before 2026-07-22 09:00 UTC):

    python3 scripts/cleanup_run_events.py \
        trajectories/apps_protocol_qwen9b_20260722_s712_test_free \
        2026-07-22T09:00:00+00:00

Behavior
--------
* Backs up the original events file to `<run_dir>/events.jsonl.pre_cleanup`
  (only if the backup does not yet exist).
* Rewrites `events.jsonl` with only events whose ISO timestamp is
  lexicographically >= the cutoff.
* Reloads the events, recomputes the four events-derived metrics, and rewrites
  `summary.json` with a `post_hoc_cleanup` provenance stanza.
* Verifies that `success_rate` from `summary["results"]` is unchanged.

The script is safe to re-run: after cleanup, no further events fall below the
cutoff, so subsequent invocations are no-ops (dropped=0).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# Make the src package importable when this script is run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.metrics import (  # noqa: E402
    asset_routing_rate,
    specialization_index,
    success_rate,
    task_overlap_rate,
    usage_metrics,
)


def cleanup(run_dir: Path, cutoff_utc: str) -> None:
    events_path = run_dir / "events.jsonl"
    summary_path = run_dir / "summary.json"
    if not events_path.exists() or not summary_path.exists():
        raise SystemExit(f"missing events.jsonl or summary.json in {run_dir}")

    backup = events_path.with_suffix(".jsonl.pre_cleanup")
    if not backup.exists():
        shutil.copy2(events_path, backup)

    with events_path.open() as f:
        events = [json.loads(line) for line in f if line.strip()]
    kept = [e for e in events if e.get("timestamp", "") >= cutoff_utc]
    dropped = len(events) - len(kept)

    with events_path.open("w") as f:
        for event in kept:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    summary = json.load(summary_path.open())
    summary["specialization_index"] = specialization_index(kept)
    summary["task_overlap_rate"] = task_overlap_rate(kept, summary.get("num_agents", 4))
    summary["asset_routing_rate"] = asset_routing_rate(kept)
    summary["usage"] = usage_metrics(kept)

    recomputed = success_rate(summary["results"])
    assert abs(summary["success_rate"] - recomputed) < 1e-9, (
        f"success_rate mismatch after cleanup: stored={summary['success_rate']} recomputed={recomputed}"
    )

    provenance = summary.setdefault("post_hoc_cleanup", {})
    provenance.update(
        {
            "reason": "Removed pre-cutoff events from an aborted earlier run of the same run_name.",
            "events_dropped": dropped,
            "cutoff_utc": cutoff_utc,
        }
    )

    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"{run_dir.name}: kept {len(kept)}/{len(events)} events (dropped {dropped}); success_rate={summary['success_rate']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("cutoff_utc", help="ISO-8601 UTC timestamp; keep events with timestamp >= cutoff")
    args = parser.parse_args()
    cleanup(args.run_dir, args.cutoff_utc)


if __name__ == "__main__":
    main()
