from __future__ import annotations

import csv
import html
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_CSV = ROOT / "results" / "tables" / "apps_protocol_summary.csv"
FAILURE_MODES_CSV = ROOT / "results" / "analysis" / "apps_failure_modes.csv"
REUSE_VS_FREE_CSV = ROOT / "results" / "analysis" / "apps_reuse_vs_free.csv"
FIG_DIR = ROOT / "results" / "figures"
TABLE_DIR = ROOT / "results" / "tables"

SETTINGS = ["free", "manual", "random", "reuse_prompt", "reuse_routing", "reuse_full"]
SETTING_LABELS = {
    "free": "Free",
    "manual": "Manual",
    "random": "Random",
    "reuse_prompt": "Prompt",
    "reuse_routing": "Routing",
    "reuse_full": "Full",
}
REUSE_SETTINGS = ["reuse_prompt", "reuse_routing", "reuse_full"]

INK = "#111827"
TEXT = "#1f2933"
MUTED = "#5f6f73"
GRID = "#d8ddd7"
AXIS = "#111827"
PAPER = "#fbf7f0"
PANEL = "#fffdf8"
BLUE = "#4a86a8"
BLUE_LIGHT = "#9fc5d6"
CORAL = "#df6f5d"
GOLD = "#d9a441"
TEAL = "#3f9b8f"
GRAY = "#9ca3af"
GRAY_DARK = "#475569"
RED = "#b35c50"
GREEN = "#3f9b8f"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def fmt3(value: str | float) -> str:
    return f"{float(value):.3f}"


def text(x: float, y: float, body: str, *, size: int = 11, anchor: str = "middle", weight: str = "400", rotate: int | None = None) -> str:
    transform = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate is not None else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{TEXT}"{transform}>{esc(body)}</text>'
    )


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#4b5563", width: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'


def rect(x: float, y: float, w: float, h: float, *, fill: str, stroke: str = "none", width: float = 0.0) -> str:
    stroke_attr = "" if stroke == "none" else f' stroke="{stroke}" stroke-width="{width}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"{stroke_attr}/>'


def polygon(points: list[tuple[float, float]], *, fill: str, stroke: str, width: float = 1.0, opacity: float = 1.0) -> str:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity:.2f}"/>'


def circle(x: float, y: float, r: float, *, fill: str, stroke: str = "white", width: float = 1.3) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def svg_document(width: int, height: int, body: list[str]) -> str:
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        *body,
        "</svg>",
        "",
    ])


def y_scale(value: float, top: float, bottom: float, max_value: float = 1.0) -> float:
    return bottom - (value / max_value) * (bottom - top)


def write_success_figure(summary_rows: list[dict[str, str]]) -> Path:
    by_key = {(row["split"], row["setting"]): row for row in summary_rows}
    width, height = 860, 560
    cx, cy, radius = 430, 292, 176
    body: list[str] = []

    body.append(text(width / 2, 28, "APPS Code Repair Success Rate", size=16, weight="700"))
    body.append(text(width / 2, 50, "Mean success over three seeds; larger radius indicates higher success.", size=11, weight="400"))
    body.append(f'<rect x="78" y="72" width="704" height="422" rx="18" ry="18" fill="{PANEL}" stroke="#eadfce" stroke-width="1.1"/>')

    angles = [-math.pi / 2 + i * 2 * math.pi / len(SETTINGS) for i in range(len(SETTINGS))]

    def radar_point(value: float, angle: float) -> tuple[float, float]:
        r = radius * value
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    for tick in [0.6, 0.8, 1.0]:
        pts = [radar_point(tick, angle) for angle in angles]
        body.append(polygon(pts, fill="none", stroke=GRID, width=1.0, opacity=1.0))
        body.append(text(cx + 6, cy - radius * tick + 4, f"{tick:.1f}", size=9, anchor="start", weight="700"))
    for setting, angle in zip(SETTINGS, angles):
        x, y = radar_point(1.05, angle)
        body.append(line(cx, cy, *radar_point(1.0, angle), stroke="#e4d8c8", width=0.8))
        anchor = "middle"
        if x < cx - 30:
            anchor = "end"
        elif x > cx + 30:
            anchor = "start"
        body.append(text(x, y + (4 if abs(x - cx) > 30 else 0), SETTING_LABELS[setting], size=11, anchor=anchor, weight="700"))

    split_specs = {
        "test": (BLUE, "#4a86a8"),
        "shifted_test": (CORAL, "#df6f5d"),
    }
    for split, (fill_color, stroke_color) in split_specs.items():
        pts = [radar_point(float(by_key[(split, setting)]["avg_success"]), angle) for setting, angle in zip(SETTINGS, angles)]
        body.append(polygon(pts, fill=fill_color, stroke=stroke_color, width=2.3, opacity=0.33 if split == "test" else 0.42))
        for setting, angle in zip(SETTINGS, angles):
            x, y = radar_point(float(by_key[(split, setting)]["avg_success"]), angle)
            body.append(circle(x, y, 4.4, fill=stroke_color, stroke=PANEL, width=1.5))

    legend_x, legend_y = 108, 455
    body.append(rect(legend_x, legend_y - 10, 20, 11, fill=BLUE))
    body.append(text(legend_x + 28, legend_y, "test", size=11, anchor="start", weight="700"))
    body.append(rect(legend_x + 88, legend_y - 10, 20, 11, fill=CORAL))
    body.append(text(legend_x + 116, legend_y, "shifted_test", size=11, anchor="start", weight="700"))
    body.append(text(width / 2, 525, "Prompt reuse expands the shifted-test polygon, while full reuse contracts it.", size=11))
    path = FIG_DIR / "apps_success_rates.svg"
    path.write_text(svg_document(width, height, body), encoding="utf-8")
    return path


