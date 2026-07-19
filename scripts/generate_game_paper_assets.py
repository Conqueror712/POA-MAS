from __future__ import annotations

import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGGREGATE_CSV = ROOT / "results" / "tables" / "game_domain_aggregate.csv"
FIG_DIR = ROOT / "results" / "figures"
TABLE_DIR = ROOT / "results" / "tables"

SPLITS = ["test", "shifted_test"]
GAMES = ["iterated_prisoners_dilemma", "public_goods"]
SETTINGS = ["no_persona", "persona", "reuse_assets"]

SPLIT_LABELS = {
    "test": "test",
    "shifted_test": "shifted",
}
GAME_LABELS = {
    "iterated_prisoners_dilemma": "IPD",
    "public_goods": "Public Goods",
}
SETTING_LABELS = {
    "no_persona": "No persona",
    "persona": "Persona",
    "reuse_assets": "Reuse assets",
}
SETTING_COLORS = {
    "no_persona": "#a8a29e",
    "persona": "#4a9b8f",
    "reuse_assets": "#df6f5d",
}

INK = "#111827"
TEXT = "#1f2933"
MUTED = "#5f6f73"
GRID = "#ddd8cf"
AXIS = "#111827"
PAPER = "#fbf7f0"
PANEL = "#fffdf8"
TEST_COLOR = "#4a86a8"
SHIFTED_COLOR = "#df6f5d"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def fmt3(value: str | float) -> str:
    return f"{float(value):.3f}"


def text(
    x: float,
    y: float,
    body: str,
    *,
    size: int = 11,
    anchor: str = "middle",
    weight: str = "400",
    rotate: int | None = None,
    fill: str = "#1f2933",
) -> str:
    transform = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate is not None else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}"{transform}>{esc(body)}</text>'
    )


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#4b5563", width: float = 1.0) -> str:
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"/>'


def rect(x: float, y: float, w: float, h: float, *, fill: str, stroke: str = "none", width: float = 0.0) -> str:
    stroke_attr = "" if stroke == "none" else f' stroke="{stroke}" stroke-width="{width}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"{stroke_attr}/>'


def circle(x: float, y: float, r: float, *, fill: str, stroke: str = "white", width: float = 1.3) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def rounded_rect(x: float, y: float, w: float, h: float, *, fill: str, stroke: str, width: float = 1.0, radius: float = 7.0) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="{radius:.1f}" ry="{radius:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
    )


def svg_document(width: int, height: int, body: list[str]) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<rect width="100%" height="100%" fill="{PAPER}"/>',
            *body,
            "</svg>",
            "",
        ]
    )


def y_scale(value: float, top: float, bottom: float, max_value: float) -> float:
    return bottom - (value / max_value) * (bottom - top)


def rows_by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {(row["split"], row["game_type"], row["setting"]): row for row in rows}


