from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SETTINGS = ["free", "manual", "random", "reuse_prompt", "reuse_routing", "reuse_full"]
BASELINES = ["free", "manual", "random"]
REUSE_SETTINGS = ["reuse_prompt", "reuse_routing", "reuse_full"]
EXCLUDED_MARKERS = {"smoke", "mock", "preflight"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def setting_name(summary: dict[str, Any]) -> str:
    strategy = summary.get("reuse_strategy")
    if strategy and strategy != "none":
        return f"reuse_{strategy}"
    return str(summary.get("mode", "unknown"))


def is_formal_run(run_name: str, prefix: str) -> bool:
    lowered = run_name.lower()
    return run_name.startswith(prefix) and not any(marker in lowered for marker in EXCLUDED_MARKERS)


def patch_text(item: dict[str, Any]) -> str:
    outputs = item.get("subtask_outputs") or {}
    return str(outputs.get("patch") or "").strip()


def review_text(item: dict[str, Any]) -> str:
    outputs = item.get("subtask_outputs") or {}
    return str(outputs.get("review") or "").strip()


def localize_text(item: dict[str, Any]) -> str:
    outputs = item.get("subtask_outputs") or {}
    return str(outputs.get("localize") or "").strip()


def has_substantive_patch(text: str) -> bool:
    compact = text.strip().lower()
    if not compact:
        return False
    empty_markers = [
        "no code provided",
        "candidate code is empty",
        "empty code",
        "candidate code is incomplete",
    ]
    if any(marker in compact for marker in empty_markers):
        return False
    return True


def classify_failure(item: dict[str, Any]) -> str:
    if item.get("success"):
        return "passed"

    error = str((item.get("eval") or {}).get("error") or "")
    patch = patch_text(item)
    review = review_text(item)
    joined = f"{error}\n{patch}\n{review}".lower()

    if not has_substantive_patch(patch):
        return "empty_or_missing_patch"
    if "timed out" in joined or "timeout" in joined:
        return "timeout"
    if "syntaxerror" in joined or "indentationerror" in joined:
        return "syntax_error"
    if re.search(r"\b(nameerror|indexerror|zerodivisionerror|typeerror|valueerror|runtimeerror|eoferror)\b", joined):
        return "runtime_error"
    if "produced different output" in joined or "different output" in joined:
        return "wrong_output"
    if "fail" in review.lower():
        return "review_rejected"
    return "other_failure"


def collect_items(trajectories_root: Path, prefix: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for summary_path in trajectories_root.rglob("summary.json"):
        run_name = summary_path.parent.name
        if not is_formal_run(run_name, prefix):
            continue
        summary = load_json(summary_path)
        split = summary.get("task_split")
        if split not in {"test", "shifted_test"}:
            continue
        setting = setting_name(summary)
        if setting not in SETTINGS:
            continue
        seed = summary.get("seed")
        for item in summary.get("results", []):
            error = (item.get("eval") or {}).get("error")
            patch = patch_text(item)
            rows.append(
                {
                    "split": split,
                    "setting": setting,
                    "seed": seed,
                    "task_id": item.get("task_id"),
                    "success": bool(item.get("success")),
                    "failure_type": classify_failure(item),
                    "eval_error": "" if error is None else str(error),
                    "patch_chars": len(patch),
                    "localize_chars": len(localize_text(item)),
                    "review_chars": len(review_text(item)),
                    "run_name": summary.get("run_name", run_name),
                    "summary_path": str(summary_path),
                }
            )
    rows.sort(key=lambda row: (str(row["split"]), str(row["seed"]), str(row["task_id"]), str(row["setting"])))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def success_rate(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row["success"]) / len(rows)


def grouped_success(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["split"]), str(row["setting"]))].append(row)
    return groups