def contrast_counts(rows: list[dict[str, str]]) -> dict[tuple[str, str], Counter[str]]:
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in rows:
        counts[(row["split"], row["setting"])][row["delta_vs_free"]] += 1
    return counts


def write_reuse_contrast_figure(contrast_rows: list[dict[str, str]]) -> Path:
    counts = contrast_counts(contrast_rows)
    width, height = 860, 420
    left, right, top, bottom = 150, 52, 56, 330
    mid_x = left + (width - left - right) / 2
    unit = 18
    body: list[str] = []
    body.append(text(width / 2, 28, "Reuse vs. Free on Matched Tasks", size=16, weight="700"))
    body.append(text(width / 2, 46, "Positive bars are rescued task-attempts; negative bars are hurt task-attempts", size=11))
    body.append(line(mid_x, top - 8, mid_x, bottom + 8, stroke="#111827", width=1.2))
    for tick in [-8, -4, 0, 4, 8]:
        x = mid_x + tick * unit
        body.append(line(x, bottom, x, bottom + 5, stroke="#111827", width=1))
        body.append(text(x, bottom + 21, str(tick), size=10))
        if tick != 0:
            body.append(line(x, top, x, bottom, stroke=GRID, width=0.8))

    rows_for_plot = []
    for split in ["shifted_test", "test"]:
        for setting in REUSE_SETTINGS:
            counter = counts[(split, setting)]
            rows_for_plot.append((split, setting, counter["rescued_by_reuse"], counter["hurt_by_reuse"]))

    row_gap = 42
    for i, (split, setting, rescued, hurt) in enumerate(rows_for_plot):
        y = top + i * row_gap + 18
        label = f"{split} / {SETTING_LABELS[setting]}"
        body.append(text(left - 12, y + 4, label, size=11, anchor="end"))
        body.append(rect(mid_x, y - 10, rescued * unit, 18, fill=BLUE))
        body.append(rect(mid_x - hurt * unit, y - 10, hurt * unit, 18, fill=RED))
        body.append(text(mid_x + rescued * unit + 8, y + 4, f"+{rescued}", size=10, anchor="start"))
        body.append(text(mid_x - hurt * unit - 8, y + 4, f"-{hurt}", size=10, anchor="end"))

    body.append(text(mid_x - 70, bottom + 45, "hurt", size=11))
    body.append(text(mid_x + 70, bottom + 45, "rescued", size=11))
    path = FIG_DIR / "apps_reuse_vs_free.svg"
    path.write_text(svg_document(width, height, body), encoding="utf-8")
    return path