def write_cooperation_figure(rows: list[dict[str, str]]) -> Path:
    by_key = rows_by_key(rows)
    width, height = 980, 570
    left, top = 72, 86
    panel_w, panel_h = 398, 186
    col_gap, row_gap = 38, 54
    body: list[str] = []

    body.append(text(width / 2, 28, "Domain 2 Cooperation in Repeated Social Dilemmas", size=16, weight="700"))
    body.append(text(width / 2, 50, "Each panel is one formal game instance; all invalid-action rates are zero.", size=11))
    body.append(text(24, top + panel_h + row_gap / 2, "Cooperation rate", size=12, rotate=-90))

    panels = [
        ("test", "iterated_prisoners_dilemma"),
        ("test", "public_goods"),
        ("shifted_test", "iterated_prisoners_dilemma"),
        ("shifted_test", "public_goods"),
    ]
    for idx, (split, game) in enumerate(panels):
        col, row_idx = idx % 2, idx // 2
        x0 = left + col * (panel_w + col_gap)
        y0 = top + row_idx * (panel_h + row_gap)
        y1 = y0 + panel_h - 34
        plot_top = y0 + 44
        body.append(rounded_rect(x0, y0, panel_w, panel_h, fill=PANEL, stroke="#eadfce", width=1.0, radius=14))
        body.append(text(x0 + 18, y0 + 26, f"{GAME_LABELS[game]} / {SPLIT_LABELS[split]}", size=12, anchor="start", weight="700"))
        for tick in [0.0, 0.5, 1.0]:
            y = y_scale(tick, plot_top, y1, 1.0)
            body.append(line(x0 + 44, y, x0 + panel_w - 24, y, stroke=GRID, width=0.8))
            body.append(text(x0 + 34, y + 4, f"{tick:.1f}", size=9, anchor="end", fill=MUTED))
        body.append(line(x0 + 44, plot_top, x0 + 44, y1, stroke=AXIS, width=0.8))
        body.append(line(x0 + 44, y1, x0 + panel_w - 24, y1, stroke=AXIS, width=0.8))

        bar_w = 58
        x_positions = [x0 + 94, x0 + 198, x0 + 302]
        for setting, x in zip(SETTINGS, x_positions):
            value = float(by_key[(split, game, setting)]["avg_cooperation_rate"])
            y = y_scale(value, plot_top, y1, 1.0)
            body.append(rounded_rect(x - bar_w / 2, y, bar_w, y1 - y, fill=SETTING_COLORS[setting], stroke="none", width=0, radius=7))
            body.append(text(x, y - 8, fmt3(value), size=10, weight="700"))
            body.append(text(x, y1 + 19, SETTING_LABELS[setting], size=9))

    body.append(text(width / 2, 548, "Public Goods shows the clearest monotonic pattern; shifted IPD is saturated.", size=11))
    path = FIG_DIR / "game_domain_cooperation.svg"
    path.write_text(svg_document(width, height, body), encoding="utf-8")
    return path


def write_payoff_figure(rows: list[dict[str, str]]) -> Path:
    by_key = rows_by_key(rows)
    width, height = 980, 450
    left, top = 72, 82
    panel_w, panel_h, col_gap = 398, 278, 38
    body: list[str] = []

    body.append(text(width / 2, 28, "Average Payoff by Condition", size=16, weight="700"))
    body.append(text(width / 2, 50, "Game-specific y-axis scales; compare conditions within each panel.", size=11))
    body.append(text(24, top + panel_h / 2, "Average payoff", size=12, rotate=-90))

    for gi, game in enumerate(GAMES):
        x0 = left + gi * (panel_w + col_gap)
        y0, y1 = top + 48, top + panel_h - 44
        max_payoff = 3.0 if game == "iterated_prisoners_dilemma" else 16.0
        ticks = [0, 1.5, 3.0] if max_payoff == 3.0 else [0, 8, 16]
        body.append(rounded_rect(x0, top, panel_w, panel_h, fill=PANEL, stroke="#eadfce", width=1.0, radius=14))
        body.append(text(x0 + 18, top + 28, GAME_LABELS[game], size=12, anchor="start", weight="700"))
        for tick in ticks:
            y = y_scale(tick, y0, y1, max_payoff)
            body.append(line(x0 + 44, y, x0 + panel_w - 24, y, stroke=GRID, width=0.8))
            body.append(text(x0 + 34, y + 4, f"{tick:g}", size=9, anchor="end", fill=MUTED))
        body.append(line(x0 + 44, y0, x0 + 44, y1, stroke=AXIS, width=0.8))
        body.append(line(x0 + 44, y1, x0 + panel_w - 24, y1, stroke=AXIS, width=0.8))

        group_centers = [x0 + 100, x0 + 204, x0 + 308]
        bar_w = 25
        for setting, gx in zip(SETTINGS, group_centers):
            for split, offset, color in [("test", -bar_w / 2 - 2, TEST_COLOR), ("shifted_test", bar_w / 2 + 2, SHIFTED_COLOR)]:
                value = float(by_key[(split, game, setting)]["avg_payoff"])
                y = y_scale(value, y0, y1, max_payoff)
                body.append(rounded_rect(gx + offset - bar_w / 2, y, bar_w, y1 - y, fill=color, stroke="none", width=0, radius=5))
            body.append(text(gx, y1 + 19, SETTING_LABELS[setting], size=9))

    legend_x = 360
    legend_y = 420
    body.append(rect(legend_x, legend_y - 11, 20, 11, fill=TEST_COLOR))
    body.append(text(legend_x + 28, legend_y, "test", size=10, anchor="start", weight="700"))
    body.append(rect(legend_x + 92, legend_y - 11, 20, 11, fill=SHIFTED_COLOR))
    body.append(text(legend_x + 120, legend_y, "shifted", size=10, anchor="start", weight="700"))

    path = FIG_DIR / "game_domain_payoff.svg"
    path.write_text(svg_document(width, height, body), encoding="utf-8")
    return path


