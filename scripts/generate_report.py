import csv
import html
import math
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = REPO_ROOT / "docs" / "assets"
POSTGRES_CONTAINER = "adops-postgres"
DB_USER = "agentic"
DB_NAME = "warehouse"


def run_psql(sql: str) -> list[dict[str, str]]:
    cmd = [
        "docker",
        "exec",
        POSTGRES_CONTAINER,
        "psql",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
        "-P",
        "pager=off",
        "-A",
        "-F",
        ",",
        "-c",
        sql,
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    lines = [
        line
        for line in proc.stdout.splitlines()
        if line and not line.startswith("(") and not line.startswith("Timing")
    ]
    return list(csv.DictReader(lines))


def money(value: float) -> str:
    return f"${value:,.2f}"


def number(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def svg_text(x: float, y: float, text: str, size: int = 14, weight: str = "400", anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'fill="#172033">{html.escape(text)}</text>'
    )


def write_bar_chart(path: Path, title: str, labels: list[str], values: list[float], value_prefix: str = "") -> None:
    width, height = 820, 420
    left, right, top, bottom = 92, 36, 72, 88
    plot_w = width - left - right
    plot_h = height - top - bottom
    max_value = max(values) if values else 1
    max_value = max(max_value, 1)
    colors = ["#2f80ed", "#00a676", "#f2994a", "#9b51e0", "#eb5757"]
    bar_gap = 18
    bar_w = max(28, (plot_w - bar_gap * (len(values) - 1)) / max(len(values), 1))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(28, 36, title, 22, "700"),
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#cad2df" stroke-width="1"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#cad2df" stroke-width="1"/>',
    ]

    for i in range(5):
        y = top + plot_h - (plot_h * i / 4)
        tick = max_value * i / 4
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#edf1f7" stroke-width="1"/>')
        parts.append(svg_text(left - 12, y + 5, number(tick), 12, anchor="end"))

    for idx, (label, value) in enumerate(zip(labels, values)):
        x = left + idx * (bar_w + bar_gap)
        bar_h = plot_h * (value / max_value)
        y = top + plot_h - bar_h
        color = colors[idx % len(colors)]
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" fill="{color}"/>')
        parts.append(svg_text(x + bar_w / 2, y - 10, f"{value_prefix}{number(value)}", 12, "700", "middle"))
        parts.append(svg_text(x + bar_w / 2, top + plot_h + 28, label, 13, "600", "middle"))

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_line_chart(path: Path, title: str, labels: list[str], values: list[float]) -> None:
    width, height = 820, 420
    left, right, top, bottom = 92, 36, 72, 88
    plot_w = width - left - right
    plot_h = height - top - bottom
    max_value = max(values) if values else 1
    max_value = max(max_value, 1)
    step = plot_w / max(len(values) - 1, 1)
    points = []
    for idx, value in enumerate(values):
        x = left + idx * step
        y = top + plot_h - plot_h * (value / max_value)
        points.append((x, y))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(28, 36, title, 22, "700"),
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#cad2df" stroke-width="1"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#cad2df" stroke-width="1"/>',
    ]

    for i in range(5):
        y = top + plot_h - (plot_h * i / 4)
        tick = max_value * i / 4
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#edf1f7" stroke-width="1"/>')
        parts.append(svg_text(left - 12, y + 5, number(tick), 12, anchor="end"))

    if points:
        polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        parts.append(f'<polyline points="{polyline}" fill="none" stroke="#2f80ed" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        for idx, (x, y) in enumerate(points):
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#ffffff" stroke="#2f80ed" stroke-width="3"/>')
            parts.append(svg_text(x, top + plot_h + 28, labels[idx], 12, "600", "middle"))

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_status_card(path: Path, latest: dict[str, str], summary: dict[str, str]) -> None:
    width, height = 820, 260
    status = latest.get("status", "UNKNOWN")
    status_color = "#00a676" if status == "SUCCESS" else "#eb5757"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(28, 38, "Latest Pipeline Health", 22, "700"),
        f'<rect x="28" y="64" width="764" height="152" rx="8" fill="#f7f9fc" stroke="#d7dee9"/>',
        f'<circle cx="62" cy="106" r="12" fill="{status_color}"/>',
        svg_text(86, 113, f"Freshness agent status: {status}", 20, "700"),
        svg_text(86, 148, f"Latest run: {latest.get('started_at', 'n/a')}", 14),
        svg_text(86, 178, f"Events loaded: {number(float(summary.get('total_events', '0')))}", 14, "700"),
        svg_text(300, 178, f"Revenue: {money(float(summary.get('purchase_revenue', '0')))}", 14, "700"),
        svg_text(500, 178, f"Purchase events: {number(float(summary.get('purchase_events', '0')))}", 14, "700"),
        "</svg>",
    ]
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    summary = run_psql(
        """
        SELECT COUNT(*) AS total_events,
               COUNT(DISTINCT user_id) AS unique_users,
               COUNT(*) FILTER (WHERE event_type = 'purchase') AS purchase_events,
               COALESCE(SUM(price) FILTER (WHERE event_type = 'purchase'), 0) AS purchase_revenue,
               MIN(event_ts)::date AS first_event_date,
               MAX(event_ts)::date AS latest_event_date
        FROM raw.raw_events;
        """
    )[0]
    funnel = run_psql(
        """
        SELECT event_type,
               COUNT(*) AS event_count,
               COALESCE(SUM(price) FILTER (WHERE event_type = 'purchase'), 0) AS revenue
        FROM raw.raw_events
        GROUP BY event_type
        ORDER BY event_count DESC;
        """
    )
    device = run_psql(
        """
        SELECT device_type,
               SUM(event_count) AS event_count,
               SUM(revenue) AS revenue
        FROM mart.fct_events_daily
        GROUP BY device_type
        ORDER BY event_count DESC;
        """
    )
    daily = run_psql(
        """
        SELECT event_day::date AS event_day,
               SUM(event_count) AS event_count
        FROM mart.fct_events_daily
        GROUP BY 1
        ORDER BY 1;
        """
    )
    latest_run = run_psql(
        """
        SELECT run_id, pipeline_name, status, started_at, ended_at
        FROM ops.pipeline_runs
        ORDER BY started_at DESC
        LIMIT 1;
        """
    )[0]

    write_bar_chart(
        ASSET_DIR / "event-funnel.svg",
        "Event Funnel",
        [row["event_type"] for row in funnel],
        [float(row["event_count"]) for row in funnel],
    )
    write_bar_chart(
        ASSET_DIR / "revenue-by-device.svg",
        "Revenue by Device",
        [row["device_type"] for row in device],
        [float(row["revenue"]) for row in device],
        "$",
    )
    write_line_chart(
        ASSET_DIR / "daily-event-volume.svg",
        "Daily Event Volume",
        [row["event_day"] for row in daily],
        [float(row["event_count"]) for row in daily],
    )
    write_status_card(ASSET_DIR / "agent-status.svg", latest_run, summary)

    print(f"Wrote report assets to {ASSET_DIR}")


if __name__ == "__main__":
    main()