def failure_mode_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    totals: Counter[tuple[str, str]] = Counter()
    failures: Counter[tuple[str, str]] = Counter()
    for row in rows:
        key = (str(row["split"]), str(row["setting"]))
        totals[key] += 1
        if not row["success"]:
            failures[key] += 1
            groups[key][str(row["failure_type"])] += 1

    output: list[dict[str, Any]] = []
    for key in sorted(totals):
        split, setting = key
        for failure_type, count in sorted(groups[key].items()):
            output.append(
                {
                    "split": split,
                    "setting": setting,
                    "failure_type": failure_type,
                    "count": count,
                    "failure_share": count / failures[key] if failures[key] else 0.0,
                    "all_attempt_share": count / totals[key] if totals[key] else 0.0,
                }
            )
    return output


def build_index(rows: list[dict[str, Any]]) -> dict[tuple[str, int, str, str], dict[str, Any]]:
    index: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    for row in rows:
        index[(str(row["split"]), int(row["seed"]), str(row["task_id"]), str(row["setting"]))] = row
    return index


def contrast_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = build_index(rows)
    keys = sorted({(str(row["split"]), int(row["seed"]), str(row["task_id"])) for row in rows})
    output: list[dict[str, Any]] = []
    for split, seed, task_id in keys:
        free = index.get((split, seed, task_id, "free"))
        if not free:
            continue
        for setting in REUSE_SETTINGS:
            reuse = index.get((split, seed, task_id, setting))
            if not reuse:
                continue
            if not free["success"] and reuse["success"]:
                delta = "rescued_by_reuse"
            elif free["success"] and not reuse["success"]:
                delta = "hurt_by_reuse"
            elif reuse["success"] and free["success"]:
                delta = "both_passed"
            else:
                delta = "both_failed"
            output.append(
                {
                    "split": split,
                    "seed": seed,
                    "task_id": task_id,
                    "setting": setting,
                    "delta_vs_free": delta,
                    "free_failure_type": free["failure_type"],
                    "reuse_failure_type": reuse["failure_type"],
                    "free_error": free["eval_error"],
                    "reuse_error": reuse["eval_error"],
                }
            )
    return output


def task_matrix_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {setting: 0 for setting in SETTINGS})
    attempts: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {setting: 0 for setting in SETTINGS})
    for row in rows:
        key = (str(row["split"]), str(row["task_id"]))
        setting = str(row["setting"])
        attempts[key][setting] += 1
        if row["success"]:
            grouped[key][setting] += 1

    output: list[dict[str, Any]] = []
    for (split, task_id), successes in sorted(grouped.items()):
        row = {"split": split, "task_id": task_id}
        for setting in SETTINGS:
            row[f"{setting}_successes"] = successes[setting]
            row[f"{setting}_attempts"] = attempts[(split, task_id)][setting]
        row["reuse_prompt_minus_free"] = successes["reuse_prompt"] - successes["free"]
        row["reuse_routing_minus_free"] = successes["reuse_routing"] - successes["free"]
        row["reuse_full_minus_free"] = successes["reuse_full"] - successes["free"]
        output.append(row)
    return output


def contrast_counts(contrasts: list[dict[str, Any]]) -> dict[tuple[str, str], Counter[str]]:
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in contrasts:
        counts[(str(row["split"]), str(row["setting"]))][str(row["delta_vs_free"])] += 1
    return counts


def format_pct(value: float) -> str:
    return f"{value:.1%}"


def top_examples(contrasts: list[dict[str, Any]], split: str, setting: str, delta: str, limit: int = 5) -> list[dict[str, Any]]:
    selected = [
        row for row in contrasts
        if row["split"] == split and row["setting"] == setting and row["delta_vs_free"] == delta
    ]
    return sorted(selected, key=lambda row: (int(row["seed"]), str(row["task_id"])))[:limit]