def write_markdown_table(path: Path, headers: list[str], rows: list[list[str]], *, right_align_from: int) -> None:
    align = ["---" if idx < right_align_from else "---:" for idx in range(len(headers))]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(align) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def latex_escape(value: str) -> str:
    return value.replace("_", "\\_").replace("%", "\\%")


def write_latex_table(path: Path, caption: str, label: str, headers: list[str], rows: list[list[str]]) -> None:
    cols = "l" + "r" * (len(headers) - 1)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        f"\\begin{{tabular}}{{{cols}}}",
        "\\toprule",
        " & ".join(latex_escape(h) for h in headers) + " \\\\",
        "\\midrule",
    ]
    lines.extend(" & ".join(latex_escape(cell) for cell in row) + " \\\\" for row in rows)
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            "\\end{table}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_paper_tables(rows: list[dict[str, str]]) -> list[Path]:
    by_key = rows_by_key(rows)
    paths: list[Path] = []
    table_rows: list[list[str]] = []
    for split in SPLITS:
        for game in GAMES:
            for setting in SETTINGS:
                row = by_key[(split, game, setting)]
                setting_label = SETTING_LABELS[setting]
                if setting == "reuse_assets":
                    setting_label = f"**{setting_label}**"
                table_rows.append(
                    [
                        SPLIT_LABELS[split],
                        GAME_LABELS[game],
                        setting_label,
                        fmt3(row["avg_cooperation_rate"]),
                        fmt3(row["avg_payoff"]),
                        fmt3(row["total_social_welfare"]),
                        fmt3(row["avg_invalid_action_rate"]),
                    ]
                )
    headers = ["Split", "Game", "Setting", "Coop.", "Avg. payoff", "Welfare", "Invalid"]
    p = TABLE_DIR / "paper_game_main_results.md"
    write_markdown_table(p, headers, table_rows, right_align_from=3)
    paths.append(p)
    p = TABLE_DIR / "paper_game_main_results.tex"
    write_latex_table(
        p,
        "Repeated social-dilemma results in Domain 2. Invalid is the invalid-action rate.",
        "tab:game-main",
        headers,
        [[cell.replace("**", "") for cell in row] for row in table_rows],
    )
    paths.append(p)

    contrast_rows: list[list[str]] = []
    for split in SPLITS:
        for game in GAMES:
            no_persona = float(by_key[(split, game, "no_persona")]["avg_cooperation_rate"])
            persona = float(by_key[(split, game, "persona")]["avg_cooperation_rate"])
            reuse = float(by_key[(split, game, "reuse_assets")]["avg_cooperation_rate"])
            contrast_rows.append(
                [
                    SPLIT_LABELS[split],
                    GAME_LABELS[game],
                    f"{persona - no_persona:+.3f}",
                    f"{reuse - no_persona:+.3f}",
                    f"{reuse - persona:+.3f}",
                ]
            )
    headers = ["Split", "Game", "Persona - no persona", "Reuse - no persona", "Reuse - persona"]
    p = TABLE_DIR / "paper_game_cooperation_deltas.md"
    write_markdown_table(p, headers, contrast_rows, right_align_from=2)
    paths.append(p)
    p = TABLE_DIR / "paper_game_cooperation_deltas.tex"
    write_latex_table(
        p,
        "Cooperation-rate deltas relative to no-persona and persona conditions.",
        "tab:game-deltas",
        headers,
        contrast_rows,
    )
    paths.append(p)
    return paths


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(AGGREGATE_CSV)
    figure_paths = [
        write_cooperation_figure(rows),
        write_payoff_figure(rows),
    ]
    table_paths = write_paper_tables(rows)
    print("Generated Domain 2 figures:")
    for path in figure_paths:
        print(f"- {path.relative_to(ROOT)}")
    print("Generated Domain 2 tables:")
    for path in table_paths:
        print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