def write_failure_modes_figure(failure_rows: list[dict[str, str]]) -> Path:
    shifted = [row for row in failure_rows if row["split"] == "shifted_test"]
    by_setting: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in shifted:
        by_setting[row["setting"]][row["failure_type"]] = int(row["count"])

    width, height = 900, 430
    left, right, top, bottom = 82, 34, 54, 332
    plot_w = width - left - right
    group_w = plot_w / len(SETTINGS)
    max_failures = 18
    colors = {
        "empty_or_missing_patch": BLUE,
        "syntax_error": GOLD,
        "wrong_output": RED,
        "runtime_error": "#6b7280",
        "timeout": "#7c3aed",
        "other_failure": GRAY,
    }
    order = ["empty_or_missing_patch", "syntax_error", "wrong_output", "runtime_error", "timeout", "other_failure"]
    body: list[str] = []
    body.append(text(width / 2, 28, "Failure Modes on shifted_test", size=16, weight="700"))
    body.append(text(width / 2, 46, "Counts over 45 task-attempts per setting", size=11))
    for tick in [0, 5, 10, 15]:
        y = bottom - (tick / max_failures) * (bottom - top)
        body.append(line(left, y, left + plot_w, y, stroke=GRID, width=0.8))
        body.append(text(left - 12, y + 4, str(tick), size=10, anchor="end"))
    body.append(line(left, top, left, bottom, stroke="#111827", width=1.1))
    body.append(line(left, bottom, left + plot_w, bottom, stroke="#111827", width=1.1))
    body.append(text(22, (top + bottom) / 2, "Failure count", size=12, rotate=-90))

    bar_w = 44
    for i, setting in enumerate(SETTINGS):
        x = left + group_w * i + group_w / 2 - bar_w / 2
        current_y = bottom
        for failure_type in order:
            count = by_setting[setting].get(failure_type, 0)
            if count == 0:
                continue
            h = (count / max_failures) * (bottom - top)
            current_y -= h
            body.append(rect(x, current_y, bar_w, h, fill=colors[failure_type]))
        total = sum(by_setting[setting].values())
        body.append(text(x + bar_w / 2, current_y - 7, str(total), size=10))
        body.append(text(x + bar_w / 2, bottom + 23, SETTING_LABELS[setting], size=10))

    legend_x = width - 240
    legend_y = 76
    labels = [
        ("empty_or_missing_patch", "empty/missing patch"),
        ("syntax_error", "syntax error"),
        ("wrong_output", "wrong output"),
    ]
    for i, (key, label) in enumerate(labels):
        y = legend_y + i * 20
        body.append(rect(legend_x, y - 10, 12, 12, fill=colors[key]))
        body.append(text(legend_x + 18, y, label, size=11, anchor="start"))

    path = FIG_DIR / "apps_failure_modes_shifted.svg"
    path.write_text(svg_document(width, height, body), encoding="utf-8")
    return path


