from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_summary(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def setting_name(summary: dict[str, Any]) -> str:
    strategy = summary.get("reuse_strategy")
    if strategy and strategy != "none":
        return f"reuse_{strategy}"
    return str(summary.get("mode", "unknown"))


def is_excluded_run(run_name: str, exclude_markers: set[str]) -> bool:
    lowered = run_name.lower()
    return any(marker in lowered for marker in exclude_markers)


def collect_rows(trajectories_root: Path, prefix: str, exclude_markers: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    bad_json: list[str] = []
    for summary_path in trajectories_root.rglob("summary.json"):
        run_name = summary_path.parent.name
        if prefix and not run_name.startswith(prefix):
            continue
        if is_excluded_run(run_name, exclude_markers):
            continue
        summary = load_summary(summary_path)
        if summary is None:
            bad_json.append(str(summary_path))
            continue
        if summary.get("task_split") not in {"test", "shifted_test"}:
            continue
        rows.append(
            {
                "run_name": summary.get("run_name", run_name),
                "split": summary.get("task_split"),
                "setting": setting_name(summary),
                "mode": summary.get("mode"),
                "reuse_strategy": summary.get("reuse_strategy"),
                "seed": summary.get("seed"),
                "num_tasks": summary.get("num_tasks"),
                "success_rate": float(summary.get("success_rate", 0.0)),
                "successes": sum(1 for item in summary.get("results", []) if item.get("success")),
                "specialization_index": float(summary.get("specialization_index", 0.0)),
                "task_overlap_rate": float(summary.get("task_overlap_rate", 0.0)),
                "asset_routing_rate": float(summary.get("asset_routing_rate", 0.0)),
                "prompt_tokens": summary.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": summary.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": summary.get("usage", {}).get("total_tokens", 0),
                "wall_time_sec": float(summary.get("wall_time_sec", 0.0)),
                "summary_path": str(summary_path),
            }
        )
    return rows, bad_json


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["split"]), str(row["setting"]))].append(row)

    output = []
    for (split, setting), group in sorted(groups.items()):
        success_values = [row["success_rate"] for row in group]
        token_values = [float(row["total_tokens"]) for row in group]
        time_values = [float(row["wall_time_sec"]) for row in group]
        output.append(
            {
                "split": split,
                "setting": setting,
                "runs": len(group),
                "seeds": ",".join(str(row["seed"]) for row in sorted(group, key=lambda item: str(item["seed"]))),
                "avg_success": statistics.mean(success_values),
                "std_success": statistics.pstdev(success_values) if len(success_values) > 1 else 0.0,
                "min_success": min(success_values),
                "max_success": max(success_values),
                "avg_tokens": statistics.mean(token_values) if token_values else 0.0,
                "avg_wall_time_sec": statistics.mean(time_values) if time_values else 0.0,
            }
        )
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


def write_markdown(path: Path, summary_rows: list[dict[str, Any]], bad_json: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# APPS Protocol Results",
        "",
        "| split | setting | runs | seeds | avg success | std | min | max | avg tokens | avg seconds |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| {split} | {setting} | {runs} | {seeds} | {avg_success:.3f} | {std_success:.3f} | "
            "{min_success:.3f} | {max_success:.3f} | {avg_tokens:.0f} | {avg_wall_time_sec:.1f} |".format(**row)
        )
    if bad_json:
        lines.extend(["", "## Bad JSON", ""])
        lines.extend(f"- `{item}`" for item in bad_json)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate APPS protocol summaries.")
    parser.add_argument("--trajectories-root", default="trajectories")
    parser.add_argument("--prefix", default="apps_protocol_")
    parser.add_argument("--exclude-markers", nargs="*", default=["smoke", "mock", "preflight"])
    parser.add_argument("--out-dir", default="results/tables")
    args = parser.parse_args()

    rows, bad_json = collect_rows(Path(args.trajectories_root), args.prefix, set(args.exclude_markers))
    summary_rows = summarize(rows)
    out_dir = Path(args.out_dir)
    write_csv(out_dir / "apps_protocol_runs.csv", rows)
    write_csv(out_dir / "apps_protocol_summary.csv", summary_rows)
    write_markdown(out_dir / "apps_protocol_summary.md", summary_rows, bad_json)

    print(json.dumps({
        "runs": len(rows),
        "groups": len(summary_rows),
        "bad_json": bad_json,
        "run_csv": str(out_dir / "apps_protocol_runs.csv"),
        "summary_csv": str(out_dir / "apps_protocol_summary.csv"),
        "summary_md": str(out_dir / "apps_protocol_summary.md"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
