"""Matched-pair statistical significance tests for APPS protocol results.

Aggregates per-task success across seeds and computes:
- Wilcoxon signed-rank p-value on paired (setting_a - setting_b) diffs
- Bootstrap 95% CI on mean diff (10k resamples)
- Sign counts (# rescues vs # hurts vs # ties)

Outputs matching `paper_apps_significance.{md,tex}` under results/tables/.

Usage:
    python3 scripts/statistical_tests.py
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
TRAJ = ROOT / "trajectories"
OUT_DIR = ROOT / "results" / "tables"

# Prefix -> human-readable backbone label
BACKBONES = [
    ("apps_protocol_20260716", "Backbone A (closed-API)"),
    ("apps_protocol_qwen27b_20260722", "Backbone B (Qwen-27B)"),
    ("apps_protocol_qwen9b_20260722", "Backbone C (Qwen-9B)"),
]

# (setting_a, setting_b) contrasts; positive diff means a > b
CONTRASTS = [
    ("reuse_prompt", "free"),
    ("reuse_prompt", "random"),
    ("reuse_full", "free"),
    ("reuse_routing", "free"),
]

SPLITS = ["shifted_test", "test"]

RUN_PATTERN = re.compile(r"_s(\d+)_(\w+?)_(free|manual|random|reuse_full|reuse_prompt|reuse_routing)$")


def load_all() -> Dict[Tuple[str, int, str, str], Dict[str, bool]]:
    """Return mapping (backbone_prefix, seed, split, setting) -> {task_id: success}."""
    data: Dict[Tuple[str, int, str, str], Dict[str, bool]] = {}
    for summary_path in sorted(TRAJ.rglob("summary.json")):
        run_name = summary_path.parent.name
        backbone_prefix = None
        for pref, _ in BACKBONES:
            if run_name.startswith(pref):
                backbone_prefix = pref
                break
        if backbone_prefix is None:
            continue
        m = RUN_PATTERN.search(run_name)
        if not m:
            continue
        seed = int(m.group(1))
        split = m.group(2)
        setting = m.group(3)
        if split not in SPLITS:
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        per_task = {r["task_id"]: bool(r["success"]) for r in summary.get("results", [])}
        data[(backbone_prefix, seed, split, setting)] = per_task
    return data


def bootstrap_ci(diffs: np.ndarray, n_boot: int = 10_000, rng_seed: int = 0) -> Tuple[float, float, float]:
    """Return (mean, lo95, hi95) on the mean of `diffs`."""
    if len(diffs) == 0:
        return (0.0, 0.0, 0.0)
    rng = np.random.default_rng(rng_seed)
    n = len(diffs)
    idx = rng.integers(0, n, size=(n_boot, n))
    boot_means = diffs[idx].mean(axis=1)
    return float(diffs.mean()), float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5))


def wilcoxon_p(diffs: np.ndarray) -> float:
    """Wilcoxon signed-rank two-sided p-value; return 1.0 if all zeros."""
    if len(diffs) == 0 or np.all(diffs == 0):
        return 1.0
    # zero_method='wilcox' drops zero-diff pairs (standard for binary outcomes)
    try:
        res = stats.wilcoxon(diffs, zero_method="wilcox", correction=False, alternative="two-sided")
        return float(res.pvalue)
    except ValueError:
        return 1.0


def format_p(p: float) -> str:
    if p < 0.001:
        return "<0.001"
    if p < 0.01:
        return f"{p:.3f}"
    return f"{p:.2f}"


def format_ci(mean: float, lo: float, hi: float) -> str:
    sign = "+" if mean >= 0 else "\u2212"
    return f"{sign}{abs(mean):.3f} [{lo:+.3f}, {hi:+.3f}]"


def run_analysis() -> List[Dict]:
    data = load_all()

    # Group tasks per (backbone, split, setting) across seeds; matched by (seed, task_id)
    rows: List[Dict] = []
    for backbone_prefix, backbone_label in BACKBONES:
        for split in SPLITS:
            for a_setting, b_setting in CONTRASTS:
                # Collect matched (seed, task_id) diffs
                diffs: List[int] = []
                rescues = hurts = ties = 0
                for seed in [712, 713, 714]:
                    key_a = (backbone_prefix, seed, split, a_setting)
                    key_b = (backbone_prefix, seed, split, b_setting)
                    if key_a not in data or key_b not in data:
                        continue
                    a_map = data[key_a]
                    b_map = data[key_b]
                    for task_id in a_map:
                        if task_id not in b_map:
                            continue
                        d = int(a_map[task_id]) - int(b_map[task_id])
                        diffs.append(d)
                        if d > 0:
                            rescues += 1
                        elif d < 0:
                            hurts += 1
                        else:
                            ties += 1
                diffs_arr = np.array(diffs, dtype=float)
                mean, lo, hi = bootstrap_ci(diffs_arr)
                p_value = wilcoxon_p(diffs_arr)
                rows.append({
                    "backbone": backbone_label,
                    "split": split,
                    "contrast": f"{a_setting} \u2212 {b_setting}",
                    "n_pairs": int(len(diffs_arr)),
                    "rescues": rescues,
                    "hurts": hurts,
                    "ties": ties,
                    "mean_diff": mean,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "p_value": p_value,
                })
    return rows


def write_markdown(path: Path, rows: List[Dict]) -> None:
    lines = [
        "# APPS Matched-Pair Significance Tests",
        "",
        "For each contrast, we pair per-task success indicators across matching",
        "(seed, task_id) and compute the paired difference. `Mean\u00a0diff` reports the",
        "mean over pairs with a bootstrap 95% CI (10k resamples). `p` is the",
        "two-sided Wilcoxon signed-rank test (zeros dropped).",
        "",
        "`Rescues`/`Hurts` count pairs where setting-a succeeds but setting-b fails, and",
        "vice versa; `Ties` are pairs with identical outcomes.",
        "",
        "| Backbone | Split | Contrast | n | Rescues | Hurts | Ties | Mean diff [95% CI] | p |",
        "|---|---|---|---:|---:|---:|---:|:--|---:|",
    ]
    for r in rows:
        lines.append(
            "| {backbone} | {split} | {contrast} | {n_pairs} | {rescues} | {hurts} | {ties} | {ci} | {p} |".format(
                backbone=r["backbone"],
                split=r["split"],
                contrast=r["contrast"],
                n_pairs=r["n_pairs"],
                rescues=r["rescues"],
                hurts=r["hurts"],
                ties=r["ties"],
                ci=format_ci(r["mean_diff"], r["ci_lo"], r["ci_hi"]),
                p=format_p(r["p_value"]),
            )
        )
    lines.append("")
    lines.append("Note: matched pairs are indexed by (seed, task_id) so `n` = number of tasks")
    lines.append("in the split times the number of seeds. On `shifted_test` this is 15\u00d73=45,")
    lines.append("on `test` it is 20\u00d73=60.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tex(path: Path, rows: List[Dict]) -> None:
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{llp{2.2cm}rrp{2.2cm}r}",
        r"\toprule",
        r"Backbone & Split & Contrast & $n$ & R/H/T & Mean diff [95\% CI] & $p$ \\",
        r"\midrule",
    ]
    prev_backbone = None
    for r in rows:
        backbone = r["backbone"] if r["backbone"] != prev_backbone else ""
        prev_backbone = r["backbone"]
        split = r["split"].replace("_", r"\_")
        # replace unicode minus for LaTeX
        contrast = r["contrast"].replace("reuse_", "").replace("_", r"\_").replace("\u2212", "$-$")
        rht = f"{r['rescues']}/{r['hurts']}/{r['ties']}"
        mean_str = f"{r['mean_diff']:+.3f}"
        mean_str = mean_str.replace("+", "$+$").replace("-", "$-$")
        ci_str = f"[{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]".replace("+", "").replace("-", "$-$")
        # Simpler: rebuild
        m = r['mean_diff']; lo = r['ci_lo']; hi = r['ci_hi']
        def _fmt(v: float) -> str:
            return f"$+${abs(v):.3f}" if v >= 0 else f"$-${abs(v):.3f}"
        mean_ci = f"{_fmt(m)} [{_fmt(lo)}, {_fmt(hi)}]"
        p_str = format_p(r["p_value"]).replace("<", "$<$")
        lines.append(f"{backbone} & {split} & {contrast} & {r['n_pairs']} & {rht} & {mean_ci} & {p_str} \\\\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\caption{Matched-pair significance tests on APPS success. Pairs are indexed by (seed, task\_id). Mean diff and 95\% CI computed by 10k-resample bootstrap on paired differences; $p$-values are two-sided Wilcoxon signed-rank (zeros dropped). R/H/T = rescues / hurts / ties.}",
        r"\label{tab:apps-significance}",
        r"\end{table}",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = run_analysis()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = OUT_DIR / "paper_apps_significance.md"
    tex = OUT_DIR / "paper_apps_significance.tex"
    write_markdown(md, rows)
    write_tex(tex, rows)
    print(f"Wrote {md}")
    print(f"Wrote {tex}")
    # Also dump a JSON of everything for later programmatic use
    json_path = OUT_DIR / "paper_apps_significance.json"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {json_path}")

    # Print a compact preview to stdout
    print("\nPreview (Prompt \u2212 Free only):")
    for r in rows:
        if r["contrast"].startswith("reuse_prompt \u2212 free"):
            print(f"  {r['backbone']:32s} {r['split']:14s} "
                  f"mean {r['mean_diff']:+.3f}  CI [{r['ci_lo']:+.3f},{r['ci_hi']:+.3f}]  "
                  f"p={format_p(r['p_value'])}  R/H/T={r['rescues']}/{r['hurts']}/{r['ties']}")


if __name__ == "__main__":
    main()
