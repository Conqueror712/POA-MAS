from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_EXCLUDE_MARKERS = {"mock"}


def load_summary(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def is_excluded(run_name: str, markers: set[str]) -> bool:
    lowered = run_name.lower()
    return any(marker in lowered for marker in markers)


def collect_rows(root: Path, prefix: str, exclude_markers: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    bad_json: list[str] = []
    for path in root.rglob("summary.json"):
        run_name = path.parent.name
        if prefix and not run_name.startswith(prefix):
            continue
        if is_excluded(run_name, exclude_markers):
            continue
        summary = load_summary(path)
        if summary is None:
            bad_json.append(str(path))
            continue
        if summary.get("domain") != "game_theory":
            continue
        metrics = summary.get("metrics", {})
        rows.append({
            "run_name": summary.get("run_name", run_name),
            "split": summary.get("task_split"),
            "game_type": summary.get("game_type"),
            "setting": summary.get("setting"),
            "task_id": summary.get("task_id"),
            "num_players": summary.get("num_players"),
            "rounds": summary.get("rounds"),
            "cooperation_rate": float(metrics.get("cooperation_rate", 0.0)),
            "nash_deviation_rate": float(metrics.get("nash_deviation_rate", 0.0)),
            "invalid_action_rate": float(metrics.get("invalid_action_rate", 0.0)),
            "average_payoff": float(metrics.get("average_payoff", 0.0)),
            "social_welfare": float(metrics.get("social_welfare", 0.0)),
            "summary_path": str(path),
        })
    rows.sort(key=lambda row: (str(row["split"]), str(row["game_type"]), str(row["setting"]), str(row["task_id"]), str(row["run_name"])))
    return rows, bad_json


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["split"]), str(row["game_type"]), str(row["setting"]))].append(row)

    output: list[dict[str, Any]] = []
    for (split, game_type, setting), group in sorted(groups.items()):
        output.append({
            "split": split,
            "game_type": game_type,
            "setting": setting,
            "runs": len(group),
            "tasks": ",".join(sorted({str(row["task_id"]) for row in group})),
            "avg_cooperation_rate": sum(row["cooperation_rate"] for row in group) / len(group),
            "avg_nash_deviation_rate": sum(row["nash_deviation_rate"] for row in group) / len(group),
            "avg_invalid_action_rate": sum(row["invalid_action_rate"] for row in group) / len(group),
            "avg_payoff": sum(row["average_payoff"] for row in group) / len(group),
            "total_social_welfare": sum(row["social_welfare"] for row in group),
        })
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], bad_json: list[str]) -> None:
    lines = [
        "# Domain 2 Game-Theory Aggregate",
        "",
        "| split | game | setting | runs | cooperation | nash deviation | invalid action | avg payoff | social welfare |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {split} | {game_type} | {setting} | {runs} | {avg_cooperation_rate:.3f} | "
            "{avg_nash_deviation_rate:.3f} | {avg_invalid_action_rate:.3f} | {avg_payoff:.3f} | "
            "{total_social_welfare:.3f} |".format(**row)
        )
    if bad_json:
        lines.extend(["", "## Bad JSON", ""])
        lines.extend(f"- `{item}`" for item in bad_json)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate Domain 2 game-theory summaries.")
    parser.add_argument("--trajectories-root", default="trajectories")
    parser.add_argument("--prefix", default="game_domain_")
    parser.add_argument("--exclude-markers", nargs="*", default=sorted(DEFAULT_EXCLUDE_MARKERS))
    parser.add_argument("--out-dir", default="results/tables")
    args = parser.parse_args()

    rows, bad_json = collect_rows(Path(args.trajectories_root), args.prefix, set(args.exclude_markers))
    summary = summarize(rows)
    out_dir = Path(args.out_dir)
    write_csv(out_dir / "game_domain_runs.csv", rows)
    write_csv(out_dir / "game_domain_aggregate.csv", summary)
    write_markdown(out_dir / "game_domain_aggregate.md", summary, bad_json)
    print(json.dumps({
        "runs": len(rows),
        "groups": len(summary),
        "bad_json": bad_json,
        "run_csv": str(out_dir / "game_domain_runs.csv"),
        "summary_csv": str(out_dir / "game_domain_aggregate.csv"),
        "summary_md": str(out_dir / "game_domain_aggregate.md"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