def write_mechanism_figure() -> Path:
    width, height = 1120, 560
    body: list[str] = []

    def rounded_rect(x: float, y: float, w: float, h: float, *, fill: str, stroke: str, width_: float = 1.0, radius: float = 8.0) -> str:
        return (
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{radius:.1f}" ry="{radius:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width_}"/>'
        )

    def arrow_line(x1: float, y1: float, x2: float, y2: float, *, color: str = "#334155", width_: float = 1.4, dash: str | None = None) -> None:
        body.append(line(x1, y1, x2, y2, stroke=color, width=width_, dash=dash))
        angle = math.atan2(y2 - y1, x2 - x1)
        left_angle = angle + math.pi * 0.86
        right_angle = angle - math.pi * 0.86
        size = 9.5
        p1 = (x2 + size * math.cos(left_angle), y2 + size * math.sin(left_angle))
        p2 = (x2 + size * math.cos(right_angle), y2 + size * math.sin(right_angle))
        body.append(f'<polygon points="{x2:.1f},{y2:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>')

    def label_box(x: float, y: float, w: float, h: float, title: str, subtitle: str, *, fill: str = "#ffffff", stroke: str = "#cbd5e1", title_color: str = "#0f172a") -> None:
        body.append(rounded_rect(x, y, w, h, fill=fill, stroke=stroke, width_=1.1, radius=8))
        body.append(text(x + 18, y + 28, title, size=13, anchor="start", weight="700"))
        body.append(text(x + 18, y + 52, subtitle, size=10, anchor="start"))

    # Title.
    body.append(text(width / 2, 30, "ORCA: Extract, Type, and Selectively Reuse Coordination Assets", size=17, weight="700"))
    body.append(text(width / 2, 52, "The empirical question is not whether all memory helps, but which asset type transfers under distribution shift.", size=11))

    # Lane backgrounds.
    lanes = [
        (42, 88, 302, 390, "1  Training-time emergence", "#f8fafc"),
        (408, 88, 304, 390, "2  Typed asset store", "#f8fafc"),
        (776, 88, 302, 390, "3  Test-time selective reuse", "#f8fafc"),
    ]
    for x, y, w, h, title, fill in lanes:
        body.append(rounded_rect(x, y, w, h, fill=fill, stroke="#d6dee8", width_=1.0, radius=12))
        body.append(text(x + 18, y + 30, title, size=13, anchor="start", weight="700"))

    # Lane 1: emergence.
    label_box(72, 142, 242, 72, "Multi-agent training runs", "localize -> patch -> review")
    label_box(72, 250, 242, 78, "Trajectory logs", "agent choices, handoffs, outcomes")
    label_box(72, 364, 242, 72, "Successful patterns", "specialization and procedures")
    arrow_line(193, 214, 193, 250)
    arrow_line(193, 328, 193, 364)

    # Lane 2: typed store.
    label_box(438, 124, 244, 60, "Role assets", "who tends to handle which subtask", fill="#ffffff", stroke="#a7bdd4")
    label_box(438, 214, 244, 60, "Procedural prompt assets", "how to localize and hand off patches", fill="#eef6fd", stroke="#2f6f9f")
    label_box(438, 304, 244, 60, "Organization assets", "team-level workflow summaries", fill="#ffffff", stroke="#a7bdd4")
    body.append(rounded_rect(466, 404, 188, 42, fill="#fff7ed", stroke="#d99a3d", width_=1.0, radius=8))
    body.append(text(560, 430, "validated by ablation", size=12, weight="700"))

    # Lane 3: selective reuse.
    label_box(806, 124, 242, 60, "Prompt-only reuse", "inject procedural guidance", fill="#eef6fd", stroke="#2f6f9f")
    label_box(806, 214, 242, 60, "Routing-only reuse", "assign subtasks from role assets")
    label_box(806, 304, 242, 60, "Full reuse", "prompt + routing together", fill="#fffafa", stroke="#b35c44")
    body.append(rounded_rect(806, 404, 242, 42, fill="#f8fafc", stroke="#94a3b8", width_=1.0, radius=8))
    body.append(text(927, 430, "choose asset type empirically", size=12, weight="700"))

    # Cross-lane arrows.
    arrow_line(314, 401, 438, 154, color="#64748b")
    arrow_line(314, 401, 438, 244, color="#2f6f9f")
    arrow_line(314, 401, 438, 334, color="#64748b")
    arrow_line(682, 154, 806, 244, color="#64748b")
    arrow_line(682, 244, 806, 154, color="#2f6f9f")
    arrow_line(682, 334, 806, 334, color="#b35c44")
    arrow_line(560, 364, 560, 404, color="#d99a3d", dash="4 3")
    arrow_line(927, 364, 927, 404, color="#64748b", dash="4 3")

    # Evidence ribbon.
    body.append(rounded_rect(118, 500, 884, 38, fill="#eef2f7", stroke="#cbd5e1", width_=1.0, radius=10))
    body.append(text(560, 525, "Domain 1 evidence: prompt-level procedural assets transfer most clearly; full reuse can over-constrain the workflow.", size=12, weight="700"))

    path = FIG_DIR / "poa_mechanism_selective_reuse.svg"
    path.write_text(svg_document(width, height, body), encoding="utf-8")
    return path


