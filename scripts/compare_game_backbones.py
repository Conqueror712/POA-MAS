"""Compare Domain 2 (games) results across two backbones (DeepSeek and Qwen27B).

The DeepSeek numbers are read from the paper's canonical Domain 2 table
(paper_game_main_results.tex), which is the ground truth for the paper.
The Qwen27B numbers are aggregated from
trajectories/game_asset_qwen27b_20260723_* .

Emits:
  results/tables/paper_game_cross_model.{md,tex}
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "tables"

# Ground-truth DeepSeek numbers (from paper Table 5 / paper_game_main_results.tex).
# These are the paper's canonical Domain 2 results at Backbone A.
DEEPSEEK = {
    ("test", "iterated_prisoners_dilemma", "no_persona"): 0.854,
    ("test", "iterated_prisoners_dilemma", "persona"): 1.000,
    ("test", "iterated_prisoners_dilemma", "reuse_assets"): 0.979,
    ("test", "public_goods", "no_persona"): 0.611,
    ("test", "public_goods", "persona"): 0.750,
    ("test", "public_goods", "reuse_assets"): 0.986,
    ("shifted_test", "iterated_prisoners_dilemma", "no_persona"): 1.000,
    ("shifted_test", "iterated_prisoners_dilemma", "persona"): 1.000,
    ("shifted_test", "iterated_prisoners_dilemma", "reuse_assets"): 1.000,
    ("shifted_test", "public_goods", "no_persona"): 0.056,
    ("shifted_test", "public_goods", "persona"): 0.767,
    ("shifted_test", "public_goods", "reuse_assets"): 0.833,
}


def load_qwen27b() -> dict[tuple[str, str, str], float]:
    md_path = ROOT / "results" / "tables_qwen27b_games" / "game_domain_aggregate.md"
    text = md_path.read_text(encoding="utf-8")
    values: dict[tuple[str, str, str], float] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or "split" in line:
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) < 5:
            continue
        split, game, setting = parts[0], parts[1], parts[2]
        try:
            coop = float(parts[4])
        except (ValueError, IndexError):
            continue
        values[(split, game, setting)] = coop
    return values


def fmt(v: float | None) -> str:
    return f"{v:.3f}" if v is not None else "\u2013"


def main() -> None:
    qwen = load_qwen27b()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for split in ("test", "shifted_test"):
        for game in ("public_goods", "iterated_prisoners_dilemma"):
            for setting in ("no_persona", "persona", "reuse_assets"):
                key = (split, game, setting)
                d = DEEPSEEK.get(key)
                q = qwen.get(key)
                rows.append({
                    "split": split,
                    "game": "PG" if game == "public_goods" else "IPD",
                    "setting": setting,
                    "deepseek": d,
                    "qwen27b": q,
                    "delta": (q - d) if (d is not None and q is not None) else None,
                })

    # Markdown
    md_lines = [
        "# Domain 2 Cross-Model Cooperation Rate",
        "",
        "Cooperation rate on Domain 2 held-out splits, averaged over 3 seeds.",
        "Backbone A = closed-API production LLM family (paper Table 5).",
        "Backbone B = Qwen3.6-27B via local vLLM (this run,",
        "`game_asset_qwen27b_20260723_*`).",
        "",
        "| Split | Game | Setting | Backbone A | Backbone B | \u0394 (B\u2212A) |",
        "|---|---|---|---:|---:|---:|",
    ]
    for r in rows:
        delta_str = ("\u2013" if r["delta"] is None
                     else ("$-$" if r["delta"] < 0 else "$+$") + f"{abs(r['delta']):.3f}")
        # for markdown use plain +/- rather than tex-escaped
        delta_str_md = "\u2013" if r["delta"] is None else ("+" if r["delta"] >= 0 else "\u2212") + f"{abs(r['delta']):.3f}"
        md_lines.append(f"| {r['split']} | {r['game']} | {r['setting']} | {fmt(r['deepseek'])} | {fmt(r['qwen27b'])} | {delta_str_md} |")
    md_lines += [
        "",
        "Interpretation summary:",
        "- **PG shifted_test**: on Backbone A, reuse (0.833) improves over persona (0.767)",
        "  and sharply over no_persona (0.056). On Backbone B, reuse (0.800) matches persona (0.800)",
        "  and both remain far above no_persona (0.000). The persona\u2192no_persona gap replicates,",
        "  but the reuse-over-persona increment does not.",
        "- **PG test**: on Backbone A, reuse (0.986) is the best condition. On Backbone B,",
        "  no_persona (1.000) is already saturated; reuse (0.833) does not improve on it.",
        "- **IPD**: saturated near 1.000 on both backbones across all conditions, uninformative",
        "  for reuse comparison.",
    ]
    md_path = OUT_DIR / "paper_game_cross_model.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Wrote {md_path}")

    # LaTeX
    tex_lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{llllrrr}",
        r"\toprule",
        r"Split & Game & Setting & Backbone A & Backbone B & $\Delta$ \\",
        r"\midrule",
    ]
    prev_split = None
    prev_game = None
    for r in rows:
        split = r["split"].replace("_", r"\_") if r["split"] != prev_split else ""
        prev_split = r["split"] if r["split"] != prev_split else prev_split
        game = r["game"] if r["game"] != prev_game else ""
        prev_game = r["game"] if r["game"] != prev_game else prev_game
        # Reset prev_game whenever split changes so each game repeats under new split
        # (simpler: recompute using a state machine)
        d_str = fmt(r["deepseek"])
        q_str = fmt(r["qwen27b"])
        if r["delta"] is None:
            delta_str = "\u2013"
        else:
            sign = "$+$" if r["delta"] >= 0 else "$-$"
            delta_str = f"{sign}{abs(r['delta']):.3f}"
        tex_lines.append(f"{r['split'].replace('_', chr(92)+'_')} & {r['game']} & {r['setting'].replace('_', chr(92)+'_')} & {d_str} & {q_str} & {delta_str} \\\\")
    tex_lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\caption{Domain 2 cooperation rate under two backbones (3 seeds each). Backbone A is the closed-API family; Backbone B is the open-weights 27B backbone from Section~\ref{sec:apps-cross-model}. The persona-vs-no-persona gap in Public Goods reproduces on Backbone B; the additional reuse-vs-persona increment observed on Backbone A does not. Iterated Prisoner's Dilemma is saturated on both backbones.}",
        r"\label{tab:games-cross-model}",
        r"\end{table}",
    ]
    tex_path = OUT_DIR / "paper_game_cross_model.tex"
    tex_path.write_text("\n".join(tex_lines) + "\n", encoding="utf-8")
    print(f"Wrote {tex_path}")


if __name__ == "__main__":
    main()
