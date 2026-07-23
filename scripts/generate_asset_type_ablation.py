"""Aggregate the asset-type ablation runs (Qwen27B) and emit paper tables.

Ablation setup: prompt-channel reuse with the loaded asset set restricted to a
single type: role assets only, or organization assets only. The full-asset
Prompt condition and the Free baseline come from the existing main table
(results/tables_qwen27b/apps_protocol_summary.csv).

Emits: results/tables/paper_apps_asset_type_ablation.{md,tex}
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
TRAJ = ROOT / "trajectories"
OUT_DIR = ROOT / "results" / "tables"


def load_ablation() -> Dict[Tuple[str, str], List[float]]:
    groups: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for d in sorted(TRAJ.glob("apps_ablation_qwen27b_20260723_*")):
        summary_path = d / "summary.json"
        if not summary_path.exists():
            continue
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        asset_mode = d.name.split("_")[-1]  # role or organization
        key = (s["task_split"], asset_mode)
        groups[key].append(float(s["success_rate"]))
    return groups


def load_reference(csv_path: Path, setting: str) -> Dict[str, float]:
    """Read one setting row per split from the Qwen27B main aggregate CSV."""
    out: Dict[str, float] = {}
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            if row["setting"] == setting:
                out[row["split"]] = float(row["avg_success"])
    return out


def fmt(v: float | None) -> str:
    return f"{v:.3f}" if v is not None else "\u2013"


def main() -> None:
    ablation = load_ablation()
    ref_csv = ROOT / "results" / "tables_qwen27b" / "apps_protocol_summary.csv"
    ref_free = load_reference(ref_csv, "free")
    ref_prompt_full = load_reference(ref_csv, "reuse_prompt")

    md = [
        "# APPS Asset-Type Ablation (Prompt Channel, Qwen3.6-27B)",
        "",
        "Within the prompt-channel reuse strategy, we restrict the loaded asset",
        "set to a single asset type and compare the resulting success rate to",
        "the full-asset Prompt condition (which loads both role and organization",
        "assets) and to the Free baseline.",
        "",
        "All runs use Qwen3.6-27B (Backbone B) with 3 seeds (712, 713, 714).",
        "",
        "| Split | Asset set | Mean | Min | Max | \u0394 vs Free | \u0394 vs Full Prompt |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    tex_rows = []
    for split in ("shifted_test", "test"):
        for label, mode in (("Role only", "role"), ("Organization only", "organization")):
            vals = ablation.get((split, mode), [])
            if not vals:
                continue
            mean = sum(vals) / len(vals)
            free = ref_free.get(split, 0.0)
            full = ref_prompt_full.get(split, 0.0)
            delta_free = mean - free
            delta_full = mean - full
            def _sd(x: float) -> str:
                return ("+" if x >= 0 else "\u2212") + f"{abs(x):.3f}"
            md.append(
                f"| {split} | {label} | {mean:.3f} | {min(vals):.3f} | {max(vals):.3f} | {_sd(delta_free)} | {_sd(delta_full)} |"
            )
            tex_rows.append((split, label, mean, min(vals), max(vals), delta_free, delta_full))
        # Add reference rows
        md.append(f"| {split} | **Full (role + org)** | {ref_prompt_full.get(split, 0.0):.3f} | \u2013 | \u2013 | {('+' if ref_prompt_full.get(split,0) - ref_free.get(split,0) >= 0 else chr(0x2212)) + f'{abs(ref_prompt_full.get(split,0) - ref_free.get(split,0)):.3f}'} | (ref) |")
        md.append(f"| {split} | *Free (no assets)* | {ref_free.get(split, 0.0):.3f} | \u2013 | \u2013 | (ref) | \u2013 |")

    md += [
        "",
        "Reading:",
        "- On both splits, restricting Prompt to a single asset type",
        "  (role-only or organization-only) *does not* improve over Free and",
        "  is worse than the full-asset Prompt condition. The role and",
        "  organization assets appear to act complementarily rather than as",
        "  independent contributors.",
        "- This dissociates the effect: the observed Prompt-vs-Free gap on this",
        "  backbone is not driven by any single asset type, and the",
        "  full-asset Prompt condition is what carries the improvement.",
    ]
    md_path = OUT_DIR / "paper_apps_asset_type_ablation.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {md_path}")

    # LaTeX
    tex = [
        r"\begin{table}[t]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{llrrr}",
        r"\toprule",
        r"Split & Asset set & Mean & $\Delta$ vs.\ Free & $\Delta$ vs.\ Full \\",
        r"\midrule",
    ]
    prev_split = None
    for split, label, mean, mn, mx, df, dfl in tex_rows:
        split_str = split.replace("_", r"\_") if split != prev_split else ""
        prev_split = split
        def _tex_signed(v: float) -> str:
            sign = "$+$" if v >= 0 else "$-$"
            return f"{sign}{abs(v):.3f}"
        tex.append(f"{split_str} & {label} & {mean:.3f} & {_tex_signed(df)} & {_tex_signed(dfl)} \\\\")
    # Reference rows
    for split in ("shifted\\_test", "test"):
        s = split.replace("\\_", "_")
        tex.append(f"{split} & \\textbf{{Full (role + org)}} & {ref_prompt_full.get(s, 0):.3f} & {'$+$' if ref_prompt_full.get(s,0) - ref_free.get(s,0) >= 0 else '$-$'}{abs(ref_prompt_full.get(s,0) - ref_free.get(s,0)):.3f} & (ref) \\\\")
        tex.append(f"{split} & \\emph{{Free (no assets)}} & {ref_free.get(s, 0):.3f} & (ref) & \\textendash \\\\")
    tex += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\caption{Asset-type ablation on Backbone B (Qwen3.6-27B), prompt-channel reuse only, 3 seeds. Restricting Prompt to a single asset type does not improve over Free and is worse than the full-asset Prompt condition; the role and organization assets appear complementary rather than independently sufficient.}",
        r"\label{tab:apps-asset-type-ablation}",
        r"\end{table}",
    ]
    tex_path = OUT_DIR / "paper_apps_asset_type_ablation.tex"
    tex_path.write_text("\n".join(tex) + "\n", encoding="utf-8")
    print(f"Wrote {tex_path}")


if __name__ == "__main__":
    main()