def write_markdown_table(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] + ["---:" for _ in headers[1:]]) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def latex_escape(value: str) -> str:
    return value.replace("_", "\\_")


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
    lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\end{table}",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_paper_tables(summary_rows: list[dict[str, str]], failure_rows: list[dict[str, str]], contrast_rows: list[dict[str, str]]) -> list[Path]:
    paths: list[Path] = []
    summary_order = [
        ("shifted_test", "free"), ("shifted_test", "manual"), ("shifted_test", "random"),
        ("shifted_test", "reuse_prompt"), ("shifted_test", "reuse_routing"), ("shifted_test", "reuse_full"),
        ("test", "free"), ("test", "manual"), ("test", "random"),
        ("test", "reuse_prompt"), ("test", "reuse_routing"), ("test", "reuse_full"),
    ]
    by_key = {(row["split"], row["setting"]): row for row in summary_rows}
    main_rows = []
    for split, setting in summary_order:
        row = by_key[(split, setting)]
        setting_label = SETTING_LABELS[setting]
        if (split, setting) in {("shifted_test", "reuse_prompt"), ("test", "manual")}:
            setting_label = f"**{setting_label}**"
        main_rows.append([split, setting_label, fmt3(row["avg_success"]), fmt3(row["std_success"]), fmt3(row["min_success"]), fmt3(row["max_success"])])
    headers = ["Split", "Setting", "Mean", "Std.", "Min", "Max"]
    p = TABLE_DIR / "paper_apps_main_results.md"
    write_markdown_table(p, headers, main_rows)
    paths.append(p)
    p = TABLE_DIR / "paper_apps_main_results.tex"
    write_latex_table(p, "APPS code-repair success rate averaged over three seeds.", "tab:apps-main", headers, [[cell.replace("**", "") for cell in row] for row in main_rows])
    paths.append(p)

    counts = contrast_counts(contrast_rows)
    contrast_table_rows = []
    for split in ["shifted_test", "test"]:
        for setting in REUSE_SETTINGS:
            c = counts[(split, setting)]
            contrast_table_rows.append([
                split,
                SETTING_LABELS[setting],
                str(c["rescued_by_reuse"]),
                str(c["hurt_by_reuse"]),
                str(c["both_passed"]),
                str(c["both_failed"]),
                f"{c['rescued_by_reuse'] - c['hurt_by_reuse']:+d}",
            ])
    headers = ["Split", "Reuse", "Rescued", "Hurt", "Both pass", "Both fail", "Net"]
    p = TABLE_DIR / "paper_apps_reuse_contrast.md"
    write_markdown_table(p, headers, contrast_table_rows)
    paths.append(p)
    p = TABLE_DIR / "paper_apps_reuse_contrast.tex"
    write_latex_table(p, "Matched-task contrast between each reuse setting and free self-organization.", "tab:apps-contrast", headers, contrast_table_rows)
    paths.append(p)

    shifted_failures: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in failure_rows:
        if row["split"] == "shifted_test":
            shifted_failures[row["setting"]][row["failure_type"]] = int(row["count"])
    failure_table_rows = []
    for setting in SETTINGS:
        failures = shifted_failures[setting]
        failure_table_rows.append([
            SETTING_LABELS[setting],
            str(failures.get("empty_or_missing_patch", 0)),
            str(failures.get("syntax_error", 0)),
            str(failures.get("wrong_output", 0)),
            str(sum(failures.values())),
        ])
    headers = ["Setting", "Empty/missing", "Syntax", "Wrong output", "All failures"]
    p = TABLE_DIR / "paper_apps_failure_modes_shifted.md"
    write_markdown_table(p, headers, failure_table_rows)
    paths.append(p)
    p = TABLE_DIR / "paper_apps_failure_modes_shifted.tex"
    write_latex_table(p, "Failure modes on shifted APPS repair tasks.", "tab:apps-failures", headers, failure_table_rows)
    paths.append(p)

    case_rows = [
        ["Accordion parser", "0000 / 712", "Free: empty patch", "Prompt + routing pass", "Clean rescue: assets stabilize patch handoff"],
        ["Fence painting", "0003 / 712", "Free: empty patch", "Prompt + routing pass", "Structured repair plan from reusable guidance"],
        ["Sofa storehouse", "0009 / 712", "Free: empty patch", "Routing passes; prompt truncates", "Routing can help, but prompt-only is not sufficient"],
        ["Golden trophy", "0012 / 712", "Free + prompt pass", "Full + routing fail", "Full reuse can interfere with patch handoff"],
        ["Max digit sum", "0001 / 714", "Free + prompt pass", "Full fails with empty patch", "Second hurt case for over-constrained full reuse"],
    ]
    headers = ["Case", "Task/seed", "Free behavior", "Reuse behavior", "Interpretation"]
    p = TABLE_DIR / "paper_apps_case_notes.md"
    write_markdown_table(p, headers, case_rows)
    paths.append(p)
    p = TABLE_DIR / "paper_apps_case_notes.tex"
    write_latex_table(p, "Representative qualitative cases from APPS shifted-test runs.", "tab:apps-cases", headers, case_rows)
    paths.append(p)
    return paths


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows = read_csv(SUMMARY_CSV)
    failure_rows = read_csv(FAILURE_MODES_CSV)
    contrast_rows = read_csv(REUSE_VS_FREE_CSV)

    figure_paths = [
        write_mechanism_figure(),
        write_success_figure(summary_rows),
        write_reuse_contrast_figure(contrast_rows),
        write_failure_modes_figure(failure_rows),
    ]
    table_paths = write_paper_tables(summary_rows, failure_rows, contrast_rows)
    print("Generated figures:")
    for path in figure_paths:
        print(f"- {path.relative_to(ROOT)}")
    print("Generated tables:")
    for path in table_paths:
        print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