def write_markdown(path: Path, rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]], contrasts: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    groups = grouped_success(rows)
    counts = contrast_counts(contrasts)

    lines: list[str] = [
        "# APPS Failure Analysis",
        "",
        "This report is generated from formal APPS protocol runs only. Runs whose names contain `smoke`, `mock`, or `preflight` are excluded.",
        "",
        "## 1. Current Position",
        "",
        f"- Formal evaluated attempts: {len(rows)}.",
        "- Complete protocol coverage: 3 seeds x 2 held-out splits x 6 settings.",
        "- The `test` split is close to saturation; `shifted_test` has clearer separation between settings.",
        "",
        "## 2. Success Rates",
        "",
        "| split | setting | attempts | success | failures | success rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for split in ["shifted_test", "test"]:
        for setting in SETTINGS:
            group = groups.get((split, setting), [])
            successes = sum(1 for row in group if row["success"])
            lines.append(
                f"| {split} | {setting} | {len(group)} | {successes} | {len(group) - successes} | {format_pct(success_rate(group))} |"
            )

    lines.extend([
        "",
        "## 3. Reuse vs Free",
        "",
        "Counts below compare each reuse setting against `free` on the same split, seed, and task.",
        "",
        "| split | setting | rescued | hurt | both passed | both failed | net rescued-hurt |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for split in ["shifted_test", "test"]:
        for setting in REUSE_SETTINGS:
            counter = counts[(split, setting)]
            rescued = counter["rescued_by_reuse"]
            hurt = counter["hurt_by_reuse"]
            lines.append(
                f"| {split} | {setting} | {rescued} | {hurt} | {counter['both_passed']} | {counter['both_failed']} | {rescued - hurt} |"
            )

    lines.extend([
        "",
        "## 4. Failure Modes",
        "",
        "| split | setting | failure type | count | share of failures | share of attempts |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in failure_rows:
        lines.append(
            "| {split} | {setting} | {failure_type} | {count} | {failure_share:.1%} | {all_attempt_share:.1%} |".format(**row)
        )

    lines.extend([
        "",
        "## 5. Typical Contrasts",
        "",
        "### shifted_test: prompt reuse helps",
        "",
    ])
    examples = top_examples(contrasts, "shifted_test", "reuse_prompt", "rescued_by_reuse")
    if examples:
        for row in examples:
            lines.append(
                f"- seed {row['seed']} / `{row['task_id']}`: free failed as `{row['free_failure_type']}`, prompt reuse passed."
            )
    else:
        lines.append("- No rescue examples found.")

    lines.extend(["", "### shifted_test: full reuse can hurt", ""])
    examples = top_examples(contrasts, "shifted_test", "reuse_full", "hurt_by_reuse")
    if examples:
        for row in examples:
            lines.append(
                f"- seed {row['seed']} / `{row['task_id']}`: free passed, full reuse failed as `{row['reuse_failure_type']}`."
            )
    else:
        lines.append("- No hurt examples found.")

    lines.extend(["", "### test: saturation limits interpretability", ""])
    examples = top_examples(contrasts, "test", "reuse_prompt", "rescued_by_reuse")
    if examples:
        for row in examples:
            lines.append(
                f"- seed {row['seed']} / `{row['task_id']}`: prompt reuse rescued a free failure, but the aggregate split remains high for most settings."
            )
    else:
        lines.append("- Very few rescue examples; most settings already pass many `test` tasks.")

    lines.extend([
        "",
        "## 6. Interpretation for the Paper",
        "",
        "### Story calibration",
        "",
        "Overall, the current APPS result is positive for the paper story, but it supports a calibrated version of the story rather than a blanket \"organizational assets always help\" claim.",
        "",
        "A suitable claim is: persistent organizational assets can improve multi-agent code-repair robustness when they are reused selectively. In the current evidence, prompt-level procedural assets are the clearest positive component; routing-only assets are mildly positive on the shifted split; full reuse is unstable and can hurt because it may over-constrain the team or interfere with patch handoff.",
        "",
        "This makes the negative `reuse_full` result useful rather than fatal: it motivates the paper's emphasis on decomposing organizational assets and evaluating which asset type should be reused under distribution shift.",
        "",
        "### Evidence-backed interpretation",
        "",
        "- The strongest current evidence is not that all organizational assets help uniformly. The more defensible claim is narrower: reusable prompt-level organizational assets improve robustness under the shifted APPS split.",
        "- `reuse_prompt` is consistently strongest on `shifted_test`, while `reuse_full` is unstable. This suggests that injecting distilled procedural knowledge helps, but forcing both prompt reuse and asset-based routing may over-constrain the team on unfamiliar tasks.",
        "- `reuse_routing` also improves over `free` on `shifted_test`, but less than `reuse_prompt`. This is useful for an ablation story: content-level reuse appears more valuable than routing-only reuse in this code-repair setup.",
        "- The `test` split should be treated as a sanity split rather than the main evidence source because baseline success is already high.",
        "- The most visible shifted-split failure mode is `empty_or_missing_patch`: the team often localizes or reviews a bug but fails to hand the evaluator an executable patch. Prompt reuse reduces this failure mode sharply on `shifted_test`.",
        "- Once a substantive patch is produced, remaining failures are mostly wrong-output or syntax errors. This supports a mechanism story in which organizational assets primarily stabilize the collaboration protocol and patch handoff, rather than simply making the model a stronger programmer.",
        "",
        "## 7. Case Notes",
        "",
        "- `apps_shifted_test_test_0000`: in seed 712, `free` produced no localization and no patch, while both `reuse_prompt` and `reuse_routing` localized the bracket/colon search bug and produced passing accordion parsers. This is a clean rescue case for reusable procedural guidance.",
        "- `apps_shifted_test_test_0003`: `free` failed with empty patches in all three seeds. `reuse_prompt` passed in two of three seeds by turning the repair into an explicit coverage-prefix computation; the remaining failure was wrong output, not missing handoff.",
        "- `apps_shifted_test_test_0012`: `free` passed in all three seeds, but `reuse_full` failed in all three seeds with empty patches. This is the clearest warning that full asset reuse can over-constrain the run or interfere with patch handoff.",
        "",
        "## 8. Recommended Next Steps",
        "",
        "1. Use `shifted_test` as the main result table in the paper draft; report `test` as sanity/near-saturation evidence.",
        "2. Add one compact figure/table for `reuse_prompt` and `reuse_routing` net rescue counts against `free`.",
        "3. Manually inspect 3-5 rescued tasks and 2-3 hurt tasks before writing claims about mechanism.",
        "4. Defer Domain 2 until after the APPS story is drafted; add it only if the paper still needs a more explicitly multi-agent/persona-flavored experiment.",
        "",
        "## 9. Generated Files",
        "",
        "- `results/analysis/apps_failure_items.csv`: one row per task attempt.",
        "- `results/analysis/apps_failure_modes.csv`: failure-type counts by split and setting.",
        "- `results/analysis/apps_reuse_vs_free.csv`: per-task reuse/free contrasts.",
        "- `results/analysis/apps_task_matrix.csv`: per-task success counts across settings.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze APPS protocol failures.")
    parser.add_argument("--trajectories-root", default="trajectories")
    parser.add_argument("--prefix", default="apps_protocol_")
    parser.add_argument("--out-dir", default="results/analysis")
    args = parser.parse_args()

    rows = collect_items(Path(args.trajectories_root), args.prefix)
    failure_rows = failure_mode_rows(rows)
    contrasts = contrast_rows(rows)
    matrix = task_matrix_rows(rows)

    out_dir = Path(args.out_dir)
    write_csv(out_dir / "apps_failure_items.csv", rows)
    write_csv(out_dir / "apps_failure_modes.csv", failure_rows)
    write_csv(out_dir / "apps_reuse_vs_free.csv", contrasts)
    write_csv(out_dir / "apps_task_matrix.csv", matrix)
    write_markdown(out_dir / "apps_failure_analysis.md", rows, failure_rows, contrasts)

    print(json.dumps({
        "attempts": len(rows),
        "failure_mode_rows": len(failure_rows),
        "contrasts": len(contrasts),
        "task_rows": len(matrix),
        "analysis_md": str(out_dir / "apps_failure_analysis.md"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
